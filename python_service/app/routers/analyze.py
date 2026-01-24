"""分析服务API路由"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from ..models.schemas import (
    AnalyzeVideoRequest,
    AnalyzeVideoResponse,
    ProgressResponse
)
from ..services.scraper import ScraperService
from ..services.sentiment import SentimentAnalyzer
from ..services.timeline import TimelineGenerator
from ..database.repository import DatabaseRepository

router = APIRouter()

# 初始化服务实例
scraper = ScraperService()
sentiment_analyzer = SentimentAnalyzer()
timeline_generator = TimelineGenerator()
db_repo = DatabaseRepository()


async def analyze_video_task(task_id: int, bvid: str, sessdata: str = None):
    """
    视频分析后台任务 (异步)

    Args:
        task_id: 任务ID
        bvid: 视频BVID
        sessdata: B站登录凭证（可选）
    """
    try:
        # 步骤1: 爬取视频信息 (10%)
        db_repo.update_task_progress(task_id, 10, "正在获取视频信息...")
        video_info = await scraper.get_video_info_async(bvid)
        if not video_info:
            db_repo.update_task_status(task_id, "FAILED", "无法获取视频信息")
            return

        # 步骤2: 爬取评论 (30%)
        db_repo.update_task_progress(task_id, 30, "正在爬取评论数据(TOP 10000)...")
        # 增加爬取数量：100页 -> 500页 (约10000条)，覆盖绝大多数视频
        comments = await scraper.get_comments_async(bvid, max_pages=500)

        # 空值保护
        if comments is None:
            comments = []
            print(f"警告: 视频 {bvid} 未获取到评论数据")

        # 步骤3: 分析评论情感 (50%)
        db_repo.update_task_progress(task_id, 50, "正在分析评论情感...")
        for comment in comments:
            result = sentiment_analyzer.analyze_text(comment.get('content', ''))
            comment['sentiment_score'] = result['score']
            comment['sentiment_label'] = result['label']

        # 保存评论到数据库
        if comments:
            db_repo.batch_insert_comments(task_id, bvid, comments)

        # 步骤4: 爬取弹幕 (70%)
        db_repo.update_task_progress(task_id, 70, "正在爬取弹幕数据...")
        danmakus = await scraper.get_danmakus_async(bvid, sessdata)

        # 空值保护
        if danmakus is None:
            danmakus = []
            print(f"警告: 视频 {bvid} 未获取到弹幕数据")

        # 步骤5: 分析弹幕情感 (80%)
        db_repo.update_task_progress(task_id, 80, "正在分析弹幕情感...")
        for danmaku in danmakus:
            result = sentiment_analyzer.analyze_text(danmaku.get('content', ''))
            danmaku['sentiment_score'] = result['score']
            danmaku['sentiment_label'] = result['label']

        # 保存弹幕到数据库
        if danmakus:
            db_repo.batch_insert_danmakus(task_id, bvid, danmakus)

        # 步骤6: 生成情绪时间轴 (90%)
        db_repo.update_task_progress(task_id, 90, "正在生成情绪时间轴...")
        if danmakus:
            timeline_points = timeline_generator.generate_timeline(danmakus)
            # 包装为正确的格式
            timeline_data = {
                'timeline': timeline_points,
                'aspect_sentiment': {}  # 切面分析暂未实现，预留字段
            }
            # 保存时间轴到数据库
            db_repo.batch_insert_timeline(task_id, bvid, timeline_data)

        # 步骤7: 完成 (100%)
        # 注意：状态一定要用 COMPLETED
        db_repo.update_task_progress(task_id, 100, "分析完成", status="COMPLETED")

        print(f"任务 {task_id} 完成: BVID={bvid}, 评论数={len(comments)}, 弹幕数={len(danmakus)}")

    except Exception as e:
        error_msg = f"分析任务失败: {str(e)}"
        print(f"任务 {task_id} 失败: {error_msg}")
        db_repo.update_task_status(task_id, "FAILED", error_msg)


@router.post("/video", response_model=AnalyzeVideoResponse)
async def analyze_video(request: AnalyzeVideoRequest, background_tasks: BackgroundTasks):
    """
    提交视频分析任务

    Args:
        request: 分析请求
        background_tasks: FastAPI后台任务管理器

    Returns:
        任务提交响应
    """
    try:
        # 验证任务是否存在
        task_info = db_repo.get_task_info(request.task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail=f"任务ID {request.task_id} 不存在")

        # 添加后台任务
        background_tasks.add_task(
            analyze_video_task,
            request.task_id,
            request.bvid,
            request.sessdata
        )

        return AnalyzeVideoResponse(
            status="success",
            message="分析任务已启动",
            task_id=request.task_id
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动分析任务失败: {str(e)}")


@router.get("/progress/{task_id}", response_model=ProgressResponse)
async def get_progress(task_id: int):
    """
    查询任务进度

    Args:
        task_id: 任务ID

    Returns:
        进度信息
    """
    try:
        task_info = db_repo.get_task_info(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail=f"任务ID {task_id} 不存在")

        return ProgressResponse(
            task_id=task_id,
            progress=task_info.get('progress', 0),
            current_step=task_info.get('current_step', ''),
            status=task_info.get('status', 'UNKNOWN')
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询进度失败: {str(e)}")


@router.get("/test")
async def test_sentiment():
    """测试情感分析功能"""
    test_texts = [
        "这个视频太棒了！",
        "垃圾，差评",
        "还行吧，一般般",
        "awsl，三连了！"
    ]

    results = []
    for text in test_texts:
        result = sentiment_analyzer.analyze_text(text)
        results.append({
            "text": text,
            "score": result['score'],
            "label": result['label']
        })

    return {
        "status": "success",
        "test_results": results
    }
