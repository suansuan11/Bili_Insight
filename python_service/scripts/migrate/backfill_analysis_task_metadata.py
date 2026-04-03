#!/usr/bin/env python3
"""
回填 analysis_task 元数据

功能:
1. 为缺失 video_title 的历史任务按 bvid 回填视频标题
2. 从 sentiment_timeline.aggregation_meta_json 回填历史任务的评论抓取元数据

用法:
    python backfill_analysis_task_metadata.py
    python backfill_analysis_task_metadata.py --task-id <task_id>
    python backfill_analysis_task_metadata.py --dry-run
"""
import argparse
import asyncio
import json
import os
import sys
from collections import defaultdict
from typing import Dict, List, Optional

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor


ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, ROOT)

from app.services.bilibili_service import BilibiliService  # noqa: E402


load_dotenv(os.path.join(ROOT, ".env"))


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "bili_insight_db"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
    }


def load_tasks(conn, task_id: Optional[str]) -> List[Dict]:
    with conn.cursor() as cursor:
        if task_id:
            cursor.execute(
                """
                SELECT task_id, bvid, video_title, comment_fetch_mode,
                       comment_risk_controlled, comment_fetch_retries
                FROM analysis_task
                WHERE task_id = %s
                """,
                (task_id,),
            )
        else:
            cursor.execute(
                """
                SELECT task_id, bvid, video_title, comment_fetch_mode,
                       comment_risk_controlled, comment_fetch_retries
                FROM analysis_task
                WHERE video_title IS NULL
                   OR comment_fetch_mode IS NULL
                   OR comment_fetch_retries = 0
                ORDER BY created_at DESC
                """
            )
        return cursor.fetchall()


def load_timeline_meta(conn, task_ids: List[str]) -> Dict[str, Dict]:
    if not task_ids:
        return {}

    placeholders = ",".join(["%s"] * len(task_ids))
    with conn.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT task_id, aggregation_meta_json
            FROM sentiment_timeline
            WHERE task_id IN ({placeholders})
            """,
            task_ids,
        )
        rows = cursor.fetchall()

    meta_map: Dict[str, Dict] = {}
    for row in rows:
        raw = row.get("aggregation_meta_json")
        if not raw:
            continue
        try:
            payload = json.loads(raw)
        except Exception:
            continue
        comment_fetch = payload.get("comment_fetch")
        if isinstance(comment_fetch, dict):
            meta_map[row["task_id"]] = comment_fetch
    return meta_map


async def fetch_title_map(bvids: List[str]) -> Dict[str, str]:
    service = BilibiliService()
    title_map: Dict[str, str] = {}
    for bvid in bvids:
        try:
            info = await service.get_video_info(bvid)
            title = (info or {}).get("title")
            if title:
                title_map[bvid] = title[:255]
                print(f"[INFO] 标题回填成功 {bvid} -> {title}")
            else:
                print(f"[WARN] 未获取到标题: {bvid}")
        except Exception as exc:
            print(f"[WARN] 获取标题失败 {bvid}: {exc}")
    return title_map


def apply_updates(conn, tasks: List[Dict], title_map: Dict[str, str], timeline_meta: Dict[str, Dict], dry_run: bool):
    title_updates = 0
    meta_updates = 0

    grouped_by_bvid: Dict[str, List[str]] = defaultdict(list)
    for task in tasks:
        if not task.get("video_title") and title_map.get(task["bvid"]):
            grouped_by_bvid[task["bvid"]].append(task["task_id"])

    for bvid, task_ids in grouped_by_bvid.items():
        if dry_run:
            title_updates += len(task_ids)
            continue
        with conn.cursor() as cursor:
            placeholders = ",".join(["%s"] * len(task_ids))
            cursor.execute(
                f"""
                UPDATE analysis_task
                SET video_title = %s, updated_at = NOW()
                WHERE task_id IN ({placeholders})
                """,
                [title_map[bvid], *task_ids],
            )
        title_updates += len(task_ids)

    for task in tasks:
        fetch_meta = timeline_meta.get(task["task_id"])
        if not fetch_meta:
            continue
        should_update = (
            task.get("comment_fetch_mode") != fetch_meta.get("mode")
            or int(task.get("comment_risk_controlled") or 0) != (1 if fetch_meta.get("risk_controlled") else 0)
            or int(task.get("comment_fetch_retries") or 0) != int(fetch_meta.get("retries") or 0)
        )
        if not should_update:
            continue

        if dry_run:
            meta_updates += 1
            continue

        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE analysis_task
                SET comment_fetch_mode = %s,
                    comment_risk_controlled = %s,
                    comment_fetch_retries = %s,
                    updated_at = NOW()
                WHERE task_id = %s
                """,
                (
                    fetch_meta.get("mode"),
                    1 if fetch_meta.get("risk_controlled") else 0,
                    int(fetch_meta.get("retries") or 0),
                    task["task_id"],
                ),
            )
        meta_updates += 1

    if not dry_run:
        conn.commit()

    return title_updates, meta_updates


def main():
    parser = argparse.ArgumentParser(description="回填 analysis_task 元数据")
    parser.add_argument("--task-id", help="只处理单个任务")
    parser.add_argument("--dry-run", action="store_true", help="不写库，只输出计划")
    args = parser.parse_args()

    conn = pymysql.connect(**get_db_config())
    try:
        tasks = load_tasks(conn, args.task_id)
        if not tasks:
            print("[INFO] 没有需要回填的任务")
            return

        print(f"[INFO] 待处理任务数: {len(tasks)}")
        missing_title_bvids = sorted({task["bvid"] for task in tasks if not task.get("video_title")})
        timeline_meta = load_timeline_meta(conn, [task["task_id"] for task in tasks])

        title_map = {}
        if missing_title_bvids:
            print(f"[INFO] 需要补标题的唯一 BVID 数: {len(missing_title_bvids)}")
            title_map = asyncio.run(fetch_title_map(missing_title_bvids))

        title_updates, meta_updates = apply_updates(conn, tasks, title_map, timeline_meta, args.dry_run)
        print(f"[INFO] 回填完成: title_updates={title_updates}, meta_updates={meta_updates}, dry_run={args.dry_run}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
