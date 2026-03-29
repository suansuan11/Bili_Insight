#!/usr/bin/env python3
"""
导出低置信度样本
从生产数据中导出低置信度样本，供人工二次标注，形成持续回流闭环

用法:
    python export_low_confidence_samples.py --threshold 0.6 --limit 200
"""
import sys
import os
import csv
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


def export_low_confidence(cursor, threshold, limit, text_type=None):
    rows = []

    # 评论
    if text_type is None or text_type == 'comment':
        sql = """
            SELECT
                comment_id as source_id, 'video_comment' as source_table,
                task_id, bvid, 'comment' as text_type,
                content as raw_text, normalized_content,
                sentiment_label, sentiment_score, sentiment_confidence,
                emotion_tags_json, aspect
            FROM video_comment
            WHERE sentiment_confidence IS NOT NULL
              AND sentiment_confidence < %s
              AND content IS NOT NULL
            ORDER BY sentiment_confidence ASC, RAND()
            LIMIT %s
        """
        cursor.execute(sql, (threshold, limit))
        rows.extend(cursor.fetchall())

    # 弹幕
    if text_type is None or text_type == 'danmaku':
        sql = """
            SELECT
                danmaku_id as source_id, 'video_danmaku' as source_table,
                task_id, bvid, 'danmaku' as text_type,
                content as raw_text, normalized_content,
                sentiment_label, sentiment_score, sentiment_confidence,
                emotion_tags_json, NULL as aspect
            FROM video_danmaku
            WHERE sentiment_confidence IS NOT NULL
              AND sentiment_confidence < %s
              AND content IS NOT NULL
            ORDER BY sentiment_confidence ASC, RAND()
            LIMIT %s
        """
        cursor.execute(sql, (threshold, limit))
        rows.extend(cursor.fetchall())

    return rows


def save_csv(rows, output_path):
    fieldnames = [
        'source_table', 'source_id', 'task_id', 'bvid', 'text_type',
        'raw_text', 'normalized_content',
        'model_label', 'model_score', 'model_confidence',
        'emotion_tags_json', 'aspect',
        # 待人工填写
        'gold_label', 'gold_intensity', 'notes'
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
                'normalized_content': row.get('normalized_content', '') or '',
                'model_label': row.get('sentiment_label', ''),
                'model_score': row.get('sentiment_score', ''),
                'model_confidence': row.get('sentiment_confidence', ''),
                'emotion_tags_json': row.get('emotion_tags_json', '') or '',
                'aspect': row.get('aspect', '') or '',
                'gold_label': '',
                'gold_intensity': '',
                'notes': '',
            })
    print(f"[INFO] 已导出 {len(rows)} 条低置信度样本到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='导出低置信度样本')
    parser.add_argument('--threshold', type=float, default=0.6, help='置信度阈值')
    parser.add_argument('--limit', type=int, default=200, help='每类最大导出数')
    parser.add_argument('--text-type', type=str, default=None, choices=['comment', 'danmaku'])
    parser.add_argument('--output', type=str,
                        default=f'low_confidence_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    args = parser.parse_args()

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            rows = export_low_confidence(cursor, args.threshold, args.limit, args.text_type)
    finally:
        conn.close()

    if not rows:
        print(f"[INFO] 未找到置信度 < {args.threshold} 的样本，可能模型尚未回写 confidence 字段")
        return

    save_csv(rows, args.output)


if __name__ == '__main__':
    main()
