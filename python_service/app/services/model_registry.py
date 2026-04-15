"""
模型注册表模块
统一管理评论模型和弹幕模型，避免业务代码直接依赖具体模型名称
"""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
except Exception:
    pass

_PYTHON_SERVICE_DIR = Path(__file__).resolve().parents[2]
_REPO_ROOT = _PYTHON_SERVICE_DIR.parent


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    version: str
    max_length: int
    label_mapping: Dict[int, str]
    score_mapping: Dict[int, float]
    # HuggingFace Hub 名称（当本地不存在时回退到此）
    hf_hub_name: str = ""


class ModelRegistry:
    """
    模型注册表

    当前默认改为中文 RoBERTa 五级情感模型，再折叠为：
    1/2 星 -> NEGATIVE
    3 星   -> NEUTRAL
    4/5 星 -> POSITIVE

    注意：
    - 首次加载会自动从 HuggingFace Hub 下载模型
    - 可将模型下载到 python_service/models/ 目录后改为本地路径
    - 可通过环境变量 COMMENT_MODEL / DANMAKU_MODEL 覆盖
    """

    # 评论模型：中文语境更强，五级评分模型再折叠为三极性
    COMMENT_MODEL = ModelConfig(
        model_name="H-Z-Ning/Senti-RoBERTa-Mini",
        version="comment-chinese-roberta-v2.0.0",
        max_length=256,
        label_mapping={
            0: "NEGATIVE",
            1: "NEGATIVE",
            2: "NEUTRAL",
            3: "POSITIVE",
            4: "POSITIVE",
        },
        score_mapping={
            0: -1.0,
            1: -0.55,
            2: 0.0,
            3: 0.55,
            4: 1.0,
        },
        hf_hub_name="H-Z-Ning/Senti-RoBERTa-Mini"
    )

    # 弹幕模型：当前同样切到中文 RoBERTa，但缩短最大长度
    DANMAKU_MODEL = ModelConfig(
        model_name="H-Z-Ning/Senti-RoBERTa-Mini",
        version="danmaku-chinese-roberta-v2.0.0",
        max_length=96,
        label_mapping={
            0: "NEGATIVE",
            1: "NEGATIVE",
            2: "NEUTRAL",
            3: "POSITIVE",
            4: "POSITIVE",
        },
        score_mapping={
            0: -1.0,
            1: -0.55,
            2: 0.0,
            3: 0.55,
            4: 1.0,
        },
        hf_hub_name="H-Z-Ning/Senti-RoBERTa-Mini"
    )

    @staticmethod
    def _resolve_model_name(model_name: str) -> str:
        """
        Resolve local model paths independent of current working directory.

        The service can be started from the repository root or from
        python_service/. Users may also keep the historical
        python_service/models/... value in .env. HuggingFace model IDs are
        returned unchanged.
        """
        if not model_name:
            return model_name

        raw_path = Path(model_name).expanduser()
        if raw_path.is_absolute():
            return str(raw_path)

        candidates = [
            Path.cwd() / raw_path,
            _PYTHON_SERVICE_DIR / raw_path,
            _REPO_ROOT / raw_path,
        ]
        if raw_path.parts and raw_path.parts[0] == _PYTHON_SERVICE_DIR.name:
            candidates.append(_REPO_ROOT / raw_path)
            candidates.append(_PYTHON_SERVICE_DIR / Path(*raw_path.parts[1:]))

        for candidate in candidates:
            if candidate.exists():
                return str(candidate)

        return model_name

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

        scheme_key = "DANMAKU_MODEL_LABEL_SCHEME" if text_type == "danmaku" else "COMMENT_MODEL_LABEL_SCHEME"
        label_scheme = os.getenv(scheme_key, "").strip().lower()
        if label_scheme == "three_class":
            label_mapping = {
                0: "NEGATIVE",
                1: "NEUTRAL",
                2: "POSITIVE",
            }
            score_mapping = {
                0: -1.0,
                1: 0.0,
                2: 1.0,
            }
        else:
            label_mapping = base.label_mapping
            score_mapping = base.score_mapping

        return ModelConfig(
            model_name=cls._resolve_model_name(env_model_name),
            version=f"{base.version}-env",
            max_length=base.max_length,
            label_mapping=label_mapping,
            score_mapping=score_mapping,
            hf_hub_name=env_model_name,
        )
