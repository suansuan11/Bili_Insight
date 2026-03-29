#!/usr/bin/env python3
"""
离线情感评估脚本
读取 sentiment_annotation 人工标注表，对新模型预测结果进行评估

用法:
    python run_sentiment_eval.py
    python run_sentiment_eval.py --text-type comment --output-dir reports/
"""
import sys
import os
import argparse
import json
from datetime import datetime
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pymysql
from pymysql.cursors import DictCursor
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        classification_report
    )
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False
    print("[WARN] scikit-learn 未安装，部分评估指标不可用")


def get_db_config():
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', 3306)),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', ''),
        'database': os.getenv('DB_NAME', 'bili_insight_db'),
        'charset': 'utf8mb4',
    }


def load_annotations(cursor, text_type=None):
    """从 sentiment_annotation 加载人工标注"""
    where = "WHERE raw_text IS NOT NULL"
    params = []
    if text_type:
        where += " AND text_type = %s"
        params.append(text_type)

    cursor.execute(
        f"SELECT * FROM sentiment_annotation {where} ORDER BY id",
        params
    )
    return cursor.fetchall()


def predict_batch(annotations):
    """调用新模型对标注集重新预测"""
    # 动态导入，避免在无环境时 crash
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))
    try:
        from app.services.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
    except Exception as e:
        print(f"[ERROR] 无法加载 SentimentAnalyzer: {e}")
        return []

    results = []
    total = len(annotations)
    for i, ann in enumerate(annotations):
        text = ann.get('raw_text', '')
        text_type = ann.get('text_type', 'comment')
        try:
            pred = analyzer.analyze(text, text_type=text_type)
        except Exception as e:
            pred = {'label': 'NEUTRAL', 'confidence': 0.0}
        results.append(pred)
        if (i + 1) % 50 == 0:
            print(f"[INFO] 预测进度: {i + 1}/{total}")

    return results


def evaluate(annotations, predictions):
    """计算评估指标"""
    gold_labels = [ann['gold_label'] for ann in annotations]
    pred_labels = [p.get('label', 'NEUTRAL') for p in predictions]

    metrics = {}

    if _SKLEARN_AVAILABLE:
        labels = ['POSITIVE', 'NEUTRAL', 'NEGATIVE']
        metrics['accuracy'] = accuracy_score(gold_labels, pred_labels)
        metrics['precision_macro'] = precision_score(gold_labels, pred_labels, labels=labels, average='macro', zero_division=0)
        metrics['recall_macro'] = recall_score(gold_labels, pred_labels, labels=labels, average='macro', zero_division=0)
        metrics['f1_macro'] = f1_score(gold_labels, pred_labels, labels=labels, average='macro', zero_division=0)
        metrics['negative_recall'] = recall_score(
            [1 if l == 'NEGATIVE' else 0 for l in gold_labels],
            [1 if l == 'NEGATIVE' else 0 for l in pred_labels],
            zero_division=0
        )
        metrics['report'] = classification_report(
            gold_labels, pred_labels, labels=labels, zero_division=0
        )
    else:
        # 简单手算 accuracy
        correct = sum(1 for g, p in zip(gold_labels, pred_labels) if g == p)
        metrics['accuracy'] = correct / len(gold_labels) if gold_labels else 0

    # 按 text_type 分组统计
    type_groups = defaultdict(lambda: {'gold': [], 'pred': []})
    for ann, pred in zip(annotations, predictions):
        t = ann.get('text_type', 'unknown')
        type_groups[t]['gold'].append(ann['gold_label'])
        type_groups[t]['pred'].append(pred.get('label', 'NEUTRAL'))

    metrics['by_type'] = {}
    for t, data in type_groups.items():
        if _SKLEARN_AVAILABLE:
            acc = accuracy_score(data['gold'], data['pred'])
        else:
            acc = sum(1 for g, p in zip(data['gold'], data['pred']) if g == p) / max(len(data['gold']), 1)
        metrics['by_type'][t] = {
            'count': len(data['gold']),
            'accuracy': round(acc, 4)
        }

    return metrics


def print_summary(metrics, total):
    print("\n" + "=" * 60)
    print(f"情感分析离线评估报告 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    print("=" * 60)
    print(f"标注样本总数: {total}")
    print(f"Accuracy:       {metrics.get('accuracy', 0):.4f}")
    print(f"Precision(mac): {metrics.get('precision_macro', 'N/A')}")
    print(f"Recall(macro):  {metrics.get('recall_macro', 'N/A')}")
    print(f"F1(macro):      {metrics.get('f1_macro', 'N/A')}")
    print(f"Neg Recall:     {metrics.get('negative_recall', 'N/A')}")
    print("\n--- 按文本类型分组 ---")
    for t, v in metrics.get('by_type', {}).items():
        print(f"  {t}: count={v['count']}, accuracy={v['accuracy']:.4f}")
    if 'report' in metrics:
        print("\n--- Classification Report ---")
        print(metrics['report'])
    print("=" * 60)


def save_results(metrics, output_dir, total):
    os.makedirs(output_dir, exist_ok=True)
    date_str = datetime.now().strftime('%Y%m%d_%H%M%S')

    # JSON
    json_path = os.path.join(output_dir, f"sentiment_eval_{date_str}.json")
    out = {k: v for k, v in metrics.items() if k != 'report'}
    out['total'] = total
    out['evaluated_at'] = datetime.now().isoformat()
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    # Markdown
    md_path = os.path.join(output_dir, f"sentiment_eval_{date_str}.md")
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# 情感分析离线评估报告\n\n")
        f.write(f"评估时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(f"| 指标 | 值 |\n|---|---|\n")
        f.write(f"| 样本总数 | {total} |\n")
        f.write(f"| Accuracy | {metrics.get('accuracy', 0):.4f} |\n")
        if 'f1_macro' in metrics:
            f.write(f"| F1 (macro) | {metrics['f1_macro']:.4f} |\n")
        if 'negative_recall' in metrics:
            f.write(f"| 负面 Recall | {metrics['negative_recall']:.4f} |\n")
        f.write("\n## 按文本类型分组\n\n")
        f.write("| 类型 | 数量 | Accuracy |\n|---|---|---|\n")
        for t, v in metrics.get('by_type', {}).items():
            f.write(f"| {t} | {v['count']} | {v['accuracy']:.4f} |\n")
        if 'report' in metrics:
            f.write(f"\n## 详细报告\n\n```\n{metrics['report']}\n```\n")

    print(f"\n[INFO] 评估结果已保存:\n  JSON: {json_path}\n  MD:   {md_path}")


def main():
    parser = argparse.ArgumentParser(description='情感分析离线评估')
    parser.add_argument('--text-type', type=str, default=None, choices=['comment', 'danmaku'])
    parser.add_argument('--output-dir', type=str, default='reports')
    args = parser.parse_args()

    conn = pymysql.connect(**get_db_config(), cursorclass=DictCursor)
    try:
        with conn.cursor() as cursor:
            annotations = load_annotations(cursor, args.text_type)
    finally:
        conn.close()

    if not annotations:
        print("[WARN] sentiment_annotation 表中暂无标注数据，请先运行 build_annotation_dataset.py 并完成人工标注")
        return

    print(f"[INFO] 读取标注样本: {len(annotations)} 条")
    predictions = predict_batch(annotations)

    if len(predictions) != len(annotations):
        print(f"[ERROR] 预测数量({len(predictions)})与标注数量({len(annotations)})不匹配")
        return

    metrics = evaluate(annotations, predictions)
    print_summary(metrics, len(annotations))
    save_results(metrics, args.output_dir, len(annotations))


if __name__ == '__main__':
    main()
