"""Lightweight regression checks for Bili-Insight sentiment rules.

This intentionally uses a neutral stub instead of loading Transformer models,
so it can run quickly in local/dev environments and still catch rule regressions.
"""
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.aspect_analyzer import AspectAnalyzer  # noqa: E402
from app.services.domain_rules import DomainRuleEngine  # noqa: E402
from app.services.text_normalizer import TextNormalizer  # noqa: E402


class RuleOnlySentimentAnalyzer:
    def __init__(self):
        self.normalizer = TextNormalizer()
        self.rule_engine = DomainRuleEngine()

    def analyze(self, text: str, text_type: str = "comment") -> dict:
        normalized = self.normalizer.normalize(text, text_type)
        baseline = {
            "label": "NEUTRAL",
            "score": 0.0,
            "confidence": 0.42,
            "source": "rule_regression_stub",
            "version": "rule-regression",
            "raw_probs": {},
            "normalized_text": normalized.normalized_text,
        }
        return self.rule_engine.apply(baseline, normalized, text_type=text_type)

    def analyze_aspect(self, aspect: str, text: str, text_type: str = "comment") -> dict:
        return self.analyze(text, text_type=text_type)


def assert_sentiment(analyzer: RuleOnlySentimentAnalyzer, text: str, expected: str, text_type: str = "comment"):
    result = analyzer.analyze(text, text_type=text_type)
    actual = result["label"]
    if actual != expected:
        raise AssertionError(f"{text!r}: expected {expected}, got {actual}, result={result}")


def assert_aspect(aspect_analyzer: AspectAnalyzer, text: str, aspect: str, expected: str):
    details = aspect_analyzer.analyze(text, text_type="comment")
    by_aspect = {item["aspect"]: item for item in details}
    if aspect not in by_aspect:
        raise AssertionError(f"{text!r}: missing aspect {aspect}, details={details}")
    actual = by_aspect[aspect]["label"]
    if actual != expected:
        raise AssertionError(f"{text!r}: aspect {aspect} expected {expected}, got {actual}, details={details}")


def main():
    analyzer = RuleOnlySentimentAnalyzer()
    aspect_analyzer = AspectAnalyzer(analyzer)

    sentiment_cases = [
        ("这期剪辑封神，节奏太舒服了", "POSITIVE", "comment"),
        ("前面还行但是后面太水了", "NEGATIVE", "comment"),
        ("不是不好看，挺有东西的", "POSITIVE", "comment"),
        ("前排打卡", "NEUTRAL", "danmaku"),
        ("就这也叫专业？", "NEGATIVE", "comment"),
        ("价格不贵，续航也不差", "POSITIVE", "comment"),
    ]
    for text, expected, text_type in sentiment_cases:
        assert_sentiment(analyzer, text, expected, text_type=text_type)

    aspect_cases = [
        ("画面很清晰，但是价格太贵了", "画面", "POSITIVE"),
        ("画面很清晰，但是价格太贵了", "价格", "NEGATIVE"),
        ("剪辑节奏拖沓，不过配乐挺舒服", "剪辑", "NEGATIVE"),
        ("剪辑节奏拖沓，不过配乐挺舒服", "配乐", "POSITIVE"),
        ("这个视频标题党，内容还行", "标题封面", "NEGATIVE"),
    ]
    for text, aspect, expected in aspect_cases:
        assert_aspect(aspect_analyzer, text, aspect, expected)

    print("sentiment rule regression passed")


if __name__ == "__main__":
    main()
