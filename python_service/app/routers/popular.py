"""热门视频API路由 - 优化重构版"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..database.repository import DatabaseRepository
from ..services.bilibili_service import BilibiliService
from ..services.credential_manager import make_credential
from ..utils.logger import logger
from typing import Dict
import asyncio

router = APIRouter()
db_repo = DatabaseRepository()

TARGET_POPULAR_VIDEO_COUNT = 100
MIN_FETCH_PAGES = 5
MAX_FETCH_PAGES = 12

class FetchRequest(BaseModel):
    pages: int = 1
    sessdata: Optional[str] = None

# 全局变量跟踪任务状态
_fetch_task_running = False
_last_fetch_result = {"status": "never_run", "count": 0}


async def fetch_popular_videos_task_async(pages: int = 1, sessdata: str = None):
    """
    后台任务：爬取热门视频并存入数据库（异步版本）
    仅当抓取到至少 100 个唯一热门视频时，才会清空旧数据并整表重建。

    Args:
        pages: 初始爬取页数（每页约20个，至少5页；若唯一视频不足100会自动补页）
        sessdata: 用户B站凭证
    """
    global _fetch_task_running, _last_fetch_result

    try:
        _fetch_task_running = True
        # 至少从5页开始抓取，后续如果唯一视频不足100会继续补页。
        requested_pages = max(pages, MIN_FETCH_PAGES)
        logger.info(
            f"开始爬取热门视频，目标唯一视频数={TARGET_POPULAR_VIDEO_COUNT}，初始页数={requested_pages}"
        )

        credential = None
        if sessdata:
            credential = make_credential(sessdata)

        bili_service = BilibiliService(credential=credential)
        ordered_unique_videos: Dict[str, Dict] = {}
        current_page = 1

        while current_page <= requested_pages and len(ordered_unique_videos) < TARGET_POPULAR_VIDEO_COUNT:
            batch_end = min(requested_pages, current_page + 4)
            logger.info(f"抓取热门视频页范围: {current_page}-{batch_end}")

            tasks = [
                bili_service.get_hot_videos(page=page_no, page_size=20)
                for page_no in range(current_page, batch_end + 1)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for page_no, result in zip(range(current_page, batch_end + 1), results):
                if isinstance(result, Exception):
                    logger.error(f"获取第{page_no}页热门视频失败: {result}")
                    continue

                for video in result:
                    bvid = video.get("bvid")
                    if not bvid or bvid in ordered_unique_videos:
                        continue
                    ordered_unique_videos[bvid] = video

            current_page = batch_end + 1
            if len(ordered_unique_videos) < TARGET_POPULAR_VIDEO_COUNT and requested_pages < MAX_FETCH_PAGES:
                requested_pages = min(MAX_FETCH_PAGES, requested_pages + 1)

        unique_videos = list(ordered_unique_videos.values())
        logger.info(
            f"热门视频抓取结束，唯一视频数={len(unique_videos)}，目标数={TARGET_POPULAR_VIDEO_COUNT}"
        )

        if len(unique_videos) < TARGET_POPULAR_VIDEO_COUNT:
            raise RuntimeError(
                f"热门视频抓取数量不足：仅获取到 {len(unique_videos)} 个唯一视频，无法保证表中存在 100 条数据"
            )

        videos_to_save = unique_videos[:TARGET_POPULAR_VIDEO_COUNT]
        inserted_count = db_repo.replace_popular_videos(videos_to_save)

        if inserted_count != TARGET_POPULAR_VIDEO_COUNT:
            raise RuntimeError(
                f"热门视频落库数量异常：期望 {TARGET_POPULAR_VIDEO_COUNT} 条，实际写入 {inserted_count} 条"
            )

        _last_fetch_result = {
            "status": "success",
            "count": inserted_count,
            "target": TARGET_POPULAR_VIDEO_COUNT,
            "fetched_unique": len(unique_videos),
            "pages_used": current_page - 1
        }
        logger.info(f"热门视频爬取完成，已清空并重建 {inserted_count} 条热门视频数据")

    except Exception as e:
        _last_fetch_result = {
            "status": "failed",
            "error": str(e),
            "count": 0
        }
        logger.error(f"爬取热门视频失败: {e}", exc_info=True)
    finally:
        _fetch_task_running = False


# 移除同步包装函数，不再需要


@router.post("/fetch")
async def trigger_fetch_popular_videos(
    background_tasks: BackgroundTasks,
    request: FetchRequest
):
    """
    触发热门视频爬取任务（后台执行）

    Args:
        request: 包含pages和sessdata的请求体

    Returns:
        任务提交响应
    """
    global _fetch_task_running

    if _fetch_task_running:
        raise HTTPException(
            status_code=409,
            detail="热门视频爬取任务正在执行中，请稍后再试"
        )

    # 直接添加异步任务，不使用同步包装
    background_tasks.add_task(fetch_popular_videos_task_async, request.pages, request.sessdata)

    return {
        "status": "success",
        "message": f"热门视频爬取任务已启动（{request.pages}页）",
        "note": "任务将在后台执行，使用bilibili-api异步并发获取"
    }


@router.get("/fetch/status")
async def get_fetch_status():
    """
    查询热门视频爬取任务状态

    Returns:
        任务状态信息
    """
    return {
        "running": _fetch_task_running,
        "last_result": _last_fetch_result
    }


@router.get("/list")
async def list_popular_videos(limit: int = 20):
    """
    获取热门视频列表

    Args:
        limit: 返回视频数量（默认20）

    Returns:
        热门视频列表
    """
    try:
        videos = db_repo.get_popular_videos(limit)
        return {
            "status": "success",
            "count": len(videos),
            "data": videos
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"查询热门视频失败: {str(e)}"
        )
