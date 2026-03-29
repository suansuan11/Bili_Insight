#!/usr/bin/env python3
"""
按任务重算情感脚本
对指定 task_id 下所有评论和弹幕用新模型重新计算情感，回写新增字段

用法:
    python recompute_sentiment_for_task.py --task-id <task_id>
    python recompute_sentiment_for_task.py --task-id <task_id> --dry-run
"""
import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))


def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'bili_insight_db'),
        'charset': 'utf8mb4',
    }


def load_analyzers():
    """加载分析器"""
    app_path = os.path.join(os.path.dirname(__file__), "..", "..", "app")
    if app_path not in sys.path:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from app.services.sentiment_analyzer import SentimentAnalyzer
    from app.services.aspect_analyzer import AspectAnalyzer
    from app.services.video_storage_service import VideoStorageService

    sa = SentimentAnalyzer()
    aa = AspectAnalyzer(sa)
    storage = VideoStorageService()
    storage.sentiment_analyzer = sa
    storage.aspect_analyzer = aa
    return sa, aa, storage


def recompute_comments(conn, task_id, sa, aa, dry_run=False):
    """重算评论情感"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT comment_id, content FROM video_comment WHERE task_id = %s AND content IS NOT NULL",
            (task_id,)
        )
        rows = cursor.fetchall()

    print(f"[INFO] 共 {len(rows)} 条评论需要重算")
    updated = 0
    failed = 0

    for i, row in enumerate(rows):
        content = row['content']
        comment_id = row['comment_id']
        try:
            sentiment = sa.analyze(content, text_type="comment")
            aspect_details = aa.analyze(content, text_type="comment")
            primary_aspect = aa.get_primary_aspect(aspect_details)

            if not dry_run:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE video_comment SET
                            normalized_content = %s,
                            sentiment_score = %s,
                            sentiment_label = %s,
                            sentiment_confidence = %s,
                            sentiment_intensity = %s,
                            sentiment_source = %s,
                            sentiment_version = %s,
                            emotion_tags_json = %s,
                            aspect = %s,
                            aspect_details_json = %s,
                            text_type = 'comment'
                        WHERE comment_id = %s
                    """, (
                        sentiment.get('normalized_text', content)[:65535],
                        sentiment.get('score', 0.0),
                        sentiment.get('label', 'NEUTRAL'),
                        sentiment.get('confidence', 0.0),
                        sentiment.get('intensity', 'WEAK'),
                        sentiment.get('source', ''),
                        sentiment.get('version', ''),
                        json.dumps(sentiment.get('emotion_tags', []), ensure_ascii=False),
                        primary_aspect,
                        json.dumps(aspect_details, ensure_ascii=False) if aspect_details else None,
                        comment_id,
                    ))
                conn.commit()
            updated += 1
        except Exception as e:
            print(f"[WARN] 评论 {comment_id} 重算失败: {e}")
            failed += 1

        if (i + 1) % 100 == 0:
            print(f"[INFO] 进度: {i + 1}/{len(rows)}, 成功={updated}, 失败={failed}")

    print(f"[INFO] 评论重算完成: 成功={updated}, 失败={failed}")
    return updated, failed


def recompute_danmakus(conn, task_id, sa, dry_run=False):
    """重算弹幕情感"""
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT danmaku_id, content FROM video_danmaku WHERE task_id = %s AND content IS NOT NULL",
            (task_id,)
        )
        rows = cursor.fetchall()

    print(f"[INFO] 共 {len(rows)} 条弹幕需要重算")
    updated = 0
    failed = 0

    for i, row in enumerate(rows):
        content = row['content']
        danmaku_id = row['danmaku_id']
        try:
            sentiment = sa.analyze(content, text_type="danmaku")

            if not dry_run:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        UPDATE video_danmaku SET
                            normalized_content = %s,
                            sentiment_score = %s,
                            sentiment_label = %s,
                            sentiment_confidence = %s,
                            sentiment_intensity = %s,
                            sentiment_source = %s,
                            sentiment_version = %s,
                            emotion_tags_json = %s,
                            text_type = 'danmaku'
                        WHERE danmaku_id = %s
                    """, (
                        sentiment.get('normalized_text', content)[:65535],
                        sentiment.get('score', 0.0),
                        sentiment.get('label', 'NEUTRAL'),
                        sentiment.get('confidence', 0.0),
                        sentiment.get('intensity', 'WEAK'),
                        sentiment.get('source', ''),
                        sentiment.get('version', ''),
                        json.dumps(sentiment.get('emotion_tags', []), ensure_ascii=False),
                        danmaku_id,
                    ))
                conn.commit()
            updated += 1
        except Exception as e:
            print(f"[WARN] 弹幕 {danmaku_id} 重算失败: {e}")
            failed += 1

        if (i + 1) % 500 == 0:
            print(f"[INFO] 进度: {i + 1}/{len(rows)}, 成功={updated}, 失败={failed}")

    print(f"[INFO] 弹幕重算完成: 成功={updated}, 失败={failed}")
    return updated, failed


async def rebuild_timeline(storage, task_id, task_bvid, dry_run=False):
    """重建时间轴与切面聚合"""
    if dry_run:
        print("[INFO] DRY RUN: 跳过时间轴重建")
        return
    await storage.generate_sentiment_timeline(task_id, task_bvid)
    print(f"[INFO] 已重建 sentiment_timeline: task_id={task_id}")


def main():
    parser = argparse.ArgumentParser(description='按任务重算情感')
    parser.add_argument('--task-id', type=str, required=True, help='任务ID')
    parser.add_argument('--dry-run', action='store_true', help='不写库，仅验证分析流程')
    args = parser.parse_args()

    print(f"[INFO] 开始重算任务: {args.task_id} {'[DRY RUN]' if args.dry_run else ''}")
    start = datetime.now()

    print("[INFO] 加载分析器...")
    sa, aa, storage = load_analyzers()

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT bvid FROM analysis_task WHERE task_id = %s", (args.task_id,))
            task = cursor.fetchone()
            if not task:
                raise RuntimeError(f"任务不存在: {args.task_id}")
        c_updated, c_failed = recompute_comments(conn, args.task_id, sa, aa, args.dry_run)
        d_updated, d_failed = recompute_danmakus(conn, args.task_id, sa, args.dry_run)
    finally:
        conn.close()

    import asyncio
    asyncio.run(rebuild_timeline(storage, args.task_id, task["bvid"], args.dry_run))

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n[INFO] 完成! 耗时 {elapsed:.1f}s")
    print(f"  评论: 成功={c_updated}, 失败={c_failed}")
    print(f"  弹幕: 成功={d_updated}, 失败={d_failed}")


if __name__ == '__main__':
    main()
