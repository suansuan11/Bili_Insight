"""B站数据获取服务 - 基于bilibili-api统一封装"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from bilibili_api import video, hot, comment, Credential, sync
from bilibili_api.comment import CommentResourceType
from bilibili_api.exceptions.NetworkException import NetworkException
from curl_cffi.requests import AsyncSession
from app.utils.logger import logger
from app.config import settings
from .browser_comment_service import BrowserCommentService
from .crawler_exceptions import CommentFetchException, BilibiliRiskControlException


class BilibiliService:
    """B站API服务统一封装类"""

    def __init__(self, credential: Optional[Credential] = None):
        """
        初始化B站服务

        Args:
            credential: B站登录凭证（可选）
        """
        self.credential = credential

    @staticmethod
    def _extract_status_code(exc: Exception) -> Optional[int]:
        if isinstance(exc, NetworkException):
            code = getattr(exc, "code", None)
            if isinstance(code, int):
                return code

        text = str(exc)
        marker = "状态码："
        if marker in text:
            suffix = text.split(marker, 1)[1].strip()
            digits = "".join(ch for ch in suffix[:4] if ch.isdigit())
            if digits:
                try:
                    return int(digits)
                except ValueError:
                    return None
        return None

    def _is_risk_control_error(self, exc: Exception) -> bool:
        code = self._extract_status_code(exc)
        text = str(exc)
        return code == 412 or "security control policy" in text.lower() or "风控" in text

    @staticmethod
    def _is_retryable_network_error(exc: Exception) -> bool:
        text = str(exc).lower()
        transient_keywords = ["timeout", "tempor", "connection reset", "server disconnected"]
        return any(keyword in text for keyword in transient_keywords)

    async def _get_video_aid(self, bvid: str) -> int:
        v = video.Video(bvid=bvid, credential=self.credential)
        info = await v.get_info()
        aid = info["aid"]
        logger.debug(f"视频AID: {aid}")
        return aid

    def _build_comment_headers(self, bvid: str) -> Dict[str, str]:
        return {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": f"https://www.bilibili.com/video/{bvid}",
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
        }

    def _get_cookie_dict(self) -> Dict[str, str]:
        if not self.credential:
            return {}
        try:
            cookies = self.credential.get_cookies()
            normalized: Dict[str, str] = {}
            for key, value in cookies.items():
                if not value:
                    continue
                key_str = str(key)
                if key_str in {"sessdata", "dedeuserid"}:
                    continue
                normalized[key_str] = str(value)
            return normalized
        except Exception as exc:
            logger.warning(f"获取 Credential cookies 失败: {exc}")
            return {}

    @staticmethod
    def _normalize_reply(reply: Dict) -> Dict:
        member = reply.get("member") or {}
        content = reply.get("content") or {}
        return {
            "author": member.get("uname", "未知用户"),
            "gender": member.get("sex", "未知"),
            "content": content.get("message", ""),
            "like": int(reply.get("like", 0) or 0),
            "reply_id": reply.get("rpid"),
            "create_time": reply.get("ctime", 0)
        }

    async def _fetch_comments_via_browser_session(self, aid: int, bvid: str, max_count: int) -> List[Dict]:
        """
        浏览器态 fallback：
        使用 curl_cffi 模拟真实浏览器请求旧版分页评论接口，尽量绕开 wbi/main 的高敏风控。
        """
        logger.warning("切换到浏览器态 fallback 评论抓取")
        headers = self._build_comment_headers(bvid)
        cookies = self._get_cookie_dict()
        all_comments: List[Dict] = []

        async with AsyncSession(impersonate="chrome", headers=headers, cookies=cookies, timeout=20) as session:
            page_index = 1
            while len(all_comments) < max_count:
                response = await session.get(
                    "https://api.bilibili.com/x/v2/reply",
                    params={
                        "oid": aid,
                        "type": CommentResourceType.VIDEO.value,
                        "pn": page_index,
                        "sort": 0
                    }
                )

                if response.status_code == 412:
                    raise BilibiliRiskControlException(
                        "B站评论接口触发风控(412)，完整浏览器态 fallback 也被拦截，请稍后重试",
                        status_code=412
                    )
                response.raise_for_status()

                payload = response.json()
                if payload.get("code") not in (0, None):
                    raise CommentFetchException(
                        f"浏览器态评论抓取失败: code={payload.get('code')} message={payload.get('message')}"
                    )

                data = payload.get("data") or {}
                replies = data.get("replies") or []
                if not replies:
                    break

                for reply in replies:
                    normalized = self._normalize_reply(reply)
                    if normalized["content"]:
                        all_comments.append(normalized)
                    if len(all_comments) >= max_count:
                        break

                if len(replies) < 20:
                    break

                page_index += 1
                await asyncio.sleep(1.0)

        logger.info(f"浏览器态 fallback 评论抓取完成 - 共获取 {len(all_comments)} 条评论")
        return all_comments

    async def _fetch_comments_via_playwright(self, aid: int, bvid: str, max_count: int) -> List[Dict]:
        if not settings.browser_fallback_enabled or not BrowserCommentService.is_available():
            raise RuntimeError("Playwright fallback 不可用")

        logger.warning("切换到 Playwright 浏览器态评论抓取")
        service = BrowserCommentService(cookie_dict=self._get_cookie_dict())
        return await service.fetch_comments(bvid=bvid, aid=aid, max_count=max_count)

    async def _fetch_comment_page(self, aid: int, offset: str = "", retries: int = 3) -> Dict:
        last_exc: Optional[Exception] = None

        for attempt in range(1, retries + 1):
            try:
                return await comment.get_comments_lazy(
                    oid=aid,
                    type_=CommentResourceType.VIDEO,
                    offset=offset,
                    credential=self.credential
                )
            except Exception as exc:
                last_exc = exc
                if self._is_risk_control_error(exc):
                    if attempt < retries:
                        delay = 1.2 * attempt
                        logger.warning("评论接口触发风控(尝试 %s/%s)，%.1fs 后重试", attempt, retries, delay)
                        await asyncio.sleep(delay)
                        continue
                    raise BilibiliRiskControlException(
                        "B站评论接口触发风控(412)，请稍后重试或重新绑定更稳定的浏览器态凭证",
                        status_code=self._extract_status_code(exc)
                    ) from exc

                if attempt < retries and self._is_retryable_network_error(exc):
                    delay = 0.8 * attempt
                    logger.warning("评论接口临时错误(尝试 %s/%s)，%.1fs 后重试: %s", attempt, retries, delay, exc)
                    await asyncio.sleep(delay)
                    continue

                raise CommentFetchException(f"获取评论失败: {exc}") from exc

        if last_exc is not None:
            raise CommentFetchException(f"获取评论失败: {last_exc}") from last_exc
        raise CommentFetchException("获取评论失败: 未知错误")

    async def probe_comment_access(self, bvid: str) -> Dict:
        """
        轻量探测评论接口可用性。
        仅请求第一页评论，用于提交任务前预检。
        """
        logger.info(f"开始探测评论接口可用性 - BVID: {bvid}")
        aid: Optional[int] = None
        try:
            aid = await self._get_video_aid(bvid)
            result = await self._fetch_comment_page(aid=aid, offset="", retries=2)
            replies = result.get("replies") or []
            return {
                "available": True,
                "risk_controlled": False,
                "message": "评论接口可用",
                "sample_count": len(replies)
            }
        except BilibiliRiskControlException as exc:
            logger.warning(f"主评论接口触发风控，尝试 fallback 探测 - BVID: {bvid}: {exc}")
        except Exception as exc:
            logger.warning(f"评论接口探测失败 - BVID: {bvid}: {exc}")

        if aid is None:
            return {
                "available": False,
                "risk_controlled": False,
                "message": "评论接口探测失败: 无法获取视频 aid"
            }

        try:
            fallback_comments = await self._fetch_comments_via_playwright(aid, bvid, max_count=5)
            return {
                "available": len(fallback_comments) > 0,
                "risk_controlled": False,
                "message": "主评论接口不可用，但 Playwright 浏览器态 fallback 可用",
                "sample_count": len(fallback_comments),
                "fallback_mode": "playwright"
            }
        except Exception as playwright_exc:
            logger.warning(f"Playwright fallback 探测失败 - BVID: {bvid}: {playwright_exc}")

        try:
            fallback_comments = await self._fetch_comments_via_browser_session(aid, bvid, max_count=5)
            return {
                "available": len(fallback_comments) > 0,
                "risk_controlled": False,
                "message": "主评论接口不可用，但 curl_cffi 浏览器态 fallback 可用",
                "sample_count": len(fallback_comments),
                "fallback_mode": "browser_session"
            }
        except BilibiliRiskControlException as fallback_exc:
            return {
                "available": False,
                "risk_controlled": True,
                "message": str(fallback_exc)
            }
        except Exception as fallback_exc:
            return {
                "available": False,
                "risk_controlled": False,
                "message": f"评论接口探测失败: {fallback_exc}"
            }

    async def get_video_info(self, bvid: str) -> Optional[Dict]:
        """
        获取视频信息

        Args:
            bvid: 视频BVID

        Returns:
            视频信息字典
        """
        logger.info(f"开始获取视频信息 - BVID: {bvid}")
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            logger.debug(f"B站API返回视频信息 - 标题: {info.get('title', 'N/A')}")

            # 格式化为统一结构
            result = {
                'bvid': info['bvid'],
                'aid': info['aid'],
                'title': info['title'],
                'author': info['owner']['name'],
                'author_mid': info['owner']['mid'],
                'publish_date': datetime.fromtimestamp(info['pubdate']).strftime('%Y-%m-%d %H:%M:%S'),
                'duration': info['duration'],
                'view_count': info['stat']['view'],
                'like_count': info['stat']['like'],
                'coin_count': info['stat']['coin'],
                'favorite_count': info['stat']['favorite'],
                'share_count': info['stat']['share'],
                'danmaku_count': info['stat']['danmaku'],
                'description': info['desc'],
                'cover_url': info['pic']
            }
            logger.info(f"视频信息获取成功 - {bvid} - {result['title']}")
            return result
        except Exception as e:
            logger.error(f"获取视频 {bvid} 信息失败: {e}", exc_info=True)
            return None

    async def get_hot_videos(self, page: int = 1, page_size: int = 20) -> List[Dict]:
        """
        获取热门视频列表

        Args:
            page: 页码（从1开始）
            page_size: 每页数量

        Returns:
            热门视频列表
        """
        logger.info(f"开始获取热门视频 - 页码: {page}, 每页数量: {page_size}")
        try:
            # 使用bilibili-api的热门视频接口
            result = await hot.get_hot_videos(pn=page, ps=page_size)

            videos = []
            for item in result.get('list', []):
                # 提取基本信息
                video_info = {
                    'bvid': item['bvid'],
                    'aid': item['aid'],
                    'title': item['title'],
                    'author': item['owner']['name'],
                    'author_mid': item['owner']['mid'],
                    'publish_date': datetime.fromtimestamp(item['pubdate']).strftime('%Y-%m-%d %H:%M:%S'),
                    'duration': item['duration'],
                    'view_count': item['stat']['view'],
                    'like_count': item['stat'].get('like', 0),
                    'coin_count': item['stat'].get('coin', 0),
                    'favorite_count': item['stat'].get('favorite', 0),
                    'share_count': item['stat'].get('share', 0),
                    'danmaku_count': item['stat'].get('danmaku', 0),
                    'comment_count': item['stat'].get('reply', 0),  # 获取评论数
                    'description': item.get('desc', ''),
                    'cover_url': item.get('pic', '')
                }
                videos.append(video_info)

            logger.info(f"热门视频获取成功 - 共{len(videos)}个视频")
            return videos
        except Exception as e:
            logger.error(f"获取热门视频失败: {e}", exc_info=True)
            return []

    async def get_comments(self, bvid: str, max_count: int = 200) -> List[Dict]:
        """
        获取视频评论

        Args:
            bvid: 视频BVID
            max_count: 最大获取数量

        Returns:
            评论列表
        """
        logger.info(f"开始获取评论 - BVID: {bvid}, 最大数量: {max_count}")
        aid = await self._get_video_aid(bvid)

        try:
            all_comments = []
            page = 1
            offset = ""

            while len(all_comments) < max_count:
                logger.debug(f"获取评论第{page}页 - 当前已获取: {len(all_comments)}条")
                result = await self._fetch_comment_page(aid=aid, offset=offset, retries=3)

                replies = result.get('replies')
                if not replies:
                    logger.debug(f"第{page}页无更多评论，停止获取")
                    break

                for reply in replies:
                    normalized = self._normalize_reply(reply)
                    if normalized["content"]:
                        all_comments.append(normalized)

                    if len(all_comments) >= max_count:
                        break

                next_offset = result.get('cursor', {}).get('pagination_reply', {}).get('next_offset')
                if not next_offset:
                    logger.debug("已到最后一页，停止获取")
                    break

                offset = next_offset
                page += 1
                await asyncio.sleep(0.8)

            logger.info(f"评论获取完成 - 共获取 {len(all_comments)} 条评论")
            return all_comments
        except BilibiliRiskControlException:
            if not self.credential:
                raise
            logger.warning("新版评论接口被风控，尝试 Playwright 浏览器态 fallback")
            try:
                return await self._fetch_comments_via_playwright(aid, bvid, max_count)
            except Exception as playwright_exc:
                logger.warning("Playwright fallback 失败，继续尝试 curl_cffi: %s", playwright_exc)
                return await self._fetch_comments_via_browser_session(aid, bvid, max_count)

    async def get_danmakus(self, bvid: str) -> List[Dict]:
        """
        获取视频弹幕

        Args:
            bvid: 视频BVID

        Returns:
            弹幕列表
        """
        logger.info(f"开始获取弹幕 - BVID: {bvid}")
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            cid = info['cid']
            logger.debug(f"视频CID: {cid}")

            # 获取弹幕
            logger.debug(f"调用B站API获取弹幕数据")
            danmakus_list = await v.get_danmakus(cid=cid)

            # 格式化弹幕数据
            danmaku_data = []
            for dm in danmakus_list:
                if dm.text:
                    danmaku_data.append({
                        'content': dm.text,
                        'dm_time': float(dm.dm_time) # Ensure float seconds
                    })

            logger.info(f"弹幕获取完成 - 共获取 {len(danmaku_data)} 条弹幕")
            return danmaku_data

        except Exception as e:
            logger.error(f"获取弹幕失败 - BVID: {bvid}: {e}", exc_info=True)
            return []

    # 同步包装方法
    def get_video_info_sync(self, bvid: str) -> Optional[Dict]:
        """同步获取视频信息"""
        return sync(self.get_video_info(bvid))

    def get_hot_videos_sync(self, page: int = 1, page_size: int = 20) -> List[Dict]:
        """同步获取热门视频"""
        return sync(self.get_hot_videos(page, page_size))

    def get_comments_sync(self, bvid: str, max_count: int = 200) -> List[Dict]:
        """同步获取评论"""
        return sync(self.get_comments(bvid, max_count))

    def get_danmakus_sync(self, bvid: str) -> List[Dict]:
        """同步获取弹幕"""
        return sync(self.get_danmakus(bvid))
