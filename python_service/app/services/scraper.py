"""爬虫服务整合模块 - 优化重构版"""
from typing import List, Dict, Optional
from .bilibili_service import BilibiliService
from .credential_manager import get_credential_manager


class ScraperService:
    """爬虫服务封装类 - 统一使用bilibili-api"""

    def __init__(self, sessdata: Optional[str] = None):
        """
        初始化爬虫服务

        Args:
            sessdata: B站登录凭证（可选，Java后端传递时使用）
        """
        # 使用凭证管理器获取凭证
        # 如果Java传递了sessdata，使用它；否则使用默认凭证
        cred_manager = get_credential_manager()
        credential = cred_manager.get_credential(sessdata)

        # 初始化B站服务
        self.bili_service = BilibiliService(credential=credential)

    def get_video_info(self, bvid: str) -> Optional[Dict]:
        """
        获取视频信息（同步）

        Args:
            bvid: 视频BVID

        Returns:
            视频信息字典或None
        """
        try:
            return self.bili_service.get_video_info_sync(bvid)
        except Exception as e:
            print(f"获取视频信息失败: {e}")
            return None

    def get_comments(self, bvid: str, max_pages: int = 10) -> List[Dict]:
        """
        获取视频评论（同步）

        Args:
            bvid: 视频BVID
            max_pages: 最大爬取页数（每页约20条）

        Returns:
            评论列表
        """
        try:
            # 每页约20条，max_pages转换为max_count
            max_count = max_pages * 20
            return self.bili_service.get_comments_sync(bvid, max_count)
        except Exception as e:
            print(f"获取评论失败: {e}")
            return []

    def get_danmakus_sync(self, bvid: str, sessdata: Optional[str] = None) -> List[Dict]:
        """
        获取视频弹幕（同步）

        Args:
            bvid: 视频BVID
            sessdata: B站登录凭证（可选，如果需要临时使用不同凭证）

        Returns:
            弹幕列表
        """
        try:
            # 如果传入了新的sessdata，创建临时服务
            if sessdata:
                cred_manager = get_credential_manager()
                temp_credential = cred_manager.get_credential(sessdata)
                temp_service = BilibiliService(credential=temp_credential)
                return temp_service.get_danmakus_sync(bvid)

            # 使用默认凭证
            return self.bili_service.get_danmakus_sync(bvid)
        except Exception as e:
            print(f"获取弹幕失败: {e}")
            return []
