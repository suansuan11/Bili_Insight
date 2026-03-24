"""爬虫服务整合模块"""
from typing import List, Dict, Optional
from .bilibili_service import BilibiliService
from .credential_manager import make_credential


class ScraperService:
    """爬虫服务封装类 - 统一使用bilibili-api"""

    def __init__(self, sessdata: Optional[str] = None):
        """
        Args:
            sessdata: B站登录凭证（由 Java 后端传入，无则游客模式）
        """
        self.bili_service = BilibiliService(credential=make_credential(sessdata))

    def get_video_info(self, bvid: str) -> Optional[Dict]:
        try:
            return self.bili_service.get_video_info_sync(bvid)
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    def get_comments(self, bvid: str, max_pages: int = 10) -> List[Dict]:
        try:
            return self.bili_service.get_comments_sync(bvid, max_pages * 20)
        except Exception as e:
            print(f"获取评论失败: {e}")
            return []

    def get_danmakus_sync(self, bvid: str, sessdata: Optional[str] = None) -> List[Dict]:
        try:
            if sessdata:
                return BilibiliService(credential=make_credential(sessdata)).get_danmakus_sync(bvid)
            return self.bili_service.get_danmakus_sync(bvid)
        except Exception as e:
            print(f"获取弹幕失败: {e}")
            return []

    async def get_video_info_async(self, bvid: str) -> Optional[Dict]:
        try:
            return await self.bili_service.get_video_info(bvid)
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    async def get_comments_async(self, bvid: str, max_pages: int = 10) -> List[Dict]:
        try:
            return await self.bili_service.get_comments(bvid, max_pages * 20)
        except Exception as e:
            print(f"获取评论失败: {e}")
            return []

    async def get_danmakus_async(self, bvid: str, sessdata: Optional[str] = None) -> List[Dict]:
        try:
            if sessdata:
                return await BilibiliService(credential=make_credential(sessdata)).get_danmakus(bvid)
            return await self.bili_service.get_danmakus(bvid)
        except Exception as e:
            print(f"获取弹幕失败: {e}")
            return []
