#!/usr/bin/env python3
"""Calibrate score thresholds on a labeled sentiment validation set.

The script predicts each labeled sample once, then grid-searches positive and
negative score cutoffs. It optimizes macro-F1 while optionally enforcing a
minimum negative recall, which is important for public-opinion alerting.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

try:
    from sklearn.metrics import accuracy_score, f1_score, recall_score
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False

LABELS = ["POSITIVE", "NEUTRAL", "NEGATIVE"]


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "bili_insight_db"),
        "charset": "utf8mb4",
    }


def load_annotations_from_db(text_type: Optional[str] = None):
    where = "WHERE raw_text IS NOT NULL AND gold_label IN ('POSITIVE','NEUTRAL','NEGATIVE')"
    params = []
    if text_type:
        where += " AND text_type = %s"
        params.append(text_type)
    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT * FROM sentiment_annotation {where} ORDER BY id", params)
            return cursor.fetchall()
    finally:
        conn.close()


def load_annotations_from_csv(csv_path: Path, text_type: Optional[str] = None):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gold = (row.get("gold_label") or "").strip().upper()
            row_type = (row.get("text_type") or "comment").strip()
            if gold not in LABELS:
                continue
            if text_type and row_type != text_type:
                continue
            rows.append({
                "raw_text": row.get("raw_text") or "",
                "text_type": row_type,
                "gold_label": gold,
            })
    return rows


def predict_scores(annotations):
    from app.services.sentiment_analyzer import SentimentAnalyzer

    analyzer = SentimentAnalyzer()
    rows = []
    total = len(annotations)
    for idx, ann in enumerate(annotations, start=1):
        text = ann.get("raw_text") or ""
        text_type = ann.get("text_type") or "comment"
        pred = analyzer.analyze(text, text_type=text_type)
        rows.append({
            "text": text,
            "text_type": text_type,
            "gold_label": ann["gold_label"],
            "default_label": pred.get("label", "NEUTRAL"),
            "score": float(pred.get("score") or 0.0),
            "confidence": float(pred.get("confidence") or 0.0),
        })
        if idx % 50 == 0:
            print(f"[INFO] 预测进度: {idx}/{total}")
    return rows


def frange(start: float, stop: float, step: float) -> Iterable[float]:
    value = start
    while value <= stop + 1e-9:
        yield round(value, 4)
        value += step


def label_by_threshold(score: float, positive_threshold: float, negative_threshold: float) -> str:
    if score >= positive_threshold:
        return "POSITIVE"
    if score <= negative_threshold:
        return "NEGATIVE"
    return "NEUTRAL"


def metric_bundle(gold: List[str], pred: List[str]):
    if _SKLEARN_AVAILABLE:
        return {
            "accuracy": accuracy_score(gold, pred),
            "macro_f1": f1_score(gold, pred, labels=LABELS, average="macro", zero_division=0),
            "negative_recall": recall_score(
                [1 if x == "NEGATIVE" else 0 for x in gold],
                [1 if x == "NEGATIVE" else 0 for x in pred],
                zero_division=0,
            ),
        }
    correct = sum(1 for g, p in zip(gold, pred) if g == p)
    return {
        "accuracy": correct / max(len(gold), 1),
        "macro_f1": correct / max(len(gold), 1),
        "negative_recall": 0.0,
    }


def calibrate(rows, min_negative_recall: float):
    gold = [row["gold_label"] for row in rows]
    default_pred = [row["default_label"] for row in rows]
    default_metrics = metric_bundle(gold, default_pred)

    candidates = []
    for pos_t in frange(0.10, 0.36, 0.02):
        for neg_t in frange(-0.36, -0.10, 0.02):
            pred = [label_by_threshold(row["score"], pos_t, neg_t) for row in rows]
            metrics = metric_bundle(gold, pred)
            if metrics["negative_recall"] < min_negative_recall:
                continue
            candidates.append({
                "positive_threshold": pos_t,
                "negative_threshold": neg_t,
                **metrics,
            })

    if not candidates:
        candidates = [{
            "positive_threshold": 0.22,
            "negative_threshold": -0.22,
            **default_metrics,
            "fallback": "no candidate satisfied min_negative_recall",
        }]

    best = max(candidates, key=lambda item: (item["macro_f1"], item["negative_recall"], item["accuracy"]))
    return default_metrics, best, sorted(
        candidates,
        key=lambda item: (item["macro_f1"], item["negative_recall"], item["accuracy"]),
        reverse=True,
    )[:10]


def save_report(output_dir: Path, total: int, default_metrics: dict, best: dict, top10: list):
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report = {
        "total": total,
        "default_metrics": default_metrics,
        "best": best,
        "top10": top10,
        "env": {
            "SENTIMENT_SCORE_POSITIVE_THRESHOLD": best["positive_threshold"],
            "SENTIMENT_SCORE_NEGATIVE_THRESHOLD": best["negative_threshold"],
        },
    }
    json_path = output_dir / f"sentiment_threshold_calibration_{stamp}.json"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path = output_dir / f"sentiment_threshold_calibration_{stamp}.md"
    md_path.write_text(
        "\n".join([
            "# 情感阈值标定报告",
            "",
            f"样本数: {total}",
            "",
            "## 当前默认结果",
            f"- accuracy: {default_metrics['accuracy']:.4f}",
            f"- macro_f1: {default_metrics['macro_f1']:.4f}",
            f"- negative_recall: {default_metrics['negative_recall']:.4f}",
            "",
            "## 推荐阈值",
            f"- SENTIMENT_SCORE_POSITIVE_THRESHOLD={best['positive_threshold']}",
            f"- SENTIMENT_SCORE_NEGATIVE_THRESHOLD={best['negative_threshold']}",
            f"- accuracy: {best['accuracy']:.4f}",
            f"- macro_f1: {best['macro_f1']:.4f}",
            f"- negative_recall: {best['negative_recall']:.4f}",
            "",
        ]),
        encoding="utf-8",
    )
    print(f"[INFO] 标定报告已保存:\n  JSON: {json_path}\n  MD:   {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Calibrate sentiment score thresholds")
    parser.add_argument("--csv", type=Path, default=None, help="Use labeled CSV instead of DB table")
    parser.add_argument("--text-type", choices=["comment", "danmaku"], default=None)
    parser.add_argument("--min-negative-recall", type=float, default=0.0)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args()

    annotations = (
        load_annotations_from_csv(args.csv, args.text_type)
        if args.csv else
        load_annotations_from_db(args.text_type)
    )
    if not annotations:
        print("[WARN] 没有可用于标定的 gold_label 样本")
        return
    print(f"[INFO] 读取标注样本: {len(annotations)}")
    rows = predict_scores(annotations)
    default_metrics, best, top10 = calibrate(rows, args.min_negative_recall)
    print("[INFO] 当前默认:", default_metrics)
    print("[INFO] 推荐阈值:", best)
    save_report(args.output_dir, len(rows), default_metrics, best, top10)


if __name__ == "__main__":
    main()
