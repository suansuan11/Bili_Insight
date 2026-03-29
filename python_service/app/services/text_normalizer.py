"""
文本标准化模块
负责对评论和弹幕做统一清洗与轻量标准化，为 Transformer 和规则层提供稳定输入
"""
import re
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class NormalizedText:
    raw_text: str
    normalized_text: str
    features: Dict = field(default_factory=dict)


class TextNormalizer:
    """
    中文文本标准化器

    支持:
    - 首尾空白去除
    - 连续空白压缩
    - 重复标点压缩（保留情绪强度信息）
    - 重复字符压缩
    - 常见网络语映射
    - URL / @用户名 清除
    - 特征提取（是否含问号、感叹号、文本长度等）
    """

    # 常见网络语映射
    SLANG_MAP = {
        "yyds": "永远的神",
        "YYDS": "永远的神",
        "awsl": "啊我死了",
        "AWSL": "啊我死了",
        "xswl": "笑死我了",
        "XSWL": "笑死我了",
        "emo": "情绪低落",
        "EMO": "情绪低落",
        "绝绝子": "绝了",
        "蚌埠住了": "忍不了了",
        "冲冲冲": "来了",
        "芜湖": "起飞",
    }

    def normalize(self, text: str, text_type: str = "comment") -> NormalizedText:
        """
        标准化文本

        Args:
            text: 原始文本
            text_type: 文本类型 comment / danmaku

        Returns:
            NormalizedText 对象
        """
        raw = text or ""
        t = raw.strip()

        # 基础特征提取（在重度清洗前）
        features = {
            "has_question_mark": "?" in t or "？" in t,
            "has_exclaim_mark": "!" in t or "！" in t,
            "length": len(t),
            "text_type": text_type,
            "is_short": len(t) <= 15,  # 弹幕/短评特征
        }

        # 1. 去除 URL
        t = re.sub(r'https?://\S+', '', t)

        # 2. 去除 @用户名
        t = re.sub(r'@[^\s，。！？\n]+', '', t)

        # 3. 连续空白压缩
        t = re.sub(r'\s+', ' ', t).strip()

        # 4. 网络语映射
        for slang, replacement in self.SLANG_MAP.items():
            t = t.replace(slang, replacement)

        # 5. 压缩重复标点，但保留情绪强度信息
        # 多个感叹号 -> !! (记录到 features)
        exclaim_count = len(re.findall(r'[!！]', t))
        features["exclaim_count"] = exclaim_count
        t = re.sub(r'[!！]{2,}', '！！', t)
        t = re.sub(r'[?？]{2,}', '？？', t)
        t = re.sub(r'[~～]{2,}', '～', t)
        t = re.sub(r'[。.]{2,}', '。', t)

        # 6. 重复字符压缩（保留最多3个，防止过度清洗）
        # 如 "哈哈哈哈哈哈" -> "哈哈哈"，但 "哈哈" 保留
        t = re.sub(r'(.)\1{3,}', r'\1\1\1', t)

        # 7. 弹幕专项：数字表情标准化
        if text_type == "danmaku":
            t = re.sub(r'\b2{3,}\b', '哈哈哈', t)  # 233 -> 哈哈哈
            t = re.sub(r'\b6{3,}\b', '好厉害', t)   # 666 -> 好厉害

        # 最终清理首尾空白
        t = t.strip()

        return NormalizedText(
            raw_text=raw,
            normalized_text=t,
            features=features
        )
