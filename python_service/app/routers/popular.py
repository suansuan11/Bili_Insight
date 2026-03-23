"""热门视频API路由 - 优化重构版"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..database.repository import DatabaseRepository
from ..services.bilibili_service import BilibiliService
from typing import Dict
import asyncio

router = APIRouter()
db_repo = DatabaseRepository()

# 全局变量跟踪任务状态
_fetch_task_running = False
_last_fetch_result = {"status": "never_run", "count": 0}


async def fetch_popular_videos_task_async(pages: int = 1):
    """
    后台任务：爬取热门视频并存入数据库（异步版本）

    Args:
        pages: 爬取页数
    """
    global _fetch_task_running, _last_fetch_result

    try:
        _fetch_task_running = True
        print(f"开始爬取热门视频（{pages}页）...")

        bili_service = BilibiliService()
        total_videos = []

        # 并发获取多页数据
        tasks = [bili_service.get_hot_videos(page=p, page_size=20) for p in range(1, pages + 1)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 汇总结果
        for result in results:
            if isinstance(result, list):
                total_videos.extend(result)
            elif isinstance(result, Exception):
                print(f"获取某页数据失败: {result}")

        print(f"收集到 {len(total_videos)} 个热门视频")

        # 保存到数据库
        success_count = 0
        first_error = None
        for video in total_videos:
            try:
                db_repo.insert_or_update_popular_video(video)
                success_count += 1
            except Exception as e:
                if not first_error:
                    first_error = str(e)
                print(f"保存视频 {video.get('bvid')} 失败: {e}")

        _last_fetch_result = {
            "status": "success" if success_count == len(total_videos) else "partial_success",
            "count": success_count,
            "total": len(total_videos),
            "first_error": first_error
        }
        print(f"热门视频爬取完成，成功保存 {success_count}/{len(total_videos)} 个视频")

    except Exception as e:
        _last_fetch_result = {
            "status": "failed",
            "error": str(e),
            "count": 0
        }
        print(f"爬取热门视频失败: {e}")
    finally:
        _fetch_task_running = False


# 移除同步包装函数，不再需要


@router.post("/fetch")
async def trigger_fetch_popular_videos(
    background_tasks: BackgroundTasks,
    pages: int = 1
):
    """
    触发热门视频爬取任务（后台执行）

    Args:
        pages: 爬取页数（默认1页）

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
    background_tasks.add_task(fetch_popular_videos_task_async, pages)

    return {
        "status": "success",
        "message": f"热门视频爬取任务已启动（{pages}页）",
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
