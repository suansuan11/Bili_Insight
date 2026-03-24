"""B站数据获取服务 - 基于bilibili-api统一封装"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from bilibili_api import video, hot, comment, Credential, sync
from bilibili_api.comment import CommentResourceType
from app.utils.logger import logger


class BilibiliService:
    """B站API服务统一封装类"""

    def __init__(self, credential: Optional[Credential] = None):
        """
        初始化B站服务

        Args:
            credential: B站登录凭证（可选）
        """
        self.credential = credential

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
        try:
            # 先获取视频aid
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info['aid']
            logger.debug(f"视频AID: {aid}")

            all_comments = []
            page = 1
            offset = ""

            while len(all_comments) < max_count:
                logger.debug(f"获取评论第{page}页 - 当前已获取: {len(all_comments)}条")
                # 使用新接口get_comments_lazy（传递凭证）
                result = await comment.get_comments_lazy(
                    oid=aid,
                    type_=CommentResourceType.VIDEO,
                    offset=offset,
                    credential=self.credential  # 关键：传递凭证
                )

                replies = result.get('replies')
                if not replies:
                    logger.debug(f"第{page}页无更多评论，停止获取")
                    break

                # 解析评论
                for reply in replies:
                    comment_data = {
                        'author': reply['member']['uname'],
                        'gender': reply['member']['sex'],
                        'content': reply['content']['message'],
                        'like': int(reply.get('like', 0)),  # Ensure int
                        'reply_id': reply.get('rpid'),
                        'create_time': reply.get('ctime', 0)
                    }
                    all_comments.append(comment_data)

                    if len(all_comments) >= max_count:
                        break

                # 获取下一页offset
                next_offset = result.get('cursor', {}).get('pagination_reply', {}).get('next_offset')
                if not next_offset:
                    logger.debug(f"已到最后一页，停止获取")
                    break

                offset = next_offset
                page += 1

                # 避免请求过快
                await asyncio.sleep(0.3)

            logger.info(f"评论获取完成 - 共获取 {len(all_comments)} 条评论")
            return all_comments

        except Exception as e:
            logger.error(f"获取评论失败 - BVID: {bvid}: {e}", exc_info=True)
            return []

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
