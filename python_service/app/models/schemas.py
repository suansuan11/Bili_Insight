"""Pydantic数据模型定义"""
from pydantic import BaseModel
from typing import Optional, List


class AnalyzeVideoRequest(BaseModel):
    """视频分析请求模型"""
    task_id: int
    bvid: str
    sessdata: Optional[str] = None


class AnalyzeVideoResponse(BaseModel):
    """视频分析响应模型"""
    status: str
    message: str
    task_id: int


class ProgressResponse(BaseModel):
    """进度查询响应模型"""
    task_id: int
    progress: int
    current_step: str
    status: str


class CommentData(BaseModel):
    """评论数据模型"""
    username: str
    gender: Optional[str] = None
    content: str
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class DanmakuData(BaseModel):
    """弹幕数据模型"""
    content: str
    dm_time: float
    sentiment_score: Optional[float] = None
    sentiment_label: Optional[str] = None


class TimelinePoint(BaseModel):
    """时间轴数据点模型"""
    time_point: float
    avg_sentiment: float
    danmaku_count: int
