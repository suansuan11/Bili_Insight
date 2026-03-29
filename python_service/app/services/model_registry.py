"""
模型注册表模块
统一管理评论模型和弹幕模型，避免业务代码直接依赖具体模型名称
"""
import os
from dataclasses import dataclass
from typing import Dict


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    version: str
    max_length: int
    label_mapping: Dict[int, str]
    # HuggingFace Hub 名称（当本地不存在时回退到此）
    hf_hub_name: str = ""


class ModelRegistry:
    """
    模型注册表

    推荐中文情感分类模型（三分类 POSITIVE / NEUTRAL / NEGATIVE）：
    - lxyuan/distilbert-base-multilingual-cased-sentiments-student
      （多语言，含中文，有三分类，下载小）
    - techthiyanes/chinese_sentiment (3分类)
    - cardiffnlp/twitter-xlm-roberta-base-sentiment (多语言)

    如果使用五分类（1-5分星）模型，label_mapping 需相应调整。

    注意：
    - 首次加载会自动从 HuggingFace Hub 下载模型
    - 可将模型下载到 python_service/models/ 目录后改为本地路径
    - 可通过环境变量 COMMENT_MODEL / DANMAKU_MODEL 覆盖
    """

    # 评论模型：较长文本，max_length 256
    COMMENT_MODEL = ModelConfig(
        model_name="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
        version="comment-multilingual-distilbert-v1.0.0",
        max_length=256,
        label_mapping={0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"},
        hf_hub_name="lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    )

    # 弹幕模型：短文本，max_length 64（与评论共用同一模型，后续可替换）
    DANMAKU_MODEL = ModelConfig(
        model_name="lxyuan/distilbert-base-multilingual-cased-sentiments-student",
        version="danmaku-multilingual-distilbert-v1.0.0",
        max_length=64,
        label_mapping={0: "NEGATIVE", 1: "NEUTRAL", 2: "POSITIVE"},
        hf_hub_name="lxyuan/distilbert-base-multilingual-cased-sentiments-student"
    )

    @classmethod
    def get_config(cls, text_type: str) -> ModelConfig:
        """
        根据文本类型获取对应的模型配置

        Args:
            text_type: 'comment' 或 'danmaku'

        Returns:
            ModelConfig
        """
        base = cls.DANMAKU_MODEL if text_type == "danmaku" else cls.COMMENT_MODEL
        env_key = "DANMAKU_MODEL" if text_type == "danmaku" else "COMMENT_MODEL"
        env_model_name = os.getenv(env_key)

        if not env_model_name:
            return base

        return ModelConfig(
            model_name=env_model_name,
            version=f"{base.version}-env",
            max_length=base.max_length,
            label_mapping=base.label_mapping,
            hf_hub_name=env_model_name,
        )
