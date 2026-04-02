"""
领域规则纠偏模块
对 Transformer 模型结果做微调和纠偏，不替代模型
"""
import os
from typing import List, Optional
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

from ..utils.logger import logger
from .text_normalizer import NormalizedText

# 词典文件路径
_LEXICON_PATH = Path(__file__).parent.parent / "resources" / "domain_lexicon.yml"

# 低置信度阈值：低于此值允许规则层干预
_LOW_CONFIDENCE_THRESHOLD = 0.65


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

    def _check_negation(self, text: str) -> bool:
        """检查文本中是否有否定词紧跟正向词（粗粒度检测）"""
        negations = self._lexicon.get("negation", [])
        for neg in negations:
            if isinstance(neg, str) and neg in text:
                return True
        return False

    def _detect_emotion_tags(self, text: str, current_label: str) -> List[str]:
        """
        根据规则词典检测情绪标签

        Returns:
            emotion_tags 列表
        """
        tags = []
        sarcasm_words = self._lexicon.get("sarcasm", [])
        negative_words = self._lexicon.get("negative", [])
        positive_words = self._lexicon.get("positive", [])

        if any(isinstance(w, str) and w in text for w in sarcasm_words):
            tags.append("sarcasm")

        if current_label == "NEGATIVE" and any(isinstance(w, str) and w in text for w in negative_words):
            tags.append("complaint")

        if current_label == "POSITIVE" and any(isinstance(w, str) and w in text for w in positive_words):
            tags.append("praise")

        if "哈哈" in text or "233" in text or "笑" in text:
            tags.append("amused")

        if "失望" in text or "后悔" in text or "可惜" in text:
            tags.append("disappointment")

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

        # 1. 检测并附加 emotion_tags
        emotion_tags = self._detect_emotion_tags(text, label)
        result["emotion_tags"] = emotion_tags

        # 2. 仅在低置信度时尝试规则纠偏
        if is_low_confidence:
            positive_words = self._lexicon.get("positive", [])
            negative_words = self._lexicon.get("negative", [])

            has_positive = any(isinstance(w, str) and w in text for w in positive_words)
            has_negative = any(isinstance(w, str) and w in text for w in negative_words)
            has_negation = self._check_negation(text)

            # 强负面词命中 -> 倾向 NEGATIVE
            if has_negative and not has_positive and label != "NEGATIVE":
                result["label"] = "NEGATIVE"
                result["score"] = -abs(result.get("score", 0.3))
                result["rule_corrected"] = True
                logger.debug(f"规则层纠偏: {label} -> NEGATIVE (低置信度 + 负面词命中)")

            # 强正面词命中 + 无否定词 -> 倾向 POSITIVE
            elif has_positive and not has_negative and not has_negation and label != "POSITIVE":
                result["label"] = "POSITIVE"
                result["score"] = abs(result.get("score", 0.3))
                result["rule_corrected"] = True
                logger.debug(f"规则层纠偏: {label} -> POSITIVE (低置信度 + 正面词命中)")

        # 3. 计算情感强度
        abs_score = abs(result.get("score", 0.0))
        if abs_score >= 0.75:
            result["intensity"] = "STRONG"
        elif abs_score >= 0.4:
            result["intensity"] = "MEDIUM"
        else:
            result["intensity"] = "WEAK"

        return result
