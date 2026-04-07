"""
领域规则纠偏模块
对 Transformer 模型结果做微调和纠偏，不替代模型
"""
from typing import Dict, List, Tuple
from pathlib import Path
import math
import re

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from ..utils.logger import logger
from .text_normalizer import NormalizedText

# 词典文件路径
_LEXICON_PATH = Path(__file__).parent.parent / "resources" / "domain_lexicon.yml"

_LOW_CONFIDENCE_THRESHOLD = 0.68


class DomainRuleEngine:
    """
    B站领域规则纠偏引擎

    职责:
    1. 识别否定词反转（低置信度时）
    2. 识别常见反讽标记，补充 emotion_tags
    3. 强化高频网络语命中
    4. 生成 emotion_tags
    5. 对低置信度样本做小范围纠偏

    原则:
    - 仅在高确定性规则触发时改标签
    - 默认不推翻高置信度模型结果(>= 0.65)
    - 对中低置信度样本优先生效
    """

    def __init__(self):
        self._lexicon = self._load_lexicon()

    def _load_lexicon(self) -> dict:
        """加载领域词典"""
        if not _YAML_AVAILABLE:
            logger.warning("pyyaml 未安装，跳过领域词典加载，规则层将使用内置默认词典")
            return self._default_lexicon()

        if not _LEXICON_PATH.exists():
            logger.warning(f"领域词典文件不存在: {_LEXICON_PATH}，使用内置默认词典")
            return self._default_lexicon()

        try:
            with open(_LEXICON_PATH, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            logger.info(f"领域词典加载成功: {_LEXICON_PATH}")
            return data or self._default_lexicon()
        except Exception as e:
            logger.error(f"加载领域词典失败: {e}，使用内置默认词典")
            return self._default_lexicon()

    def _default_lexicon(self) -> dict:
        """内置默认词典（pyyaml 不可用时的兜底）"""
        return {
            "positive": ["真香", "神作", "牛", "好看", "厉害", "赞", "爱了", "顶"],
            "negative": ["逆天", "无语", "拉胯", "烂", "失望", "垃圾", "坑"],
            "sarcasm": ["笑死", "绝了", "你是懂", "太会了", "好家伙", "蚌埠住了", "麻了"],
            "neutral": ["前排", "打卡", "来了", "路过", "第一"],
            "strong_positive": ["封神", "吹爆", "入股不亏", "真香", "神作"],
            "strong_negative": ["避雷", "别买", "看不下去", "浪费时间", "一坨", "标题党"],
            "mild_positive": ["还行", "可以", "不差", "不亏", "没毛病"],
            "mild_negative": ["一般", "有点尬", "不太行", "不推荐"],
            "negation": ["不", "没", "无", "别", "非", "未"],
            "intensifiers": ["太", "巨", "非常", "真", "好", "超", "特别"],
        }

    def _find_hits(self, text: str, bucket: str) -> List[str]:
        words = self._lexicon.get(bucket, [])
        return [w for w in words if isinstance(w, str) and w and w in text]

    def _split_clauses(self, text: str) -> List[str]:
        clauses = re.split(r"[，,。！？!?；;]|但是|不过|然而|只是|就是|却|而是|但", text)
        return [clause.strip() for clause in clauses if clause and clause.strip()]

    def _window_has_any(self, text: str, index: int, candidates: List[str], backward: int = 4, forward: int = 1) -> bool:
        start = max(0, index - backward)
        end = min(len(text), index + forward)
        window = text[start:end]
        return any(isinstance(c, str) and c and c in window for c in candidates)

    def _negation_count_before(self, text: str, index: int, backward: int = 4) -> int:
        """统计情感词前短窗口内的否定强度，避免“不是不好看”被单次反转。"""
        prefix = text[max(0, index - backward):index]
        return sum(1 for ch in prefix if ch in {"不", "没", "无", "非", "未", "别"})

    def _score_hit(self, text: str, hit: str, base_sign: int) -> float:
        idx = text.find(hit)
        intensifiers = self._lexicon.get("intensifiers", [])

        score = 1.0 * base_sign
        if idx >= 0 and self._window_has_any(text, idx, intensifiers, backward=3, forward=0):
            score *= 1.35
        if idx >= 0 and self._negation_count_before(text, idx) % 2 == 1:
            score *= -1
        return score

    def _weighted_phrase_score(self, text: str, bucket: str, weight: float) -> Tuple[float, List[str]]:
        hits = self._find_hits(text, bucket)
        return len(hits) * weight, hits

    def _direct_signal_score(self, text: str, current_label: str) -> Tuple[float, Dict[str, List[str]]]:
        positive_hits = self._find_hits(text, "positive")
        negative_hits = self._find_hits(text, "negative")
        sarcasm_hits = self._find_hits(text, "sarcasm")
        neutral_hits = self._find_hits(text, "neutral")

        score = 0.0
        for hit in positive_hits:
            score += self._score_hit(text, hit, 1)
        for hit in negative_hits:
            score += self._score_hit(text, hit, -1)

        strong_pos_score, strong_positive_hits = self._weighted_phrase_score(text, "strong_positive", 1.35)
        strong_neg_score, strong_negative_hits = self._weighted_phrase_score(text, "strong_negative", -1.45)
        mild_pos_score, mild_positive_hits = self._weighted_phrase_score(text, "mild_positive", 0.55)
        mild_neg_score, mild_negative_hits = self._weighted_phrase_score(text, "mild_negative", -0.55)
        score += strong_pos_score + strong_neg_score + mild_pos_score + mild_neg_score

        # 反讽词默认偏负向，尤其配合问号或负面词时
        if sarcasm_hits:
            sarcasm_bias = -0.9 if ("？" in text or "?" in text or negative_hits) else -0.35
            if current_label == "POSITIVE" and positive_hits and not negative_hits:
                sarcasm_bias *= 0.5
            score += sarcasm_bias

        if "这也叫" in text or "就这" in text:
            score -= 1.25
            if "？" in text or "?" in text:
                score -= 0.45

        return score, {
            "positive": positive_hits,
            "negative": negative_hits,
            "sarcasm": sarcasm_hits,
            "neutral": neutral_hits,
            "strong_positive": strong_positive_hits,
            "strong_negative": strong_negative_hits,
            "mild_positive": mild_positive_hits,
            "mild_negative": mild_negative_hits,
        }

    def _merge_hits(self, base: Dict[str, List[str]], extra: Dict[str, List[str]]) -> Dict[str, List[str]]:
        for key, values in extra.items():
            merged = base.setdefault(key, [])
            for value in values:
                if value not in merged:
                    merged.append(value)
        return base

    def _contrast_tail(self, text: str) -> str:
        match = re.search(r"(?:但是|不过|然而|只是|却|但|可惜|问题是)([^，。！？!?；;]+)$", text)
        return match.group(1).strip() if match else ""

    def _lexicon_score(self, text: str, text_type: str, current_label: str) -> Tuple[float, Dict[str, List[str]]]:
        score, hits = self._direct_signal_score(text, current_label)

        tail = self._contrast_tail(text)
        if tail:
            tail_score, tail_hits = self._direct_signal_score(tail, current_label)
            if abs(tail_score) >= 0.4:
                # 转折后半句通常承载最终态度，增强 tail 权重。
                score = score * 0.65 + tail_score * 0.9
                self._merge_hits(hits, tail_hits)

        if text_type == "danmaku":
            dm_cfg = self._lexicon.get("danmaku_specific", {}) or {}
            if any(isinstance(w, str) and w in text for w in dm_cfg.get("praise", [])):
                score += 0.8
            if any(isinstance(w, str) and w in text for w in dm_cfg.get("mocking", [])):
                score -= 0.8
            if any(isinstance(w, str) and w in text for w in dm_cfg.get("moved", [])):
                score += 0.65
            if any(isinstance(w, str) and w in text for w in dm_cfg.get("disappointed", [])):
                score -= 0.8

        clauses = self._split_clauses(text)
        if len(clauses) > 1:
            tail = clauses[-1]
            tail_positive = len(self._find_hits(tail, "positive"))
            tail_negative = len(self._find_hits(tail, "negative"))
            if tail_negative > tail_positive:
                score -= 0.35
            elif tail_positive > tail_negative:
                score += 0.25

        if hits.get("neutral"):
            affective_count = sum(
                len(hits.get(bucket, []))
                for bucket in ("positive", "negative", "sarcasm", "strong_positive", "strong_negative")
            )
            if affective_count == 0:
                score *= 0.25

        score = math.tanh(score / 2.2)
        return round(score, 4), hits

    def _detect_emotion_tags(self, text: str, current_label: str, hits: Dict[str, List[str]]) -> List[str]:
        """
        根据规则词典检测情绪标签

        Returns:
            emotion_tags 列表
        """
        tags = []
        if hits.get("sarcasm"):
            tags.append("sarcasm")

        if current_label == "NEGATIVE" and (hits.get("negative") or hits.get("strong_negative") or hits.get("mild_negative")):
            tags.append("complaint")

        if current_label == "POSITIVE" and (hits.get("positive") or hits.get("strong_positive") or hits.get("mild_positive")):
            tags.append("praise")

        if "哈哈" in text or "233" in text or "笑" in text:
            tags.append("amused")

        if "失望" in text or "后悔" in text or "可惜" in text:
            tags.append("disappointment")

        if "感动" in text or "泪目" in text or "哭" in text:
            tags.append("moved")

        if "震撼" in text or "惊艳" in text:
            tags.append("surprised")

        if hits.get("neutral"):
            tags.append("neutral_signal")

        return list(set(tags))  # 去重

    def apply(
        self,
        result: dict,
        normalized: NormalizedText,
        text_type: str = "comment"
    ) -> dict:
        """
        对情感分析结果应用规则纠偏

        Args:
            result: SentimentAnalyzer 输出的结果字典
            normalized: 标准化后的文本对象
            text_type: 文本类型

        Returns:
            修正后的结果字典（in-place 修改并返回）
        """
        text = normalized.normalized_text
        confidence = result.get("confidence", 1.0)
        label = result.get("label", "NEUTRAL")
        is_low_confidence = confidence < _LOW_CONFIDENCE_THRESHOLD

        rule_score, hits = self._lexicon_score(text, text_type, label)
        model_score = float(result.get("score", 0.0))

        strong_rule = abs(rule_score) >= 0.5
        neutral_only = bool(hits.get("neutral")) and not any(
            hits.get(bucket)
            for bucket in ("positive", "negative", "sarcasm", "strong_positive", "strong_negative")
        )

        weight = 0.12 if confidence >= 0.82 and not strong_rule else 0.2
        if text_type == "danmaku":
            weight = 0.5
        elif normalized.features.get("is_short"):
            weight = 0.45
        elif is_low_confidence:
            weight = 0.35

        blended_score = max(-1.0, min(1.0, model_score * (1 - weight) + rule_score * weight))

        if neutral_only and normalized.features.get("normalized_length", 0) <= 12:
            blended_score *= 0.2

        if blended_score >= 0.22:
            blended_label = "POSITIVE"
        elif blended_score <= -0.22:
            blended_label = "NEGATIVE"
        else:
            blended_label = "NEUTRAL"

        if neutral_only and normalized.features.get("normalized_length", 0) <= 12:
            blended_label = "NEUTRAL"

        result["rule_score"] = rule_score
        result["score"] = round(blended_score, 4)
        result["label"] = blended_label
        result["rule_hits"] = hits
        result["rule_corrected"] = blended_label != label

        # 置信度在短文本/规则强命中时做轻微重估
        hit_strength = min(1.0, sum(
            len(hits.get(bucket, []))
            for bucket in ("positive", "negative", "sarcasm", "strong_positive", "strong_negative")
        ) / 3)
        recalibrated_conf = max(confidence, min(0.95, abs(rule_score) * 0.65 + hit_strength * 0.25))
        if strong_rule and hit_strength > 0:
            recalibrated_conf = max(recalibrated_conf, 0.58)
        if text_type == "danmaku" and confidence < 0.5:
            recalibrated_conf = max(recalibrated_conf, min(0.85, abs(rule_score) * 0.8))
        if neutral_only:
            recalibrated_conf = max(recalibrated_conf, 0.68)
        result["confidence"] = round(recalibrated_conf, 4)

        # 1. 检测并附加 emotion_tags
        emotion_tags = self._detect_emotion_tags(text, result["label"], hits)
        result["emotion_tags"] = emotion_tags

        # 2. 计算情感强度
        abs_score = abs(result.get("score", 0.0))
        if abs_score >= 0.75:
            result["intensity"] = "STRONG"
        elif abs_score >= 0.4:
            result["intensity"] = "MEDIUM"
        else:
            result["intensity"] = "WEAK"

        return result
