#!/usr/bin/env python3
"""Prepare low-effort review and pseudo-label datasets.

Use this after prelabel_annotation_csv.py. It splits AI-prelabeled rows into:

- review_subset: high-value rows for limited human review.
- pseudo_train: high-confidence pseudo-label rows for weak-supervised training.
- holdout_uncertain: rows that should not be used until reviewed.

Pseudo labels are not a substitute for a gold evaluation set; use the reviewed
subset for calibration/evaluation and pseudo_train only for extra training data.
"""
import argparse
import csv
from pathlib import Path
from typing import Dict, List


FIELDNAMES = [
    "source_table", "source_id", "task_id", "bvid", "text_type",
    "raw_text", "normalized_text",
    "model_label", "model_score", "model_confidence",
    "gold_label", "gold_intensity", "gold_emotion_tags", "gold_aspect_details",
    "annotator", "notes",
]


def default_output_dir() -> Path:
    return Path(__file__).resolve().parent / "weak_supervision"


def row_identity(row: Dict) -> tuple:
    return (
        (row.get("source_table") or "").strip(),
        str(row.get("source_id") or "").strip(),
        (row.get("text_type") or "").strip(),
    )


def parse_note_value(notes: str, key: str, default: str = "") -> str:
    token = f"{key}="
    if token not in notes:
        return default
    return notes.split(token, 1)[1].split(";", 1)[0].strip()


def parse_float(value: str, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def review_score(row: Dict) -> float:
    notes = row.get("notes", "")
    priority = parse_note_value(notes, "review_priority", "LOW")
    confidence = parse_float(parse_note_value(notes, "ai_confidence", row.get("model_confidence", "")), 0.0)
    label = (row.get("gold_label") or "").strip()
    disagreed = "previous_model_disagreed=true" in notes
    has_aspect = bool((row.get("gold_aspect_details") or "").strip())

    score = 0.0
    score += {"HIGH": 4.0, "MEDIUM": 2.0, "LOW": 0.0}.get(priority, 0.0)
    score += max(0.0, 0.75 - confidence) * 4
    if disagreed:
        score += 1.6
    if label == "NEGATIVE":
        score += 1.8
    if has_aspect:
        score += 1.2
    if len(row.get("raw_text") or "") <= 8:
        score += 0.5
    return round(score, 4)


def is_pseudo_train_candidate(row: Dict, min_confidence: float) -> bool:
    notes = row.get("notes", "")
    confidence = parse_float(parse_note_value(notes, "ai_confidence", row.get("model_confidence", "")), 0.0)
    priority = parse_note_value(notes, "review_priority", "HIGH")
    label = (row.get("gold_label") or "").strip()
    if not label:
        return False
    if priority == "HIGH":
        return False
    if "previous_model_disagreed=true" in notes and confidence < 0.85:
        return False
    return confidence >= min_confidence


def load_rows(path: Path) -> List[Dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path: Path, rows: List[Dict]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def balance_by_label(rows: List[Dict], max_per_label: int) -> List[Dict]:
    if max_per_label <= 0:
        return rows
    grouped = {}
    for row in rows:
        grouped.setdefault((row.get("gold_label") or "").strip(), []).append(row)
    balanced = []
    for label_rows in grouped.values():
        label_rows.sort(key=lambda row: parse_float(parse_note_value(row.get("notes", ""), "ai_confidence"), 0.0), reverse=True)
        balanced.extend(label_rows[:max_per_label])
    balanced.sort(key=lambda row: parse_float(parse_note_value(row.get("notes", ""), "ai_confidence"), 0.0), reverse=True)
    return balanced


def stratified_review_subset(rows: List[Dict], review_size: int) -> List[Dict]:
    label_targets = {
        "NEGATIVE": max(20, int(review_size * 0.25)),
        "NEUTRAL": int(review_size * 0.40),
        "POSITIVE": int(review_size * 0.35),
    }
    selected = []
    selected_ids = set()
    for label, target in label_targets.items():
        candidates = [row for row in rows if (row.get("gold_label") or "").strip() == label]
        candidates.sort(key=review_score, reverse=True)
        for row in candidates[:target]:
            selected.append(row)
            selected_ids.add(row_identity(row))

    if len(selected) < review_size:
        rest = [row for row in rows if row_identity(row) not in selected_ids]
        rest.sort(key=review_score, reverse=True)
        selected.extend(rest[:review_size - len(selected)])

    selected = selected[:review_size]
    selected.sort(key=review_score, reverse=True)
    for row in selected:
        notes = row.get("notes") or ""
        row["notes"] = f"{notes}; selected_for_minimal_review=true; active_review_score={review_score(row)}"
    return selected


def partition_rows(
    rows: List[Dict],
    review_size: int,
    pseudo_min_confidence: float,
    pseudo_max_per_label: int,
):
    review_subset = stratified_review_subset(rows, review_size)
    review_keys = {row_identity(row) for row in review_subset}
    pseudo_train = [
        row for row in rows
        if row_identity(row) not in review_keys and is_pseudo_train_candidate(row, pseudo_min_confidence)
    ]
    pseudo_train = balance_by_label(pseudo_train, pseudo_max_per_label)
    pseudo_keys = {row_identity(row) for row in pseudo_train}
    holdout_uncertain = [
        row for row in rows
        if row_identity(row) not in review_keys and row_identity(row) not in pseudo_keys
    ]
    return review_subset, pseudo_train, holdout_uncertain


def main():
    parser = argparse.ArgumentParser(description="Prepare weak-supervision datasets")
    parser.add_argument("prelabeled_csv", type=Path)
    parser.add_argument("--output-dir", type=Path, default=default_output_dir())
    parser.add_argument("--review-size", type=int, default=180)
    parser.add_argument("--pseudo-min-confidence", type=float, default=0.80)
    parser.add_argument("--pseudo-max-per-label", type=int, default=80)
    args = parser.parse_args()

    rows = load_rows(args.prelabeled_csv)
    if not rows:
        print("[WARN] empty input")
        return

    review_subset, pseudo_train, holdout_uncertain = partition_rows(
        rows,
        review_size=args.review_size,
        pseudo_min_confidence=args.pseudo_min_confidence,
        pseudo_max_per_label=args.pseudo_max_per_label,
    )

    write_rows(args.output_dir / "review_subset.csv", review_subset)
    write_rows(args.output_dir / "pseudo_train.csv", pseudo_train)
    write_rows(args.output_dir / "holdout_uncertain.csv", holdout_uncertain)

    label_counts = {}
    for row in review_subset:
        label = row.get("gold_label") or ""
        label_counts[label] = label_counts.get(label, 0) + 1
    pseudo_counts = {}
    for row in pseudo_train:
        label = row.get("gold_label") or ""
        pseudo_counts[label] = pseudo_counts.get(label, 0) + 1

    print("[INFO] weak-supervision split generated")
    print(f"  review_subset={len(review_subset)} labels={label_counts}")
    print(f"  pseudo_train={len(pseudo_train)} labels={pseudo_counts}")
    print(f"  holdout_uncertain={len(holdout_uncertain)}")
    print(f"  output_dir={args.output_dir}")


if __name__ == "__main__":
    main()
