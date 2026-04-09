#!/usr/bin/env python3
"""Fine-tune a 3-class sentiment model from labeled Bili-Insight annotations."""
import argparse
import csv
import os
import random
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

LABEL_TO_ID = {"NEGATIVE": 0, "NEUTRAL": 1, "POSITIVE": 2}
ID_TO_LABEL = {v: k for k, v in LABEL_TO_ID.items()}


def load_training_dependencies():
    try:
        import torch
        from torch.utils.data import Dataset
        from transformers import (
            AutoModelForSequenceClassification,
            AutoTokenizer,
            Trainer,
            TrainingArguments,
        )
    except ImportError as exc:
        raise RuntimeError(
            "缺少训练依赖，请先在 python_service 环境中安装 torch 和 transformers 相关依赖"
        ) from exc

    return {
        "torch": torch,
        "Dataset": Dataset,
        "AutoModelForSequenceClassification": AutoModelForSequenceClassification,
        "AutoTokenizer": AutoTokenizer,
        "Trainer": Trainer,
        "TrainingArguments": TrainingArguments,
    }


def get_db_config():
    return {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", 3306)),
        "user": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASSWORD", ""),
        "database": os.getenv("DB_NAME", "bili_insight_db"),
        "charset": "utf8mb4",
    }


def load_rows_from_db(text_type: Optional[str] = None):
    where = "WHERE raw_text IS NOT NULL AND gold_label IN ('POSITIVE','NEUTRAL','NEGATIVE')"
    params = []
    if text_type:
        where += " AND text_type = %s"
        params.append(text_type)
    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT raw_text, text_type, gold_label FROM sentiment_annotation {where}", params)
            return cursor.fetchall()
    finally:
        conn.close()


def load_rows_from_csv(csv_path: Path, text_type: Optional[str] = None):
    rows = []
    with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            gold = (row.get("gold_label") or "").strip().upper()
            row_type = (row.get("text_type") or "comment").strip()
            if gold not in LABEL_TO_ID:
                continue
            if text_type and row_type != text_type:
                continue
            rows.append({
                "raw_text": row.get("raw_text") or "",
                "text_type": row_type,
                "gold_label": gold,
            })
    return rows


def build_dataset_class(torch_module, dataset_base):
    class SentimentDataset(dataset_base):
        def __init__(self, rows, tokenizer, max_length: int):
            self.rows = rows
            self.tokenizer = tokenizer
            self.max_length = max_length

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, idx):
            row = self.rows[idx]
            encoding = self.tokenizer(
                row["raw_text"],
                truncation=True,
                max_length=self.max_length,
                padding="max_length",
                return_tensors="pt",
            )
            item = {key: value.squeeze(0) for key, value in encoding.items()}
            item["labels"] = torch_module.tensor(LABEL_TO_ID[row["gold_label"]], dtype=torch_module.long)
            return item

    return SentimentDataset


def split_rows(rows, eval_ratio: float, seed: int):
    random.Random(seed).shuffle(rows)
    split_at = max(1, int(len(rows) * (1 - eval_ratio)))
    if split_at >= len(rows):
        split_at = len(rows) - 1
    return rows[:split_at], rows[split_at:]


def main():
    parser = argparse.ArgumentParser(description="Fine-tune sentiment model")
    parser.add_argument("--csv", type=Path, default=None, help="Use labeled CSV instead of DB table")
    parser.add_argument("--text-type", choices=["comment", "danmaku"], default="comment")
    parser.add_argument("--base-model", default=os.getenv("SENTIMENT_BASE_MODEL", "H-Z-Ning/Senti-RoBERTa-Mini"))
    parser.add_argument("--output-dir", type=Path, default=Path("models/comment-sentiment-v1"))
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--max-length", type=int, default=160)
    parser.add_argument("--eval-ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--min-samples", type=int, default=200)
    args = parser.parse_args()

    rows = load_rows_from_csv(args.csv, args.text_type) if args.csv else load_rows_from_db(args.text_type)
    if len(rows) < args.min_samples:
        print(f"[WARN] 标注样本不足: {len(rows)} < {args.min_samples}，先不要微调")
        return

    deps = load_training_dependencies()
    SentimentDataset = build_dataset_class(deps["torch"], deps["Dataset"])

    counts = {}
    for row in rows:
        counts[row["gold_label"]] = counts.get(row["gold_label"], 0) + 1
    print(f"[INFO] 加载样本 {len(rows)} 条: {counts}")

    train_rows, eval_rows = split_rows(rows, args.eval_ratio, args.seed)
    tokenizer = deps["AutoTokenizer"].from_pretrained(args.base_model)
    model = deps["AutoModelForSequenceClassification"].from_pretrained(
        args.base_model,
        num_labels=3,
        id2label=ID_TO_LABEL,
        label2id=LABEL_TO_ID,
        ignore_mismatched_sizes=True,
    )

    training_args = deps["TrainingArguments"](
        output_dir=str(args.output_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        logging_steps=20,
        seed=args.seed,
    )
    trainer = deps["Trainer"](
        model=model,
        args=training_args,
        train_dataset=SentimentDataset(train_rows, tokenizer, args.max_length),
        eval_dataset=SentimentDataset(eval_rows, tokenizer, args.max_length),
    )
    trainer.train()
    trainer.save_model(str(args.output_dir))
    tokenizer.save_pretrained(str(args.output_dir))

    print("[INFO] 微调完成")
    print(f"[INFO] 模型输出目录: {args.output_dir}")
    if args.text_type == "danmaku":
        print(f"DANMAKU_MODEL={args.output_dir}")
        print("DANMAKU_MODEL_LABEL_SCHEME=three_class")
    else:
        print(f"COMMENT_MODEL={args.output_dir}")
        print("COMMENT_MODEL_LABEL_SCHEME=three_class")


if __name__ == "__main__":
    main()
