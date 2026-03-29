#!/usr/bin/env python3
"""
构建标注候选集脚本
从 video_comment / video_danmaku 抽样，优先选取高互动、低置信度、争议性样本
导出 CSV 供人工标注

用法:
    python build_annotation_dataset.py --task-id <task_id> --output annotation_candidates.csv
    python build_annotation_dataset.py --limit 500 --output all_candidates.csv
"""
import sys
import os
import argparse
import csv
from datetime import datetime

# 将项目根路径加入 sys.path
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


def sample_comments(cursor, task_id=None, limit=300):
    """从 video_comment 抽样候选"""
    where = "WHERE content IS NOT NULL AND CHAR_LENGTH(content) > 5"
    params = []

    if task_id:
        where += " AND task_id = %s"
        params.append(task_id)

    # 策略: 高点赞 + 低置信度 + 负面预测
    sql = f"""
        SELECT
            comment_id as source_id,
            'video_comment' as source_table,
            task_id, bvid,
            'comment' as text_type,
            content as raw_text,
            normalized_content as normalized_text,
            sentiment_label,
            sentiment_score,
            sentiment_confidence,
            like_count
        FROM video_comment
        {where}
        ORDER BY
            COALESCE(sentiment_confidence, 1.0) ASC,    -- 低置信度优先
            like_count DESC,                               -- 高互动优先
            RAND()                                         -- 随机打散
        LIMIT %s
    """
    params.append(limit)
    cursor.execute(sql, params)
    return cursor.fetchall()


def sample_danmakus(cursor, task_id=None, limit=200):
    """从 video_danmaku 抽样候选"""
    where = "WHERE content IS NOT NULL AND CHAR_LENGTH(content) > 2"
    params = []

    if task_id:
        where += " AND task_id = %s"
        params.append(task_id)

    sql = f"""
        SELECT
            danmaku_id as source_id,
            'video_danmaku' as source_table,
            task_id, bvid,
            'danmaku' as text_type,
            content as raw_text,
            normalized_content as normalized_text,
            sentiment_label,
            sentiment_score,
            sentiment_confidence,
            0 as like_count
        FROM video_danmaku
        {where}
        ORDER BY
            COALESCE(sentiment_confidence, 1.0) ASC,
            RAND()
        LIMIT %s
    """
    params.append(limit)
    cursor.execute(sql, params)
    return cursor.fetchall()


def export_csv(rows, output_path):
    """导出为标注 CSV"""
    fieldnames = [
        'source_table', 'source_id', 'task_id', 'bvid', 'text_type',
        'raw_text', 'normalized_text',
        'model_label', 'model_score', 'model_confidence',
        # 以下由人工填写
        'gold_label', 'gold_intensity', 'gold_emotion_tags', 'gold_aspect_details',
        'annotator', 'notes'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                'source_table': row.get('source_table', ''),
                'source_id': row.get('source_id', ''),
                'task_id': row.get('task_id', ''),
                'bvid': row.get('bvid', ''),
                'text_type': row.get('text_type', ''),
                'raw_text': row.get('raw_text', ''),
                'normalized_text': row.get('normalized_text', '') or '',
                'model_label': row.get('sentiment_label', ''),
                'model_score': row.get('sentiment_score', ''),
                'model_confidence': row.get('sentiment_confidence', ''),
                'gold_label': '',
                'gold_intensity': '',
                'gold_emotion_tags': '',
                'gold_aspect_details': '',
                'annotator': '',
                'notes': '',
            })

    print(f"[INFO] 已导出 {len(rows)} 条候选样本到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='构建情感标注候选集')
    parser.add_argument('--task-id', type=str, default=None, help='限定任务ID')
    parser.add_argument('--limit', type=int, default=None, help='同时设置评论与弹幕总抽样上限')
    parser.add_argument('--comment-limit', type=int, default=300, help='评论抽样数量')
    parser.add_argument('--danmaku-limit', type=int, default=200, help='弹幕抽样数量')
    parser.add_argument('--output', type=str,
                        default=f'annotation_candidates_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv',
                        help='输出文件路径')
    args = parser.parse_args()

    if args.limit is not None:
        args.comment_limit = args.limit
        args.danmaku_limit = args.limit

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            print(f"[INFO] 抽取评论候选 (limit={args.comment_limit})...")
            comments = sample_comments(cursor, args.task_id, args.comment_limit)
            print(f"[INFO] 抽取弹幕候选 (limit={args.danmaku_limit})...")
            danmakus = sample_danmakus(cursor, args.task_id, args.danmaku_limit)

        all_rows = list(comments) + list(danmakus)
        print(f"[INFO] 共计候选样本: {len(all_rows)} 条")
        export_csv(all_rows, args.output)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
