#!/usr/bin/env python3
"""Build targeted annotation candidates to balance sentiment labels.

This sampler is designed for the post-evaluation stage where the gold set is
too imbalanced. It excludes already imported sentiment_annotation rows and
over-samples likely NEGATIVE/POSITIVE examples for reviewer confirmation.
"""
import argparse
import csv
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

FIELDNAMES = [
    "source_table", "source_id", "task_id", "bvid", "text_type",
    "raw_text", "normalized_text",
    "model_label", "model_score", "model_confidence",
    "gold_label", "gold_intensity", "gold_emotion_tags", "gold_aspect_details",
    "annotator", "notes",
]


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "bili_insight_db"),
        "charset": "utf8mb4",
    }


def fetch_rows(cursor, source: str, label: str, limit: int, min_confidence: float, seed: int):
    if limit <= 0:
        return []

    if source == "comment":
        table = "video_comment"
        id_col = "comment_id"
        text_col = "content"
        normalized_col = "normalized_content"
        source_table = "video_comment"
        like_expr = "COALESCE(v.like_count, 0)"
        length_filter = "CHAR_LENGTH(v.content) >= 4"
    else:
        table = "video_danmaku"
        id_col = "danmaku_id"
        text_col = "content"
        normalized_col = "normalized_content"
        source_table = "video_danmaku"
        like_expr = "0"
        length_filter = "CHAR_LENGTH(v.content) >= 2"

    if label == "NEGATIVE":
        score_filter = "v.sentiment_score <= -0.24"
        score_order = "v.sentiment_score ASC"
    elif label == "POSITIVE":
        score_filter = "v.sentiment_score >= 0.24"
        score_order = "v.sentiment_score DESC"
    else:
        score_filter = "ABS(v.sentiment_score) < 0.18"
        score_order = "ABS(v.sentiment_score) ASC"

    sql = f"""
        SELECT
            v.{id_col} AS source_id,
            %s AS source_table,
            v.task_id,
            v.bvid,
            %s AS text_type,
            v.{text_col} AS raw_text,
            v.{normalized_col} AS normalized_text,
            v.sentiment_label AS model_label,
            v.sentiment_score AS model_score,
            v.sentiment_confidence AS model_confidence,
            {like_expr} AS interaction_score
        FROM {table} v
        LEFT JOIN sentiment_annotation sa
          ON sa.source_table = %s
         AND sa.source_id = v.{id_col}
         AND sa.text_type = %s
        WHERE sa.id IS NULL
          AND v.{text_col} IS NOT NULL
          AND {length_filter}
          AND v.sentiment_label = %s
          AND COALESCE(v.sentiment_confidence, 0) >= %s
          AND {score_filter}
        ORDER BY
          CASE WHEN {like_expr} > 0 THEN 0 ELSE 1 END ASC,
          {score_order},
          COALESCE(v.sentiment_confidence, 0) DESC,
          RAND(%s)
        LIMIT %s
    """
    text_type = "comment" if source == "comment" else "danmaku"
    cursor.execute(sql, (
        source_table,
        text_type,
        source_table,
        text_type,
        label,
        min_confidence,
        seed,
        limit,
    ))
    rows = cursor.fetchall()
    for row in rows:
        row["target_label"] = label
        row["target_source"] = source
    return rows


def export_csv(rows, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    written = 0
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            key = (row.get("source_table"), row.get("source_id"), row.get("text_type"))
            if key in seen:
                continue
            seen.add(key)
            notes = (
                f"targeted_expansion=true; target_label={row.get('target_label')}; "
                f"target_source={row.get('target_source')}; "
                f"model_confidence={float(row.get('model_confidence') or 0):.4f}; "
                f"model_score={float(row.get('model_score') or 0):.4f}"
            )
            writer.writerow({
                "source_table": row.get("source_table", ""),
                "source_id": row.get("source_id", ""),
                "task_id": row.get("task_id", ""),
                "bvid": row.get("bvid", ""),
                "text_type": row.get("text_type", ""),
                "raw_text": row.get("raw_text", ""),
                "normalized_text": row.get("normalized_text", "") or "",
                "model_label": row.get("model_label", ""),
                "model_score": row.get("model_score", ""),
                "model_confidence": row.get("model_confidence", ""),
                "gold_label": "",
                "gold_intensity": "",
                "gold_emotion_tags": "",
                "gold_aspect_details": "",
                "annotator": "",
                "notes": notes,
            })
            written += 1
    print(f"[INFO] exported {written} targeted rows to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Build targeted sentiment annotation candidates")
    parser.add_argument("--negative-comments", type=int, default=120)
    parser.add_argument("--negative-danmakus", type=int, default=120)
    parser.add_argument("--positive-comments", type=int, default=100)
    parser.add_argument("--positive-danmakus", type=int, default=60)
    parser.add_argument("--min-confidence", type=float, default=0.55)
    parser.add_argument("--seed", type=int, default=20260415)
    parser.add_argument("--output", type=Path, default=Path("python_service/scripts/eval/targeted_expansion_candidates.csv"))
    args = parser.parse_args()

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            rows = []
            rows.extend(fetch_rows(cursor, "comment", "NEGATIVE", args.negative_comments, args.min_confidence, args.seed))
            rows.extend(fetch_rows(cursor, "danmaku", "NEGATIVE", args.negative_danmakus, args.min_confidence, args.seed + 1))
            rows.extend(fetch_rows(cursor, "comment", "POSITIVE", args.positive_comments, args.min_confidence, args.seed + 2))
            rows.extend(fetch_rows(cursor, "danmaku", "POSITIVE", args.positive_danmakus, args.min_confidence, args.seed + 3))
    finally:
        conn.close()

    export_csv(rows, args.output)


if __name__ == "__main__":
    main()
