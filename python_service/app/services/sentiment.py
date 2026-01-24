"""情感分析模块 - 使用SnowNLP"""
from snownlp import SnowNLP
import jieba
from typing import Dict, List
from ..config import settings


class SentimentAnalyzer:
    """情感分析器"""

    def __init__(self):
        """初始化分析器"""
        self.positive_threshold = settings.sentiment_positive_threshold
        self.negative_threshold = settings.sentiment_negative_threshold

        # B站特色词典（可后续扩展）
        self.bilibili_dict = {
            '三连': 5,
            'awsl': 5,
            '牛逼': 5,
            '太棒了': 5,
            '666': 4,
            '垃圾': -5,
            '骗钱': -5,
            '退订': -4,
            '差评': -4
        }

    def analyze_text(self, text: str) -> Dict[str, any]:
        """
        分析单条文本的情感

        Args:
            text: 待分析文本

        Returns:
            {
                "score": 0.85,  # 0-1之间的情感分数
                "label": "POSITIVE"  # POSITIVE/NEUTRAL/NEGATIVE
            }
        """
        if not text or not text.strip():
            return {"score": 0.5, "label": "NEUTRAL"}

        try:
            # 使用SnowNLP计算基础情感分数
            s = SnowNLP(text)
            base_score = s.sentiments

            # 应用规则增强
            final_score = self._enhance_sentiment(text, base_score)

            # 确保分数在0-1范围内
            final_score = max(0.0, min(1.0, final_score))

            # 判断情感标签
            if final_score >= self.positive_threshold:
                label = "POSITIVE"
            elif final_score <= self.negative_threshold:
                label = "NEGATIVE"
            else:
                label = "NEUTRAL"

            return {
                "score": round(final_score, 4),
                "label": label
            }

        except Exception as e:
            print(f"情感分析失败: {e}, 文本: {text[:50]}")
            return {"score": 0.5, "label": "NEUTRAL"}

    def _enhance_sentiment(self, text: str, base_score: float) -> float:
        """
        使用规则增强情感分数

        Args:
            text: 原始文本
            base_score: 基础情感分数

        Returns:
            增强后的情感分数
        """
        enhanced_score = base_score

        # 检测强情感词
        for word, weight in self.bilibili_dict.items():
            if word in text:
                if weight > 0:
                    # 正面词增强
                    enhanced_score = min(enhanced_score + 0.15, 1.0)
                else:
                    # 负面词降低
                    enhanced_score = max(enhanced_score - 0.15, 0.0)

        # 检测否定词
        negative_words = ['不', '没', '无', '别', '莫']
        for neg_word in negative_words:
            if neg_word in text:
                # 反转情感倾向
                enhanced_score = 1.0 - enhanced_score
                break

        return enhanced_score

    def batch_analyze(self, texts: List[str]) -> List[Dict[str, any]]:
        """
        批量分析文本情感

        Args:
            texts: 文本列表

        Returns:
            情感分析结果列表
        """
        return [self.analyze_text(text) for text in texts]

    def calculate_average_sentiment(self, texts: List[str]) -> float:
        """
        计算一组文本的平均情感值

        Args:
            texts: 文本列表

        Returns:
            平均情感分数
        """
        if not texts:
            return 0.5

        results = self.batch_analyze(texts)
        scores = [r['score'] for r in results if r['score'] is not None]

        if not scores:
            return 0.5

        return round(sum(scores) / len(scores), 4)
