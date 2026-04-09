import importlib.util
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_module(relative_path: str, module_name: str):
    module_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


import_annotation_csv = load_module(
    "python_service/scripts/eval/import_annotation_csv.py",
    "import_annotation_csv",
)
prepare_weak_supervision_dataset = load_module(
    "python_service/scripts/eval/prepare_weak_supervision_dataset.py",
    "prepare_weak_supervision_dataset",
)


class ImportAnnotationCsvTests(unittest.TestCase):
    def test_rejects_ai_prelabeled_rows_without_human_annotator(self):
        row = {
            "source_table": "video_comment",
            "source_id": "123",
            "task_id": "task-1",
            "bvid": "BV1xx411c7mD",
            "text_type": "comment",
            "raw_text": "这也太好看了",
            "gold_label": "POSITIVE",
            "annotator": "ai_prelabel_v1",
        }

        with self.assertRaisesRegex(ValueError, "annotator"):
            import_annotation_csv.normalize_row(row, 2)

    def test_accepts_human_annotated_rows(self):
        row = {
            "source_table": "video_comment",
            "source_id": "123",
            "task_id": "task-1",
            "bvid": "BV1xx411c7mD",
            "text_type": "comment",
            "raw_text": "这也太好看了",
            "gold_label": "POSITIVE",
            "annotator": "reviewer_alice",
        }

        normalized = import_annotation_csv.normalize_row(row, 2)

        self.assertEqual(normalized["gold_label"], "POSITIVE")
        self.assertEqual(normalized["annotator"], "reviewer_alice")


class PrepareWeakSupervisionDatasetTests(unittest.TestCase):
    def test_partition_rows_keeps_comment_and_danmaku_with_same_source_id_separate(self):
        rows = [
            {
                "source_table": "video_comment",
                "source_id": "42",
                "text_type": "comment",
                "raw_text": "这也太水了",
                "gold_label": "NEGATIVE",
                "notes": "review_priority=HIGH; ai_confidence=0.41",
            },
            {
                "source_table": "video_danmaku",
                "source_id": "42",
                "text_type": "danmaku",
                "raw_text": "好耶",
                "gold_label": "POSITIVE",
                "notes": "review_priority=LOW; ai_confidence=0.96",
            },
        ]

        review_subset, pseudo_train, holdout_uncertain = prepare_weak_supervision_dataset.partition_rows(
            rows,
            review_size=1,
            pseudo_min_confidence=0.8,
            pseudo_max_per_label=80,
        )

        self.assertEqual(len(review_subset), 1)
        self.assertEqual(review_subset[0]["source_table"], "video_comment")
        self.assertEqual(len(pseudo_train), 1)
        self.assertEqual(pseudo_train[0]["source_table"], "video_danmaku")
        self.assertEqual(holdout_uncertain, [])


class TrainSentimentModelScriptTests(unittest.TestCase):
    def test_help_does_not_require_training_dependencies(self):
        script_path = ROOT / "python_service" / "scripts" / "eval" / "train_sentiment_model.py"

        result = subprocess.run(
            [sys.executable, str(script_path), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("Fine-tune sentiment model", result.stdout)


class WeakSupervisionPathTests(unittest.TestCase):
    def test_default_output_dir_is_script_relative(self):
        output_dir = prepare_weak_supervision_dataset.default_output_dir()

        self.assertEqual(
            output_dir,
            ROOT / "python_service" / "scripts" / "eval" / "weak_supervision",
        )


if __name__ == "__main__":
    unittest.main()
