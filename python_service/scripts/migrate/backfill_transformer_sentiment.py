#!/usr/bin/env python3
"""
批量回填 Transformer 情感分析结果
对历史任务分批回填新模型情感结果

用法:
    python backfill_transformer_sentiment.py --limit 1000 --dry-run
    python backfill_transformer_sentiment.py --date-from 2026-01-01 --date-to 2026-03-01
    python backfill_transformer_sentiment.py --only-completed --limit 500
"""
import sys
import os
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


def get_target_tasks(cursor, date_from=None, date_to=None, only_completed=False, limit=None):
    """查询待回填任务列表"""
    where_clauses = []
    params = []

    if only_completed:
        where_clauses.append("status = 'COMPLETED'")

    if date_from:
        where_clauses.append("created_at >= %s")
        params.append(date_from)

    if date_to:
        where_clauses.append("created_at <= %s")
        params.append(date_to)

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    limit_clause = f"LIMIT {int(limit)}" if limit else ""

    cursor.execute(
        f"SELECT task_id, bvid, status, created_at FROM analysis_task {where} ORDER BY created_at ASC {limit_clause}",
        params
    )
    return cursor.fetchall()


def main():
    parser = argparse.ArgumentParser(description='批量回填 Transformer 情感结果')
    parser.add_argument('--date-from', type=str, default=None, help='起始日期 YYYY-MM-DD')
    parser.add_argument('--date-to', type=str, default=None, help='结束日期 YYYY-MM-DD')
    parser.add_argument('--limit', type=int, default=None, help='最多处理任务数')
    parser.add_argument('--only-completed', action='store_true', help='只回填 COMPLETED 任务')
    parser.add_argument('--dry-run', action='store_true', help='不写库，仅模拟')
    parser.add_argument('--batch-size', type=int, default=1, help='相邻任务之间不做暂停，批次单位为任务数')
    args = parser.parse_args()

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            tasks = get_target_tasks(
                cursor,
                date_from=args.date_from,
                date_to=args.date_to,
                only_completed=args.only_completed,
                limit=args.limit,
            )
    finally:
        conn.close()

    if not tasks:
        print("[INFO] 未找到符合条件的任务")
        return

    print(f"[INFO] 共找到 {len(tasks)} 个任务需要回填 {'[DRY RUN]' if args.dry_run else ''}")

    # 复用单任务脚本逻辑
    from recompute_sentiment_for_task import (
        load_analyzers,
        recompute_comments,
        recompute_danmakus,
        rebuild_timeline,
    )

    print("[INFO] 加载分析器（首次加载可能需要下载模型）...")
    sa, aa, storage = load_analyzers()

    total_c_ok = total_c_fail = total_d_ok = total_d_fail = 0
    start = datetime.now()

    for i, task in enumerate(tasks):
        task_id = task['task_id']
        print(f"\n[{i + 1}/{len(tasks)}] 处理任务: {task_id} (bvid={task.get('bvid', 'N/A')})")

        conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
        try:
            c_ok, c_fail = recompute_comments(conn, task_id, sa, aa, args.dry_run)
            d_ok, d_fail = recompute_danmakus(conn, task_id, sa, args.dry_run)
            import asyncio
            asyncio.run(rebuild_timeline(storage, task_id, task["bvid"], args.dry_run))
            total_c_ok += c_ok
            total_c_fail += c_fail
            total_d_ok += d_ok
            total_d_fail += d_fail
        except Exception as e:
            print(f"[ERROR] 任务 {task_id} 处理失败: {e}")
        finally:
            conn.close()

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n[INFO] 批量回填完成! 总耗时 {elapsed:.1f}s")
    print(f"  评论: 成功={total_c_ok}, 失败={total_c_fail}")
    print(f"  弹幕: 成功={total_d_ok}, 失败={total_d_fail}")


if __name__ == '__main__':
    main()
