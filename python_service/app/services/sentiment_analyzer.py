"""
主情感分析模块
负责加载 Transformer 模型，对评论和弹幕分流推理
"""
from typing import Dict, Optional
from ..utils.logger import logger

# 懒加载 transformers / torch，避免首次导入在无 GPU 环境报错
_TRANSFORMERS_AVAILABLE = False
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    _TRANSFORMERS_AVAILABLE = True
except ImportError:
    logger.warning("transformers / torch 未安装，情感分析将回退到 SnowNLP fallback 模式")

from .text_normalizer import TextNormalizer, NormalizedText
from .domain_rules import DomainRuleEngine
from .model_registry import ModelRegistry, ModelConfig


class SentimentAnalyzer:
    """
    Transformer 主情感分析器

    特性:
    - 懒加载模型（首次调用 analyze 时才加载）
    - 评论 / 弹幕分流，使用独立配置
    - 规则层纠偏（低置信度时）
    - 分数映射到 [-1, 1] 范围
    - 自动 fallback 到 SnowNLP（当 transformers 不可用时）
    """

    def __init__(self):
        self.normalizer = TextNormalizer()
        self.rule_engine = DomainRuleEngine()
        self._tokenizers: Dict[str, object] = {}
        self._models: Dict[str, object] = {}
        self._use_fallback = not _TRANSFORMERS_AVAILABLE

        if self._use_fallback:
            self._init_fallback()

    def _init_fallback(self):
        """初始化 SnowNLP fallback"""
        try:
            from snownlp import SnowNLP
            self._SnowNLP = SnowNLP
            logger.info("SentimentAnalyzer: 使用 SnowNLP fallback 模式")
        except ImportError:
            self._SnowNLP = None
            logger.error("SnowNLP 也不可用，情感分析将返回默认 NEUTRAL")

    def _load_model(self, text_type: str):
        """懒加载 Transformer 模型（单例，按模型名缓存）"""
        cfg = ModelRegistry.get_config(text_type)
        model_name = cfg.model_name

        if model_name not in self._models:
            logger.info(f"加载情感模型: {model_name} (text_type={text_type})")
            try:
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSequenceClassification.from_pretrained(model_name)
                model.eval()
                # 若有 GPU 则使用
                if _TRANSFORMERS_AVAILABLE and torch.cuda.is_available():
                    model = model.cuda()
                    logger.info(f"模型已加载到 GPU: {model_name}")
                else:
                    logger.info(f"模型已加载到 CPU: {model_name}")
                self._tokenizers[model_name] = tokenizer
                self._models[model_name] = model
            except Exception as e:
                logger.error(f"模型加载失败: {model_name}, error={e}")
                raise RuntimeError(f"无法加载情感分析模型: {model_name}") from e

        return cfg, self._tokenizers[model_name], self._models[model_name]

    def _analyze_with_transformer(
        self, normalized: NormalizedText, text_type: str, text_pair: Optional[str] = None
    ) -> dict:
        """使用 Transformer 模型推理"""
        cfg, tokenizer, model = self._load_model(text_type)

        if text_pair is None:
            inputs = tokenizer(
                normalized.normalized_text,
                return_tensors="pt",
                truncation=True,
                max_length=cfg.max_length,
                padding=True
            )
        else:
            inputs = tokenizer(
                normalized.normalized_text,
                text_pair,
                return_tensors="pt",
                truncation=True,
                max_length=cfg.max_length,
                padding=True
            )

        # 若模型在 GPU 则 inputs 也要移到 GPU
        if _TRANSFORMERS_AVAILABLE and torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
            probs = torch.softmax(logits, dim=-1).squeeze().tolist()

        # 确保 probs 是列表（batch_size=1 时 squeeze 可能返回标量）
        if not isinstance(probs, list):
            probs = [probs]

        label_probs = {
            cfg.label_mapping[i]: float(probs[i])
            for i in range(len(probs))
            if i in cfg.label_mapping
        }

        label = max(label_probs, key=label_probs.get)
        confidence = label_probs[label]
        score = label_probs.get("POSITIVE", 0.0) - label_probs.get("NEGATIVE", 0.0)

        return {
            "label": label,
            "score": round(score, 4),
            "confidence": round(confidence, 4),
            "source": f"transformer_{text_type}_v1",
            "version": cfg.version,
            "raw_probs": {k: round(v, 4) for k, v in label_probs.items()},
            "normalized_text": normalized.normalized_text,
        }

    def _analyze_with_fallback(
        self, normalized: NormalizedText, text_type: str, text_pair: Optional[str] = None
    ) -> dict:
        """SnowNLP fallback 推理"""
        text = normalized.normalized_text if text_pair is None else f"{normalized.normalized_text} {text_pair}"
        if not text:
            return self._empty_result(text_type)

        if self._SnowNLP is None:
            return self._empty_result(text_type)

        try:
            s = self._SnowNLP(text)
            raw_score = s.sentiments  # 0-1

            # 映射到 [-1, 1]
            score = round(raw_score * 2 - 1, 4)

            if raw_score >= 0.65:
                label = "POSITIVE"
            elif raw_score <= 0.35:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"

            confidence = round(abs(raw_score - 0.5) * 2, 4)

            return {
                "label": label,
                "score": score,
                "confidence": confidence,
                "source": f"fallback_snownlp_{text_type}_v1",
                "version": "snownlp-fallback-v1.0.0",
                "raw_probs": {},
                "normalized_text": normalized.normalized_text,
            }
        except Exception as e:
            logger.debug(f"SnowNLP fallback 失败: {e}")
            return self._empty_result(text_type)

    def _empty_result(self, text_type: str) -> dict:
        """空文本默认结果"""
        return {
            "label": "NEUTRAL",
            "score": 0.0,
            "confidence": 0.0,
            "source": f"fallback_empty_{text_type}",
            "version": "fallback-v1.0.0",
            "raw_probs": {},
            "normalized_text": "",
        }

    def analyze(self, text: str, text_type: str = "comment") -> dict:
        """
        分析文本情感

        Args:
            text: 原始文本
            text_type: 文本类型 'comment' / 'danmaku'

        Returns:
            dict 包含:
                label: POSITIVE / NEUTRAL / NEGATIVE
                score: [-1.0, 1.0]
                confidence: [0.0, 1.0]
                intensity: WEAK / MEDIUM / STRONG
                emotion_tags: list
                source: 分析来源标识
                version: 模型版本
                raw_probs: 原始概率分布
                normalized_text: 标准化后文本
        """
        if not text or not text.strip():
            result = self._empty_result(text_type)
            result["intensity"] = "WEAK"
            result["emotion_tags"] = []
            return result

        normalized = self.normalizer.normalize(text, text_type)

        if self._use_fallback:
            result = self._analyze_with_fallback(normalized, text_type)
        else:
            try:
                result = self._analyze_with_transformer(normalized, text_type)
            except Exception as e:
                logger.warning(f"Transformer 推理失败，本次请求回退到 SnowNLP: {e}")
                self._init_fallback()
                result = self._analyze_with_fallback(normalized, text_type)

        # 应用规则纠偏（会添加 intensity / emotion_tags）
        result = self.rule_engine.apply(result, normalized, text_type=text_type)

        return result

    def analyze_aspect(self, aspect: str, text: str, text_type: str = "comment") -> dict:
        """
        对 aspect + 文本对做情感判别。

        当前仍复用主情感模型，但使用真正的 pair 输入而不是简单字符串拼接，
        以避免所有 aspect 继承整句同一极性。
        """
        if not text or not text.strip():
            result = self._empty_result(text_type)
            result["intensity"] = "WEAK"
            result["emotion_tags"] = []
            return result

        normalized = self.normalizer.normalize(text, text_type)

        if self._use_fallback:
            result = self._analyze_with_fallback(normalized, text_type, text_pair=aspect)
        else:
            try:
                result = self._analyze_with_transformer(normalized, text_type, text_pair=aspect)
            except Exception as e:
                logger.warning(f"Transformer aspect 推理失败，本次请求回退到 SnowNLP: {e}")
                self._init_fallback()
                result = self._analyze_with_fallback(normalized, text_type, text_pair=aspect)

        result = self.rule_engine.apply(result, normalized, text_type=text_type)
        return result
