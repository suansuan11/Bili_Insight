"""
视频分析API路由
提供视频完整分析接口（视频信息 + 评论 + 弹幕 + 情感分析）
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional

from app.services.bilibili_service import BilibiliService
from app.services.credential_manager import make_credential
from app.services.video_storage_service import VideoStorageService
from app.utils.logger import logger


router = APIRouter()


# ====== 请求/响应模型 ======

class AnalyzeVideoRequest(BaseModel):
    """视频分析请求"""
    bvid: str
    max_comments: int = 500
    sessdata: Optional[str] = None
    bili_jct: Optional[str] = None
    buvid3: Optional[str] = None
    cookie_json: Optional[str] = None
    task_id: Optional[str] = None  # Java 侧传来的 task_id；存在时直接使用，不再自行创建


class TaskResponse(BaseModel):
    """任务响应"""
    task_id: str
    message: str


class TaskStatusResponse(BaseModel):
    """任务状态响应"""
    task_id: str
    status: str
    progress: int
    current_step: Optional[str] = None
    error_message: Optional[str] = None


class TaskResultResponse(BaseModel):
    """任务结果响应"""
    task_id: str
    status: str
    bvid: str
    comment_count: int
    danmaku_count: int
    timeline_points: int
    aspects: dict


class CommentProbeResponse(BaseModel):
    available: bool
    risk_controlled: bool
    message: str
    sample_count: int = 0


# ====== 后台任务函数 ======

async def analyze_video_background(
    task_id: str,
    bvid: str,
    max_comments: int,
    credential
):
    """后台执行视频分析任务"""
    logger.info(f"[{task_id}] 开始执行视频分析任务 - BVID: {bvid}, 最大评论数: {max_comments}")
    bili_service = BilibiliService(credential=credential)
    storage_service = VideoStorageService()

    try:
        # 1. 获取视频信息
        logger.info(f"[{task_id}] 步骤1: 获取视频信息")
        await storage_service.update_task_progress(task_id, 10, "正在获取视频信息")
        video_info = await bili_service.get_video_info(bvid)
        if not video_info:
            raise Exception("获取视频信息失败")
        await storage_service.update_task_video_info(task_id, video_info.get('title'))
        logger.info(f"[{task_id}] 视频信息获取成功 - 标题: {video_info.get('title', 'N/A')}")

        # 2. 获取评论
        logger.info(f"[{task_id}] 步骤2: 获取评论 (最多{max_comments}条)")
        await storage_service.update_task_progress(task_id, 30, "正在获取评论")
        comments = await bili_service.get_comments(bvid, max_count=max_comments)
        logger.info(f"[{task_id}] 评论获取完成 - 共{len(comments)}条")
        comment_fetch_meta = dict(getattr(bili_service, "last_comment_fetch_meta", {}) or {})
        await storage_service.update_task_comment_fetch_meta(task_id, comment_fetch_meta)

        saved_comments = await storage_service.save_comments(task_id, bvid, comments)
        logger.info(f"[{task_id}] 评论保存完成 - 成功保存{saved_comments}条")

        # 3. 获取弹幕
        logger.info(f"[{task_id}] 步骤3: 获取弹幕")
        await storage_service.update_task_progress(task_id, 60, "正在获取弹幕")
        danmakus = await bili_service.get_danmakus(bvid)
        logger.info(f"[{task_id}] 弹幕获取完成 - 共{len(danmakus)}条")
        
        saved_danmakus = await storage_service.save_danmakus(task_id, bvid, danmakus)
        logger.info(f"[{task_id}] 弹幕保存完成 - 成功保存{saved_danmakus}条")

        # 4. 生成情绪时间轴
        logger.info(f"[{task_id}] 步骤4: 生成情绪时间轴和切面分析")
        await storage_service.update_task_progress(task_id, 90, "正在生成情绪时间轴")
        timeline_result = await storage_service.generate_sentiment_timeline(task_id, bvid, comment_fetch_meta=comment_fetch_meta)
        logger.info(f"[{task_id}] 情绪时间轴生成完成 - 时间点: {len(timeline_result.get('timeline', []))}, 切面: {len(timeline_result.get('aspects', {}))}")

        # 5. 完成
        await storage_service.complete_task(task_id)
        logger.info(f"[{task_id}] 视频分析任务完成")

    except Exception as e:
        logger.error(f"[{task_id}] 任务执行失败: {e}", exc_info=True)
        await storage_service.fail_task(task_id, str(e))


# ====== API端点 ======

@router.post("/video", response_model=TaskResponse)
async def analyze_video(request: AnalyzeVideoRequest, background_tasks: BackgroundTasks):
    """
    启动视频完整分析任务（异步）

    功能:
    1. 获取视频信息
    2. 获取所有评论并进行情感分析
    3. 获取所有弹幕并进行情感分析
    4. 生成情绪时间轴（按时间聚合）
    5. 生成切面情感分析（如外观、性能等维度）

    返回: 任务ID，前端通过轮询 /status/{task_id} 获取进度
    """
    logger.info(f"收到视频分析请求 - BVID: {request.bvid}, 最大评论数: {request.max_comments}")
    try:
        # 获取凭证（由 Java 后端从 DB 读取后传入，无则游客模式）
        credential = make_credential(request.sessdata, request.bili_jct, request.buvid3, request.cookie_json)
        logger.debug(f"凭证创建完成 - 使用{'用户凭证' if request.sessdata else '游客模式'}")

        # 若 Java 侧已创建任务记录并传来 task_id，直接使用；否则自行创建
        storage_service = VideoStorageService()
        if request.task_id:
            task_id = request.task_id
            logger.info(f"使用Java传入的任务ID: {task_id}")
            await storage_service.update_task_progress(task_id, 0, "任务已接收，准备开始")
        else:
            task_id = await storage_service.create_task(request.bvid, task_type="FULL_ANALYSIS")
            logger.info(f"创建新任务 - 任务ID: {task_id}")

        # 添加后台任务
        background_tasks.add_task(
            analyze_video_background,
            task_id,
            request.bvid,
            request.max_comments,
            credential
        )
        logger.info(f"后台任务已添加 - 任务ID: {task_id}")

        return TaskResponse(
            task_id=task_id,
            message=f"分析任务已提交，任务ID: {task_id}"
        )

    except Exception as e:
        logger.error(f"创建分析任务失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.post("/probe-comment", response_model=CommentProbeResponse)
async def probe_comment_access(request: AnalyzeVideoRequest):
    """
    轻量探测评论接口是否可用。
    用于 Java 提交任务前判断当前账号是否已触发 B站评论风控。
    """
    try:
        credential = make_credential(request.sessdata, request.bili_jct, request.buvid3, request.cookie_json)
        bili_service = BilibiliService(credential=credential)
        result = await bili_service.probe_comment_access(request.bvid)
        return CommentProbeResponse(
            available=bool(result.get("available")),
            risk_controlled=bool(result.get("risk_controlled")),
            message=str(result.get("message") or ""),
            sample_count=int(result.get("sample_count") or 0)
        )
    except Exception as e:
        logger.error(f"评论接口探测失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"评论接口探测失败: {str(e)}")


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查询任务状态（用于前端轮询）"""
    try:
        storage_service = VideoStorageService()
        task_info = await storage_service.get_task_info(task_id)

        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        return TaskStatusResponse(
            task_id=task_id,
            status=task_info['status'],
            progress=task_info['progress'],
            current_step=task_info.get('current_step'),
            error_message=task_info.get('error_message')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败: {str(e)}")


@router.get("/result/{task_id}", response_model=TaskResultResponse)
async def get_task_result(task_id: str):
    """获取任务完整结果"""
    try:
        storage_service = VideoStorageService()

        # 查询任务信息
        task_info = await storage_service.get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        if task_info['status'] != 'COMPLETED':
            raise HTTPException(status_code=400, detail=f"任务未完成，当前状态: {task_info['status']}")

        # 查询统计信息
        comment_stats = await storage_service.get_comment_stats(task_id)
        danmaku_stats = await storage_service.get_danmaku_stats(task_id)

        # 查询情绪时间轴
        with storage_service.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM sentiment_timeline WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                timeline_data = cursor.fetchone()

                import json
                timeline = json.loads(timeline_data['timeline_json']) if timeline_data else []
                aspects = json.loads(timeline_data['aspect_sentiment_json']) if timeline_data else {}

        return TaskResultResponse(
            task_id=task_id,
            status=task_info['status'],
            bvid=task_info['bvid'],
            comment_count=comment_stats['total'],
            danmaku_count=danmaku_stats['total'],
            timeline_points=len(timeline),
            aspects=aspects
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")


@router.get("/timeline/{task_id}")
async def get_sentiment_timeline(task_id: str):
    """获取情绪时间轴数据（用于ECharts渲染）"""
    try:
        storage_service = VideoStorageService()

        # 查询任务是否存在
        task_info = await storage_service.get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 查询时间轴数据
        with storage_service.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT timeline_json FROM sentiment_timeline WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()

                if not result:
                    return {"timeline": []}

                import json
                timeline = json.loads(result['timeline_json'])
                return {"timeline": timeline}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取时间轴失败: {str(e)}")


@router.get("/aspects/{task_id}")
async def get_aspect_sentiments(task_id: str):
    """获取切面情感分析数据（用于雷达图等）"""
    try:
        storage_service = VideoStorageService()

        # 查询任务是否存在
        task_info = await storage_service.get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="任务不存在")

        # 查询切面数据
        with storage_service.get_connection() as conn:
            with conn.cursor() as cursor:
                sql = "SELECT aspect_sentiment_json FROM sentiment_timeline WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()

                if not result:
                    return {"aspects": {}}

                import json
                aspects = json.loads(result['aspect_sentiment_json'])
                return {"aspects": aspects}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取切面分析失败: {str(e)}")
