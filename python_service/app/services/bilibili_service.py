"""B站数据获取服务 - 基于bilibili-api统一封装"""
import asyncio
from typing import List, Dict, Optional
from datetime import datetime

from bilibili_api import video, hot, comment, Credential, sync
from bilibili_api.comment import CommentResourceType


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
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()

            # 格式化为统一结构
            return {
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
        except Exception as e:
            print(f"获取视频 {bvid} 信息失败: {e}")
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
                    'description': item.get('desc', ''),
                    'cover_url': item.get('pic', '')
                }
                videos.append(video_info)

            return videos
        except Exception as e:
            print(f"获取热门视频失败: {e}")
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
        try:
            # 先获取视频aid
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            aid = info['aid']

            all_comments = []
            page = 1
            offset = ""

            while len(all_comments) < max_count:
                # 使用新接口get_comments_lazy（传递凭证）
                result = await comment.get_comments_lazy(
                    oid=aid,
                    type_=CommentResourceType.VIDEO,
                    offset=offset,
                    credential=self.credential  # 关键：传递凭证
                )

                replies = result.get('replies')
                if not replies:
                    break

                # 解析评论
                for reply in replies:
                    comment_data = {
                        'author': reply['member']['uname'],
                        'gender': reply['member']['sex'],
                        'content': reply['content']['message'],
                        'like': reply.get('like', 0),
                        'reply_id': reply.get('rpid'),
                        'create_time': reply.get('ctime', 0)
                    }
                    all_comments.append(comment_data)

                    if len(all_comments) >= max_count:
                        break

                # 获取下一页offset
                next_offset = result.get('cursor', {}).get('pagination_reply', {}).get('next_offset')
                if not next_offset:
                    break

                offset = next_offset
                page += 1

                # 避免请求过快
                await asyncio.sleep(0.3)

            print(f"共获取 {len(all_comments)} 条评论")
            return all_comments

        except Exception as e:
            print(f"获取评论失败: {e}")
            return []

    async def get_danmakus(self, bvid: str) -> List[Dict]:
        """
        获取视频弹幕

        Args:
            bvid: 视频BVID

        Returns:
            弹幕列表
        """
        try:
            v = video.Video(bvid=bvid, credential=self.credential)
            info = await v.get_info()
            cid = info['cid']

            # 获取弹幕
            danmakus_list = await v.get_danmakus(cid=cid)

            # 格式化弹幕数据
            danmaku_data = []
            for dm in danmakus_list:
                if dm.text:
                    danmaku_data.append({
                        'content': dm.text,
                        'dm_time': dm.dm_time
                    })

            print(f"共获取 {len(danmaku_data)} 条弹幕")
            return danmaku_data

        except Exception as e:
            print(f"获取弹幕失败: {e}")
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
