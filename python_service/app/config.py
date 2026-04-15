"""配置管理模块"""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[1] / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 3306
    db_user: str = "root"
    db_password: str
    db_name: str = "bili_insight_db"

    # 服务配置
    service_port: int = 8001
    service_host: str = "0.0.0.0"

    # B站配置
    bilibili_sessdata: Optional[str] = None

    # 分析配置
    sentiment_positive_threshold: float = 0.6
    sentiment_negative_threshold: float = 0.4
    sentiment_score_positive_threshold: float = 0.36
    sentiment_score_negative_threshold: float = -0.36
    sentiment_rule_low_confidence_threshold: float = 0.68
    sentiment_rule_high_confidence_threshold: float = 0.82
    sentiment_rule_high_confidence_weight: float = 0.12
    sentiment_rule_base_weight: float = 0.2
    sentiment_rule_low_confidence_weight: float = 0.35
    sentiment_rule_short_text_weight: float = 0.45
    sentiment_rule_danmaku_weight: float = 0.5
    aspect_score_positive_threshold: float = 0.22
    aspect_score_negative_threshold: float = -0.22
    aspect_min_confidence: float = 0.52
    timeline_window_size: int = 10

    # API安全配置
    api_key: Optional[str] = None

    # 浏览器态抓取配置
    browser_fallback_enabled: bool = True
    browser_headless: bool = True


# 创建全局配置实例
settings = Settings()
