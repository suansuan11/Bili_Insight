"""配置管理模块"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置类"""

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
    timeline_window_size: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


# 创建全局配置实例
settings = Settings()
