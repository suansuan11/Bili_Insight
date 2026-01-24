"""
完整视频数据获取与存储测试
测试视频: BV18TqpBqEMG
功能: 获取视频信息、所有评论、所有弹幕，并存入数据库
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径到sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.bilibili_service import BilibiliService
from app.services.credential_manager import get_credential_manager
from app.services.video_storage_service import VideoStorageService


async def test_full_analysis(bvid: str):
    """完整的视频数据获取与存储流程"""

    print("=" * 60)
    print(f"开始分析视频: {bvid}")
    print("=" * 60)

    # 1. 初始化服务
    credential = get_credential_manager().get_credential()
    if credential:
        print("✓ 使用已登录凭证")
    else:
        print("⚠ 使用游客模式（可能部分功能受限）")

    bili_service = BilibiliService(credential=credential)
    storage_service = VideoStorageService()

    # 2. 创建分析任务
    print("\n[1/5] 创建分析任务...")
    task_id = await storage_service.create_task(bvid, task_type="FULL_ANALYSIS")
    print(f"✓ 任务ID: {task_id}")

    try:
        # 3. 获取视频信息
        print("\n[2/5] 获取视频基础信息...")
        await storage_service.update_task_progress(task_id, 10, "正在获取视频信息")

        video_info = await bili_service.get_video_info(bvid)
        if not video_info:
            raise Exception("获取视频信息失败")

        print(f"✓ 标题: {video_info['title']}")
        print(f"✓ UP主: {video_info['author']}")
        print(f"✓ 播放: {video_info['view_count']:,} | 点赞: {video_info['like_count']:,}")
        print(f"✓ 弹幕数: {video_info['danmaku_count']:,}")

        # 4. 获取所有评论
        print("\n[3/5] 获取所有评论...")
        await storage_service.update_task_progress(task_id, 30, "正在获取评论")

        comments = await bili_service.get_comments(bvid, max_count=500)
        print(f"✓ 共获取 {len(comments)} 条评论")

        # 保存评论到数据库
        saved_count = await storage_service.save_comments(task_id, bvid, comments)
        print(f"✓ 已存入数据库: {saved_count} 条评论")

        # 5. 获取所有弹幕
        print("\n[4/5] 获取所有弹幕...")
        await storage_service.update_task_progress(task_id, 60, "正在获取弹幕")

        danmakus = await bili_service.get_danmakus(bvid)
        print(f"✓ 共获取 {len(danmakus)} 条弹幕")

        # 保存弹幕到数据库
        saved_count = await storage_service.save_danmakus(task_id, bvid, danmakus)
        print(f"✓ 已存入数据库: {saved_count} 条弹幕")

        # 6. 生成情绪时间轴
        print("\n[5/5] 生成情绪时间轴...")
        await storage_service.update_task_progress(task_id, 90, "正在生成情绪时间轴")

        timeline_data = await storage_service.generate_sentiment_timeline(task_id, bvid)
        print(f"✓ 时间轴数据点: {len(timeline_data['timeline'])}")
        print(f"✓ 切面分析: {list(timeline_data['aspects'].keys())}")

        # 完成任务
        await storage_service.complete_task(task_id)

        # 打印统计信息
        print("\n" + "=" * 60)
        print("分析完成！数据存储统计:")
        print("=" * 60)
        print(f"任务ID: {task_id}")
        print(f"视频BVID: {bvid}")
        print(f"评论数: {len(comments)}")
        print(f"弹幕数: {len(danmakus)}")
        print(f"情绪时间点: {len(timeline_data['timeline'])}")
        print(f"切面维度: {len(timeline_data['aspects'])}")
        print("\n✅ 所有数据已保存到MySQL数据库")
        print(f"✅ 可通过任务ID({task_id})查询分析结果")

        return task_id

    except Exception as e:
        print(f"\n❌ 分析失败: {e}")
        await storage_service.fail_task(task_id, str(e))
        raise


async def query_task_results(task_id: int):
    """查询任务结果"""
    storage_service = VideoStorageService()

    print("\n" + "=" * 60)
    print(f"查询任务结果: Task ID = {task_id}")
    print("=" * 60)

    # 查询任务状态
    task_info = await storage_service.get_task_info(task_id)
    print(f"\n任务状态: {task_info['status']}")
    print(f"进度: {task_info['progress']}%")
    print(f"创建时间: {task_info['created_at']}")
    print(f"完成时间: {task_info.get('completed_at', 'N/A')}")

    # 查询评论统计
    comment_stats = await storage_service.get_comment_stats(task_id)
    print(f"\n评论统计:")
    print(f"  总数: {comment_stats['total']}")
    print(f"  正面: {comment_stats['positive']} ({comment_stats['positive_rate']:.1%})")
    print(f"  中性: {comment_stats['neutral']} ({comment_stats['neutral_rate']:.1%})")
    print(f"  负面: {comment_stats['negative']} ({comment_stats['negative_rate']:.1%})")

    # 查询弹幕统计
    danmaku_stats = await storage_service.get_danmaku_stats(task_id)
    print(f"\n弹幕统计:")
    print(f"  总数: {danmaku_stats['total']}")
    print(f"  正面: {danmaku_stats['positive']} ({danmaku_stats['positive_rate']:.1%})")
    print(f"  中性: {danmaku_stats['neutral']} ({danmaku_stats['neutral_rate']:.1%})")
    print(f"  负面: {danmaku_stats['negative']} ({danmaku_stats['negative_rate']:.1%})")


async def main():
    """主函数"""
    # 测试视频BVID
    bvid = "BV18TqpBqEMG"

    # 执行完整分析
    task_id = await test_full_analysis(bvid)

    # 查询结果（可选）
    # await query_task_results(task_id)


if __name__ == "__main__":
    asyncio.run(main())
