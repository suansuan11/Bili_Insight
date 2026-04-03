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

    def _score_hit(self, text: str, hit: str, base_sign: int) -> float:
        idx = text.find(hit)
        negations = self._lexicon.get("negation", [])
        intensifiers = self._lexicon.get("intensifiers", [])

        score = 1.0 * base_sign
        if idx >= 0 and self._window_has_any(text, idx, intensifiers, backward=3, forward=0):
            score *= 1.35
        if idx >= 0 and self._window_has_any(text, idx, negations, backward=3, forward=0):
            score *= -1
        return score

    def _lexicon_score(self, text: str, text_type: str, current_label: str) -> Tuple[float, Dict[str, List[str]]]:
        positive_hits = self._find_hits(text, "positive")
        negative_hits = self._find_hits(text, "negative")
        sarcasm_hits = self._find_hits(text, "sarcasm")

        score = 0.0
        for hit in positive_hits:
            score += self._score_hit(text, hit, 1)
        for hit in negative_hits:
            score += self._score_hit(text, hit, -1)

        # 反讽词默认偏负向，尤其配合问号或负面词时
        if sarcasm_hits:
            sarcasm_bias = -0.9 if ("？" in text or "?" in text or negative_hits) else -0.35
            if current_label == "POSITIVE" and positive_hits and not negative_hits:
                sarcasm_bias *= 0.5
            score += sarcasm_bias

        if "这也叫" in text or "就这" in text:
            score -= 0.75

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

        score = math.tanh(score / 2.2)
        return round(score, 4), {
            "positive": positive_hits,
            "negative": negative_hits,
            "sarcasm": sarcasm_hits,
        }

    def _detect_emotion_tags(self, text: str, current_label: str, hits: Dict[str, List[str]]) -> List[str]:
        """
        根据规则词典检测情绪标签

        Returns:
            emotion_tags 列表
        """
        tags = []
        if hits.get("sarcasm"):
            tags.append("sarcasm")

        if current_label == "NEGATIVE" and hits.get("negative"):
            tags.append("complaint")

        if current_label == "POSITIVE" and hits.get("positive"):
            tags.append("praise")

        if "哈哈" in text or "233" in text or "笑" in text:
            tags.append("amused")

        if "失望" in text or "后悔" in text or "可惜" in text:
            tags.append("disappointment")

        if "感动" in text or "泪目" in text or "哭" in text:
            tags.append("moved")

        if "震撼" in text or "惊艳" in text:
            tags.append("surprised")

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

        weight = 0.2
        if text_type == "danmaku":
            weight = 0.5
        elif normalized.features.get("is_short"):
            weight = 0.4
        elif is_low_confidence:
            weight = 0.35

        blended_score = max(-1.0, min(1.0, model_score * (1 - weight) + rule_score * weight))

        if blended_score >= 0.22:
            blended_label = "POSITIVE"
        elif blended_score <= -0.22:
            blended_label = "NEGATIVE"
        else:
            blended_label = "NEUTRAL"

        result["rule_score"] = rule_score
        result["score"] = round(blended_score, 4)
        result["label"] = blended_label
        result["rule_hits"] = hits
        result["rule_corrected"] = blended_label != label

        # 置信度在短文本/规则强命中时做轻微重估
        hit_strength = min(1.0, (len(hits.get("positive", [])) + len(hits.get("negative", [])) + len(hits.get("sarcasm", []))) / 3)
        recalibrated_conf = max(confidence, min(0.95, abs(rule_score) * 0.65 + hit_strength * 0.25))
        if text_type == "danmaku" and confidence < 0.5:
            recalibrated_conf = max(recalibrated_conf, min(0.85, abs(rule_score) * 0.8))
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
