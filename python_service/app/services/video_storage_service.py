"""
视频数据存储服务
负责将爬取的数据存入MySQL数据库，并进行情感分析
"""
from ..config import settings
from ..utils.logger import logger
import json
import uuid
from typing import List, Dict, Optional
from datetime import datetime
import pymysql
from pymysql.cursors import DictCursor

from .sentiment_analyzer import SentimentAnalyzer
from .aspect_analyzer import AspectAnalyzer


class VideoStorageService:
    """视频数据存储服务"""

    def __init__(self):
        """初始化数据库连接与分析模块"""
        self.db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'user': settings.db_user,
            'password': settings.db_password,
            'database': settings.db_name,
            'charset': 'utf8mb4'
        }

        # 注入情感分析模块（单例，懒加载模型）
        self.sentiment_analyzer = SentimentAnalyzer()
        self.aspect_analyzer = AspectAnalyzer(self.sentiment_analyzer)

    def get_connection(self):
        """获取数据库连接"""
        return pymysql.connect(**self.db_config, cursorclass=DictCursor)

    async def create_task(self, bvid: str, task_type: str = "VIDEO_REVIEW") -> str:
        """
        创建分析任务

        Args:
            bvid: 视频BVID
            task_type: 任务类型

        Returns:
            任务ID (UUID字符串)
        """
        task_id = str(uuid.uuid4())[:32]  # 生成UUID作为task_id
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO analysis_task (task_id, bvid, status, task_type, progress, current_step)
                    VALUES (%s, %s, 'RUNNING', %s, 0, '任务已创建')
                """
                cursor.execute(sql, (task_id, bvid, task_type))
                conn.commit()
                return task_id
        finally:
            conn.close()

    async def update_task_progress(self, task_id: str, progress: int, current_step: str):
        """更新任务进度，同时将状态置为 RUNNING"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE analysis_task
                    SET progress = %s, current_step = %s, status = 'RUNNING'
                    WHERE task_id = %s
                """
                cursor.execute(sql, (progress, current_step, task_id))
                conn.commit()
        finally:
            conn.close()

    async def update_task_video_info(self, task_id: str, title: Optional[str]):
        """回写视频标题，供任务列表和详情页直接读取"""
        if not title:
            return

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE analysis_task
                    SET video_title = %s, updated_at = NOW()
                    WHERE task_id = %s
                """
                cursor.execute(sql, (title[:255], task_id))
                conn.commit()
        finally:
            conn.close()

    async def update_task_comment_fetch_meta(self, task_id: str, fetch_meta: Optional[Dict]):
        """回写评论抓取元数据，便于后端和前端直接判断抓取稳定性"""
        if not fetch_meta:
            return

        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE analysis_task
                    SET comment_fetch_mode = %s,
                        comment_risk_controlled = %s,
                        comment_fetch_retries = %s,
                        updated_at = NOW()
                    WHERE task_id = %s
                """
                cursor.execute(sql, (
                    fetch_meta.get('mode'),
                    1 if fetch_meta.get('risk_controlled') else 0,
                    int(fetch_meta.get('retries') or 0),
                    task_id,
                ))
                conn.commit()
        finally:
            conn.close()

    async def complete_task(self, task_id: str):
        """标记任务完成"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE analysis_task
                    SET status = 'COMPLETED', progress = 100,
                        current_step = '分析完成', completed_at = NOW()
                    WHERE task_id = %s
                """
                cursor.execute(sql, (task_id,))
                conn.commit()
        finally:
            conn.close()

    async def fail_task(self, task_id: str, error_message: str):
        """标记任务失败"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    UPDATE analysis_task
                    SET status = 'FAILED', error_message = %s,
                        current_step = '分析失败',
                        completed_at = NOW()
                    WHERE task_id = %s
                """
                cursor.execute(sql, (error_message, task_id))
                conn.commit()
        finally:
            conn.close()

    def _analyze_comment_sentiment(self, content: str) -> dict:
        """分析评论情感（含 aspect 多切面）"""
        sentiment = self.sentiment_analyzer.analyze(content, text_type="comment")
        aspect_details = self.aspect_analyzer.analyze(content, text_type="comment")
        primary_aspect = self.aspect_analyzer.get_primary_aspect(aspect_details)
        return {
            "sentiment": sentiment,
            "aspect_details": aspect_details,
            "primary_aspect": primary_aspect,
        }

    def _analyze_danmaku_sentiment(self, content: str) -> dict:
        """分析弹幕情感（仅主情感，不做 aspect）"""
        sentiment = self.sentiment_analyzer.analyze(content, text_type="danmaku")
        return {"sentiment": sentiment}

    async def save_comments(self, task_id: str, bvid: str, comments: List[Dict]) -> int:
        """
        保存评论到数据库并进行情感分析（Transformer 升级版）

        Args:
            task_id: 任务ID
            bvid: 视频BVID
            comments: 评论列表

        Returns:
            保存的条数
        """
        if not comments:
            logger.warning(f"[{task_id}] 评论列表为空，跳过保存")
            return 0

        logger.info(f"[{task_id}] 开始保存评论 - 共{len(comments)}条")
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO video_comment
                    (comment_id, task_id, bvid, username, gender, text_type,
                     content, normalized_content, like_count,
                     sentiment_score, sentiment_label,
                     sentiment_confidence, sentiment_intensity,
                     sentiment_source, sentiment_version,
                     emotion_tags_json, aspect, aspect_details_json,
                     publish_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                inserted = 0
                for idx, comment in enumerate(comments):
                    content = comment.get('content', '')
                    if not content:
                        continue

                    # 情感分析（Transformer + 规则层 + aspect 多切面）
                    try:
                        analysis = self._analyze_comment_sentiment(content)
                        sentiment = analysis["sentiment"]
                        aspect_details = analysis["aspect_details"]
                        primary_aspect = analysis["primary_aspect"]
                    except Exception as e:
                        logger.warning(f"[{task_id}] 评论情感分析失败，使用默认值: {e}")
                        sentiment = {
                            "label": "NEUTRAL", "score": 0.0, "confidence": 0.0,
                            "intensity": "WEAK", "source": "error_fallback",
                            "version": "error", "emotion_tags": [],
                        }
                        aspect_details = []
                        primary_aspect = None

                    normalized_content = sentiment.get("normalized_text", content)
                    emotion_tags_json = json.dumps(
                        sentiment.get("emotion_tags", []), ensure_ascii=False
                    )
                    aspect_details_json = (
                        json.dumps(aspect_details, ensure_ascii=False)
                        if aspect_details else None
                    )

                    # 解析时间戳
                    publish_time = None
                    if comment.get('create_time'):
                        try:
                            publish_time = datetime.fromtimestamp(comment['create_time'])
                        except Exception:
                            pass

                    # 生成任务内唯一 comment_id，避免不同任务因 reply_id 冲突污染彼此数据
                    source_reply_id = comment.get('reply_id', 0)
                    if source_reply_id:
                        comment_id = abs(hash(f"{task_id}_{source_reply_id}")) % (2**63)
                    else:
                        comment_id = abs(hash(f"{task_id}_{bvid}_{content}_{inserted}")) % (2**63)

                    cursor.execute(sql, (
                        comment_id,
                        task_id,
                        bvid,
                        comment.get('author', '未知用户'),
                        comment.get('gender', '未知'),
                        'comment',
                        content,
                        normalized_content,
                        comment.get('like', 0),
                        sentiment.get('score', 0.0),
                        sentiment.get('label', 'NEUTRAL'),
                        sentiment.get('confidence', 0.0),
                        sentiment.get('intensity', 'WEAK'),
                        sentiment.get('source', ''),
                        sentiment.get('version', ''),
                        emotion_tags_json,
                        primary_aspect,
                        aspect_details_json,
                        publish_time
                    ))
                    inserted += 1

                    # 每100条记录输出一次进度
                    if (idx + 1) % 100 == 0:
                        logger.debug(f"[{task_id}] 评论保存进度: {idx + 1}/{len(comments)}")

                conn.commit()
                logger.info(f"[{task_id}] 评论保存完成 - 成功保存 {inserted} 条评论")
                return inserted

        except Exception as e:
            logger.error(f"[{task_id}] 保存评论失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    async def save_danmakus(self, task_id: str, bvid: str, danmakus: List[Dict]) -> int:
        """
        保存弹幕到数据库并进行情感分析（Transformer 升级版）

        Args:
            task_id: 任务ID
            bvid: 视频BVID
            danmakus: 弹幕列表

        Returns:
            保存的条数
        """
        if not danmakus:
            logger.warning(f"[{task_id}] 弹幕列表为空，跳过保存")
            return 0

        logger.info(f"[{task_id}] 开始保存弹幕 - 共{len(danmakus)}条")
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    INSERT INTO video_danmaku
                    (danmaku_id, task_id, bvid, text_type, content, normalized_content,
                     dm_time, appear_time,
                     sentiment_score, sentiment_label,
                     sentiment_confidence, sentiment_intensity,
                     sentiment_source, sentiment_version,
                     emotion_tags_json)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                inserted = 0
                for idx, dm in enumerate(danmakus):
                    content = dm.get('content', '')
                    if not content:
                        continue

                    # 情感分析（仅主情感，弹幕不强制做 aspect）
                    try:
                        analysis = self._analyze_danmaku_sentiment(content)
                        sentiment = analysis["sentiment"]
                    except Exception as e:
                        logger.warning(f"[{task_id}] 弹幕情感分析失败，使用默认值: {e}")
                        sentiment = {
                            "label": "NEUTRAL", "score": 0.0, "confidence": 0.0,
                            "intensity": "WEAK", "source": "error_fallback",
                            "version": "error", "emotion_tags": [],
                            "normalized_text": content,
                        }

                    normalized_content = sentiment.get("normalized_text", content)
                    emotion_tags_json = json.dumps(
                        sentiment.get("emotion_tags", []), ensure_ascii=False
                    )

                    dm_time = int(dm.get('dm_time', 0))
                    danmaku_id = abs(hash(f"{bvid}_{content}_{dm_time}_{inserted}")) % (2**63)

                    cursor.execute(sql, (
                        danmaku_id,
                        task_id,
                        bvid,
                        'danmaku',
                        content,
                        normalized_content,
                        dm_time,
                        dm_time,  # appear_time = dm_time
                        sentiment.get('score', 0.0),
                        sentiment.get('label', 'NEUTRAL'),
                        sentiment.get('confidence', 0.0),
                        sentiment.get('intensity', 'WEAK'),
                        sentiment.get('source', ''),
                        sentiment.get('version', ''),
                        emotion_tags_json,
                    ))
                    inserted += 1

                    # 每500条记录输出一次进度
                    if (idx + 1) % 500 == 0:
                        logger.debug(f"[{task_id}] 弹幕保存进度: {idx + 1}/{len(danmakus)}")

                conn.commit()
                logger.info(f"[{task_id}] 弹幕保存完成 - 成功保存 {inserted} 条弹幕")
                return inserted

        except Exception as e:
            logger.error(f"[{task_id}] 保存弹幕失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    async def generate_sentiment_timeline(self, task_id: str, bvid: str, comment_fetch_meta: Optional[Dict] = None) -> Dict:
        """
        生成情绪时间轴数据

        Args:
            task_id: 任务ID
            bvid: 视频BVID

        Returns:
            包含timeline和aspects的字典
        """
        logger.info(f"[{task_id}] 开始生成情绪时间轴和切面分析")
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                # 1. 按10秒间隔聚合弹幕情感得分（confidence 加权均值）
                logger.debug(f"[{task_id}] 查询弹幕数据生成时间轴")
                sql_timeline = """
                    SELECT
                        FLOOR(dm_time / 10) * 10 as time_bucket,
                        SUM(sentiment_score * COALESCE(sentiment_confidence, 0.5)) /
                            SUM(COALESCE(sentiment_confidence, 0.5)) as weighted_score,
                        AVG(sentiment_score) as avg_score,
                        COUNT(*) as count
                    FROM video_danmaku
                    WHERE task_id = %s AND sentiment_score IS NOT NULL
                    GROUP BY time_bucket
                    ORDER BY time_bucket
                """
                cursor.execute(sql_timeline, (task_id,))
                timeline_rows = cursor.fetchall()

                timeline = [
                    {
                        'time': int(row['time_bucket']),
                        'score': round(float(row['weighted_score'] or row['avg_score']), 4),
                        'count': row['count']
                    }
                    for row in timeline_rows
                ]
                logger.info(f"[{task_id}] 生成时间轴数据点: {len(timeline)} 个")

                # 2. 计算切面情感得分（基于评论，优先使用 aspect_details_json）
                logger.debug(f"[{task_id}] 查询评论数据生成切面分析")
                # 先从 aspect_details_json 中聚合（新字段）
                sql_aspect_details = """
                    SELECT aspect_details_json, sentiment_confidence
                    FROM video_comment
                    WHERE task_id = %s AND aspect_details_json IS NOT NULL
                """
                cursor.execute(sql_aspect_details, (task_id,))
                aspect_detail_rows = cursor.fetchall()

                # 聚合多 aspect 明细
                aspect_agg: Dict = {}
                for row in aspect_detail_rows:
                    try:
                        details = json.loads(row['aspect_details_json'])
                        conf = float(row.get('sentiment_confidence') or 0.5)
                        for d in details:
                            asp = d.get('aspect')
                            score = d.get('score', 0.0)
                            label = d.get('label', 'NEUTRAL')
                            if asp not in aspect_agg:
                                aspect_agg[asp] = {'score_sum': 0.0, 'conf_sum': 0.0,
                                                   'count': 0, 'positive': 0,
                                                   'neutral': 0, 'negative': 0}
                            weight = conf
                            aspect_agg[asp]['score_sum'] += score * weight
                            aspect_agg[asp]['conf_sum'] += weight
                            aspect_agg[asp]['count'] += 1
                            aspect_agg[asp][label.lower()] = aspect_agg[asp].get(label.lower(), 0) + 1
                    except Exception:
                        pass

                if aspect_agg:
                    aspects = {
                        asp: {
                            'score': round(v['score_sum'] / v['conf_sum'], 4) if v['conf_sum'] > 0 else 0.0,
                            'count': v['count'],
                            'positive': v.get('positive', 0),
                            'neutral': v.get('neutral', 0),
                            'negative': v.get('negative', 0),
                        }
                        for asp, v in aspect_agg.items()
                    }
                else:
                    # 回退到旧 aspect 字段聚合
                    sql_aspects = """
                        SELECT
                            aspect,
                            AVG(sentiment_score) as avg_score,
                            COUNT(*) as count
                        FROM video_comment
                        WHERE task_id = %s AND aspect IS NOT NULL
                        GROUP BY aspect
                    """
                    cursor.execute(sql_aspects, (task_id,))
                    aspect_rows = cursor.fetchall()
                    aspects = {
                        row['aspect']: {
                            'score': round(float(row['avg_score']), 4),
                            'count': row['count']
                        }
                        for row in aspect_rows
                    }
                logger.info(f"[{task_id}] 生成切面分析: {len(aspects)} 个切面 - {list(aspects.keys())}")

                # 3. 保存到sentiment_timeline表
                timeline_json = json.dumps(timeline, ensure_ascii=False)
                aspect_json = json.dumps(aspects, ensure_ascii=False)
                aggregation_meta = {
                    "version": "timeline-v2",
                    "weight": "sentiment_confidence",
                    "window_seconds": 10,
                }
                if comment_fetch_meta:
                    aggregation_meta["comment_fetch"] = comment_fetch_meta
                aggregation_meta_json = json.dumps(aggregation_meta, ensure_ascii=False)

                logger.debug(f"[{task_id}] 保存时间轴和切面数据到数据库")
                sql_insert = """
                    INSERT INTO sentiment_timeline
                        (task_id, bvid, timeline_json, aspect_sentiment_json,
                         timeline_version, aggregation_meta_json)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        timeline_json = VALUES(timeline_json),
                        aspect_sentiment_json = VALUES(aspect_sentiment_json),
                        timeline_version = VALUES(timeline_version),
                        aggregation_meta_json = VALUES(aggregation_meta_json)
                """
                cursor.execute(sql_insert, (
                    task_id, bvid, timeline_json, aspect_json,
                    'timeline-v2', aggregation_meta_json
                ))
                conn.commit()

                logger.info(f"[{task_id}] 情绪时间轴和切面分析生成完成")
                return {
                    'timeline': timeline,
                    'aspects': aspects
                }

        except Exception as e:
            logger.error(f"[{task_id}] 生成情绪时间轴失败: {e}", exc_info=True)
            raise
        finally:
            conn.close()

    async def get_task_info(self, task_id: str) -> Dict:
        """查询任务信息"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = "SELECT * FROM analysis_task WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                return cursor.fetchone()
        finally:
            conn.close()

    async def get_comment_stats(self, task_id: str) -> Dict:
        """查询评论统计"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive,
                        SUM(CASE WHEN sentiment_label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral,
                        SUM(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative
                    FROM video_comment
                    WHERE task_id = %s
                """
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()

                total = result['total'] or 0
                return {
                    'total': total,
                    'positive': result['positive'] or 0,
                    'neutral': result['neutral'] or 0,
                    'negative': result['negative'] or 0,
                    'positive_rate': (result['positive'] or 0) / total if total > 0 else 0,
                    'neutral_rate': (result['neutral'] or 0) / total if total > 0 else 0,
                    'negative_rate': (result['negative'] or 0) / total if total > 0 else 0
                }
        finally:
            conn.close()

    async def get_danmaku_stats(self, task_id: str) -> Dict:
        """查询弹幕统计"""
        conn = self.get_connection()
        try:
            with conn.cursor() as cursor:
                sql = """
                    SELECT
                        COUNT(*) as total,
                        SUM(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 ELSE 0 END) as positive,
                        SUM(CASE WHEN sentiment_label = 'NEUTRAL' THEN 1 ELSE 0 END) as neutral,
                        SUM(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 ELSE 0 END) as negative
                    FROM video_danmaku
                    WHERE task_id = %s
                """
                cursor.execute(sql, (task_id,))
                result = cursor.fetchone()

                total = result['total'] or 0
                return {
                    'total': total,
                    'positive': result['positive'] or 0,
                    'neutral': result['neutral'] or 0,
                    'negative': result['negative'] or 0,
                    'positive_rate': (result['positive'] or 0) / total if total > 0 else 0,
                    'neutral_rate': (result['neutral'] or 0) / total if total > 0 else 0,
                    'negative_rate': (result['negative'] or 0) / total if total > 0 else 0
                }
        finally:
            conn.close()
