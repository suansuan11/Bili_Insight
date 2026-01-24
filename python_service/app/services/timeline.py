"""情绪时间轴生成模块"""
from typing import List, Dict
from ..config import settings


class TimelineGenerator:
    """情绪时间轴生成器"""

    def __init__(self, window_size: int = None):
        """
        初始化生成器

        Args:
            window_size: 时间窗口大小(秒)，默认从配置读取
        """
        self.window_size = window_size or settings.timeline_window_size

    def generate_timeline(self, danmakus: List[Dict]) -> List[Dict]:
        """
        生成情绪时间轴

        Args:
            danmakus: 弹幕列表，每个包含:
                {
                    "content": "弹幕文本",
                    "dm_time": 15.5,  # 弹幕时间点(秒)
                    "sentiment_score": 0.8  # 情感分数
                }

        Returns:
            时间轴数据点列表:
            [
                {"time_point": 0, "avg_sentiment": 0.75, "danmaku_count": 10},
                {"time_point": 10, "avg_sentiment": 0.82, "danmaku_count": 25},
                ...
            ]
        """
        if not danmakus:
            return []

        # 按时间排序
        sorted_danmakus = sorted(danmakus, key=lambda x: x.get('dm_time', 0))

        # 获取视频总时长（最后一条弹幕的时间）
        max_time = max(dm.get('dm_time', 0) for dm in sorted_danmakus)

        if max_time <= 0:
            return []

        timeline = []

        # 按时间窗口划分
        current_time = 0
        while current_time <= max_time:
            end_time = current_time + self.window_size

            # 筛选当前时间窗口内的弹幕
            window_danmakus = [
                dm for dm in sorted_danmakus
                if current_time <= dm.get('dm_time', 0) < end_time
            ]

            if window_danmakus:
                # 计算平均情感值
                scores = [dm.get('sentiment_score', 0.5) for dm in window_danmakus
                          if dm.get('sentiment_score') is not None]

                avg_sentiment = sum(scores) / len(scores) if scores else 0.5

                timeline.append({
                    "time_point": round(current_time, 3),
                    "avg_sentiment": round(avg_sentiment, 4),
                    "danmaku_count": len(window_danmakus)
                })

            current_time += self.window_size

        # 应用平滑处理
        return self._smooth_timeline(timeline)

    def _smooth_timeline(self, timeline: List[Dict], window: int = 3) -> List[Dict]:
        """
        对时间轴进行移动平均平滑

        Args:
            timeline: 原始时间轴数据
            window: 平滑窗口大小

        Returns:
            平滑后的时间轴数据
        """
        if len(timeline) < window:
            return timeline

        smoothed = []
        for i in range(len(timeline)):
            start = max(0, i - window // 2)
            end = min(len(timeline), i + window // 2 + 1)

            # 计算窗口内平均情感值
            avg = sum(t['avg_sentiment'] for t in timeline[start:end]) / (end - start)

            smoothed_point = timeline[i].copy()
            smoothed_point['avg_sentiment'] = round(avg, 4)
            smoothed.append(smoothed_point)

        return smoothed

    def fill_gaps(self, timeline: List[Dict], video_duration: float) -> List[Dict]:
        """
        填充时间轴空白区域

        Args:
            timeline: 原始时间轴
            video_duration: 视频总时长

        Returns:
            填充后的完整时间轴
        """
        if not timeline:
            return []

        filled = []
        time_points = [t['time_point'] for t in timeline]

        current_time = 0
        while current_time <= video_duration:
            if current_time in time_points:
                # 已有数据点
                idx = time_points.index(current_time)
                filled.append(timeline[idx])
            else:
                # 插值填充
                prev_point = None
                next_point = None

                for t in timeline:
                    if t['time_point'] < current_time:
                        prev_point = t
                    elif t['time_point'] > current_time and next_point is None:
                        next_point = t
                        break

                # 计算插值
                if prev_point and next_point:
                    sentiment = (prev_point['avg_sentiment'] + next_point['avg_sentiment']) / 2
                elif prev_point:
                    sentiment = prev_point['avg_sentiment']
                elif next_point:
                    sentiment = next_point['avg_sentiment']
                else:
                    sentiment = 0.5

                filled.append({
                    "time_point": round(current_time, 3),
                    "avg_sentiment": round(sentiment, 4),
                    "danmaku_count": 0
                })

            current_time += self.window_size

        return filled
