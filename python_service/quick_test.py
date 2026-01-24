"""
快速测试脚本 - 测试BV18TqpBqEMG视频
简化版，快速验证数据获取和存储流程
"""
import asyncio
import sys
import os
from pathlib import Path

# 设置UTF-8输出
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')

sys.path.insert(0, str(Path(__file__).parent))

from app.services.bilibili_service import BilibiliService
from app.services.credential_manager import get_credential_manager


async def quick_test():
    """快速测试：只获取数据，不存储"""
    bvid = "BV18TqpBqEMG"

    print("=" * 60)
    print(f"快速测试: {bvid}")
    print("=" * 60)

    # 初始化服务
    credential = get_credential_manager().get_credential()
    bili_service = BilibiliService(credential=credential)

    # 1. 获取视频信息
    print("\n[1/3] 获取视频信息...")
    video_info = await bili_service.get_video_info(bvid)

    if video_info:
        print(f"[OK] Title: {video_info['title']}")
        print(f"[OK] Author: {video_info['author']}")
        print(f"[OK] Views: {video_info['view_count']:,}")
        print(f"[OK] Danmakus: {video_info['danmaku_count']:,}")
    else:
        print("[FAIL] Video info fetch failed")
        return

    # 2. 获取评论（少量测试）
    print("\n[2/3] 获取评论（前20条）...")
    comments = await bili_service.get_comments(bvid, max_count=20)
    print(f"[OK] Fetched {len(comments)} comments")

    if len(comments) > 0:
        print("\n示例评论:")
        for i, c in enumerate(comments[:3], 1):
            print(f"  {i}. {c['author']}: {c['content'][:30]}...")

    # 3. 获取弹幕（少量测试）
    print("\n[3/3] Fetching danmakus...")
    danmakus = await bili_service.get_danmakus(bvid)
    print(f"[OK] Fetched {len(danmakus)} danmakus")

    if len(danmakus) > 0:
        print("\nSample danmakus:")
        for i, dm in enumerate(danmakus[:5], 1):
            print(f"  {i}. [{dm['dm_time']:.1f}s] {dm['content']}")

    # 测试NLP
    print("\n" + "=" * 60)
    print("NLP Sentiment Analysis Test")
    print("=" * 60)

    from app.services.video_storage_service import VideoStorageService
    storage = VideoStorageService()

    test_texts = [
        "这个手机真的太好看了，外观设计非常漂亮",
        "性能很差，经常卡顿，太失望了",
        "价格还行，中规中矩吧"
    ]

    for text in test_texts:
        score, label = storage.calculate_sentiment(text)
        aspect = storage.detect_aspect(text)
        print(f"\nText: {text}")
        print(f"Score: {score:.4f} | Label: {label}")
        print(f"Aspect: {aspect or 'None'}")

    print("\n[SUCCESS] Quick test completed!")
    print("\nRun 'python test_full_video_analysis.py' for full test with database storage")


if __name__ == "__main__":
    asyncio.run(quick_test())
