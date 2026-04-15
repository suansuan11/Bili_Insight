#!/usr/bin/env python3
"""Import manually labeled sentiment CSV rows into sentiment_annotation.

Only rows with a non-empty gold_label are imported. This script does not infer
labels; leaving a row unlabeled keeps it out of evaluation.
"""
import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

VALID_LABELS = {"POSITIVE", "NEUTRAL", "NEGATIVE"}
VALID_INTENSITIES = {"", "WEAK", "MEDIUM", "STRONG"}


def is_ai_prelabeled_annotator(value: str) -> bool:
    return (value or "").strip().lower().startswith("ai_prelabel")


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "bili_insight_db"),
        "charset": "utf8mb4",
    }


def parse_json_or_list(value: str) -> Optional[str]:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = [item.strip() for item in value.split(",") if item.strip()]
    return json.dumps(parsed, ensure_ascii=False)


def normalize_row(
    row: dict,
    line_no: int,
    reviewed_by: Optional[str] = None,
    allow_ai_prelabel: bool = False,
) -> Optional[dict]:
    gold_label = (row.get("gold_label") or "").strip().upper()
    if not gold_label:
        return None
    if gold_label not in VALID_LABELS:
        raise ValueError(f"line {line_no}: invalid gold_label={gold_label!r}")

    gold_intensity = (row.get("gold_intensity") or "").strip().upper()
    if gold_intensity not in VALID_INTENSITIES:
        raise ValueError(f"line {line_no}: invalid gold_intensity={gold_intensity!r}")

    raw_text = row.get("raw_text") or ""
    if not raw_text.strip():
        raise ValueError(f"line {line_no}: raw_text is required")

    annotator = (reviewed_by or row.get("annotator") or "").strip()
    if not annotator:
        raise ValueError(f"line {line_no}: annotator is required for imported gold labels")
    if is_ai_prelabeled_annotator(annotator) and not allow_ai_prelabel:
        raise ValueError(f"line {line_no}: annotator must be a human reviewer, got {annotator!r}")

    notes = row.get("notes") or ""
    if reviewed_by:
        notes = f"{notes}; human_reviewed_by={reviewed_by}; ai_prelabel_confirmed_or_corrected=true"

    return {
        "source_table": row.get("source_table") or "",
        "source_id": int(row.get("source_id") or 0),
        "task_id": row.get("task_id") or None,
        "bvid": row.get("bvid") or None,
        "text_type": (row.get("text_type") or "comment").strip(),
        "raw_text": raw_text,
        "normalized_text": row.get("normalized_text") or row.get("normalized_content") or None,
        "gold_label": gold_label,
        "gold_intensity": gold_intensity or None,
        "gold_emotion_tags_json": parse_json_or_list(row.get("gold_emotion_tags") or ""),
        "gold_aspect_details_json": parse_json_or_list(row.get("gold_aspect_details") or ""),
        "annotator": annotator,
        "notes": notes[:255] or None,
    }


def read_labeled_rows(
    csv_path: Path,
    reviewed_by: Optional[str] = None,
    allow_ai_prelabel: bool = False,
):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            normalized = normalize_row(
                row,
                line_no,
                reviewed_by=reviewed_by,
                allow_ai_prelabel=allow_ai_prelabel,
            )
            if normalized:
                rows.append(normalized)
    return rows


def upsert_annotation(cursor, row: dict) -> str:
    cursor.execute(
        """
        SELECT id FROM sentiment_annotation
        WHERE source_table = %s AND source_id = %s AND text_type = %s
        ORDER BY id ASC LIMIT 1
        """,
        (row["source_table"], row["source_id"], row["text_type"]),
    )
    existing = cursor.fetchone()
    if existing:
        cursor.execute(
            """
            UPDATE sentiment_annotation
            SET task_id = %s, bvid = %s, raw_text = %s, normalized_text = %s,
                gold_label = %s, gold_intensity = %s,
                gold_emotion_tags_json = %s,
                gold_aspect_details_json = %s,
                annotator = %s, notes = %s
            WHERE id = %s
            """,
            (
                row["task_id"],
                row["bvid"],
                row["raw_text"],
                row["normalized_text"],
                row["gold_label"],
                row["gold_intensity"],
                row["gold_emotion_tags_json"],
                row["gold_aspect_details_json"],
                row["annotator"],
                row["notes"],
                existing["id"],
            ),
        )
        return "updated"

    cursor.execute(
        """
        INSERT INTO sentiment_annotation
            (source_table, source_id, task_id, bvid, text_type,
             raw_text, normalized_text, gold_label, gold_intensity,
             gold_emotion_tags_json, gold_aspect_details_json, annotator, notes)
        VALUES
            (%s, %s, %s, %s, %s, %s, %s, %s, %s,
             %s, %s, %s, %s)
        """,
        (
            row["source_table"],
            row["source_id"],
            row["task_id"],
            row["bvid"],
            row["text_type"],
            row["raw_text"],
            row["normalized_text"],
            row["gold_label"],
            row["gold_intensity"],
            row["gold_emotion_tags_json"],
            row["gold_aspect_details_json"],
            row["annotator"],
            row["notes"],
        ),
    )
    return "inserted"


def main():
    parser = argparse.ArgumentParser(description="Import labeled annotation CSV")
    parser.add_argument("csv_path", type=Path, help="CSV exported by build_annotation_dataset.py")
    parser.add_argument("--dry-run", action="store_true", help="Validate rows without writing DB")
    parser.add_argument(
        "--reviewed-by",
        type=str,
        default=None,
        help="Human reviewer name. Overrides the CSV annotator column during import.",
    )
    parser.add_argument(
        "--allow-ai-prelabel",
        action="store_true",
        help="Allow importing rows whose annotator is ai_prelabel*. Not recommended for final gold evaluation.",
    )
    args = parser.parse_args()

    rows = read_labeled_rows(
        args.csv_path,
        reviewed_by=args.reviewed_by,
        allow_ai_prelabel=args.allow_ai_prelabel,
    )
    if not rows:
        print("[WARN] CSV 中没有 gold_label 非空的样本，未导入任何数据")
        return

    if args.dry_run:
        counts = {}
        for row in rows:
            counts[row["gold_label"]] = counts.get(row["gold_label"], 0) + 1
        print(f"[INFO] dry-run validated {len(rows)} labeled rows: {counts}")
        return

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    inserted = updated = 0
    try:
        with conn.cursor() as cursor:
            for row in rows:
                action = upsert_annotation(cursor, row)
                inserted += action == "inserted"
                updated += action == "updated"
        conn.commit()
    finally:
        conn.close()

    print(f"[INFO] 导入完成: inserted={inserted}, updated={updated}, total={len(rows)}")


if __name__ == "__main__":
    main()
