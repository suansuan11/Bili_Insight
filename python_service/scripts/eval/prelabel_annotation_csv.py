#!/usr/bin/env python3
"""Pre-label annotation CSV rows with the current sentiment pipeline.

The output is for human review. It fills gold_* columns so reviewers can correct
labels instead of starting from blank cells, and marks annotator as ai_prelabel.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from app.services.aspect_analyzer import AspectAnalyzer
from app.services.sentiment_analyzer import SentimentAnalyzer


FIELDNAMES = [
    "source_table", "source_id", "task_id", "bvid", "text_type",
    "raw_text", "normalized_text",
    "model_label", "model_score", "model_confidence",
    "gold_label", "gold_intensity", "gold_emotion_tags", "gold_aspect_details",
    "annotator", "notes",
]


def confidence_bucket(confidence: float) -> str:
    if confidence < 0.45:
        return "HIGH"
    if confidence < 0.65:
        return "MEDIUM"
    return "LOW"


def should_prelabeled(row: dict, overwrite_existing: bool) -> bool:
    return overwrite_existing or not (row.get("gold_label") or "").strip()


def prelabel_row(row: dict, sentiment_analyzer: SentimentAnalyzer, aspect_analyzer: AspectAnalyzer, include_aspects: bool, overwrite_existing: bool):
    if not should_prelabeled(row, overwrite_existing):
        return row

    text = row.get("raw_text") or ""
    text_type = row.get("text_type") or "comment"
    sentiment = sentiment_analyzer.analyze(text, text_type=text_type)

    row["gold_label"] = sentiment.get("label", "NEUTRAL")
    row["gold_intensity"] = sentiment.get("intensity", "WEAK")
    row["gold_emotion_tags"] = json.dumps(sentiment.get("emotion_tags", []), ensure_ascii=False)
    row["normalized_text"] = sentiment.get("normalized_text") or row.get("normalized_text") or ""

    aspect_details = []
    if include_aspects and text_type == "comment":
        aspect_details = aspect_analyzer.analyze(text, text_type=text_type)
    row["gold_aspect_details"] = json.dumps(aspect_details, ensure_ascii=False) if aspect_details else ""

    confidence = float(sentiment.get("confidence") or 0.0)
    previous_label = (row.get("model_label") or "").strip()
    disagreed = bool(previous_label and previous_label != row["gold_label"])
    review_priority = confidence_bucket(confidence)
    if disagreed and review_priority == "LOW":
        review_priority = "MEDIUM"

    note_parts = []
    existing_notes = (row.get("notes") or "").strip()
    if existing_notes:
        note_parts.append(existing_notes)
    note_parts.extend([
        "AI_PRELABEL_NEEDS_HUMAN_REVIEW",
        f"review_priority={review_priority}",
        f"ai_confidence={confidence:.4f}",
        f"ai_score={float(sentiment.get('score') or 0.0):.4f}",
        f"ai_source={sentiment.get('source', '')}",
    ])
    if previous_label:
        note_parts.append(f"previous_model_label={previous_label}")
    if disagreed:
        note_parts.append("previous_model_disagreed=true")
    row["annotator"] = "ai_prelabel_v1"
    row["notes"] = "; ".join(note_parts)
    return row


def main():
    parser = argparse.ArgumentParser(description="Pre-label annotation CSV for human review")
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--overwrite-existing", action="store_true")
    parser.add_argument("--no-aspects", action="store_true", help="Skip gold_aspect_details pre-labeling")
    parser.add_argument("--limit", type=int, default=None, help="Only prelabel first N rows; useful for smoke tests")
    args = parser.parse_args()

    output = args.output
    if output is None:
        output = args.input_csv.with_name(f"{args.input_csv.stem}_prelabeled.csv")

    sentiment_analyzer = SentimentAnalyzer()
    aspect_analyzer = AspectAnalyzer(sentiment_analyzer)

    rows = []
    with args.input_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for index, row in enumerate(reader, start=1):
            for field in FIELDNAMES:
                row.setdefault(field, "")
            if args.limit is None or index <= args.limit:
                row = prelabel_row(
                    row,
                    sentiment_analyzer,
                    aspect_analyzer,
                    include_aspects=not args.no_aspects,
                    overwrite_existing=args.overwrite_existing,
                )
            rows.append(row)
            if index % 50 == 0:
                print(f"[INFO] 预标注进度: {index}")

    with output.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

    labeled = sum(1 for row in rows if (row.get("gold_label") or "").strip())
    print(f"[INFO] 预标注完成: output={output}, rows={len(rows)}, labeled={labeled}, generated_at={datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
