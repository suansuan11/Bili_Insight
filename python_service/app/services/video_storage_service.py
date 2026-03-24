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
import jieba
import jieba.analyse
from snownlp import SnowNLP
import pymysql
from pymysql.cursors import DictCursor


class VideoStorageService:
    """视频数据存储服务"""

    def __init__(self):
        """初始化数据库连接"""
        self.db_config = {
            'host': settings.db_host,
            'port': settings.db_port,
            'user': settings.db_user,
            'password': settings.db_password,
            'database': settings.db_name,
            'charset': 'utf8mb4'
        }

        # ABSA切面关键词库（通用 + 数码 + 美食 + 游戏 + 生活）
        self.aspect_keywords = {
            # 数码/产品类
            '外观': ['外观', '颜值', '设计', '外形', '好看', '漂亮', '丑', '美', '造型', '外壳', '配色'],
            '性能': ['性能', '配置', '速度', '快', '慢', '卡', '流畅', '处理器', '芯片', '帧率', '延迟'],
            '价格': ['价格', '贵', '便宜', '性价比', '值', '划算', '钱', '元', '块', '折扣', '优惠'],
            '续航': ['续航', '电池', '耗电', '充电', '电量', '待机', '掉电'],
            '拍照': ['拍照', '摄像', '相机', '照片', '镜头', '像素', '夜拍', '画质'],
            '屏幕': ['屏幕', '显示', '分辨率', '刷新率', '亮度', '色彩', '护眼'],
            '系统': ['系统', '软件', '界面', 'UI', '操作', '体验', '功能', '更新'],
            '售后': ['售后', '服务', '维修', '保修', '客服', '退换', '质量'],
            # 美食/食品类
            '口味': ['好吃', '难吃', '味道', '口感', '香', '甜', '咸', '辣', '酸', '苦', '鲜', '腻', '清淡', '重口'],
            '食材': ['食材', '原料', '配料', '新鲜', '食品', '原材料', '用料'],
            '分量': ['分量', '份量', '多', '少', '够吃', '不够', '量大', '量少', '性价比'],
            '环境': ['环境', '装修', '氛围', '干净', '卫生', '脏', '嘈杂', '安静', '位置'],
            # 内容/视频类
            '内容': ['内容', '干货', '有用', '没用', '信息量', '知识', '教程', '讲解', '清晰'],
            '剪辑': ['剪辑', '节奏', '画面', '特效', '转场', '字幕', '配乐', 'bgm', '音效'],
            '主播': ['主播', 'up主', 'up', '博主', '作者', '讲得', '说得', '表达', '幽默', '有趣'],
            # 游戏类
            '玩法': ['玩法', '操作', '手感', '机制', '系统', '模式', '难度', '平衡'],
            '画面': ['画面', '画质', '特效', '渲染', '分辨率', '帧数', '优化'],
            # 通用情感
            '整体': ['总体', '整体', '总的来说', '综合', '推荐', '不推荐', '值得', '后悔']
        }

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
                        completed_at = NOW()
                    WHERE task_id = %s
                """
                cursor.execute(sql, (error_message, task_id))
                conn.commit()
        finally:
            conn.close()

    def calculate_sentiment(self, text: str) -> tuple:
        """
        计算文本情感得分

        Args:
            text: 文本内容

        Returns:
            (score, label) - 得分(0-1)和标签(POSITIVE/NEUTRAL/NEGATIVE)
        """
        if not text or len(text.strip()) == 0:
            return 0.5, 'NEUTRAL'

        try:
            s = SnowNLP(text)
            score = s.sentiments  # 0-1之间，越接近1越正面

            # 使用配置中的阈值
            if score >= settings.sentiment_positive_threshold:
                label = 'POSITIVE'
            elif score <= settings.sentiment_negative_threshold:
                label = 'NEGATIVE'
            else:
                label = 'NEUTRAL'

            return round(score, 4), label

        except Exception as e:
            logger.debug(f"情感分析失败: {e}")
            return 0.5, 'NEUTRAL'

    def detect_aspect(self, text: str) -> Optional[str]:
        """
        检测文本所属的切面维度

        Args:
            text: 文本内容

        Returns:
            切面标签或None
        """
        for aspect, keywords in self.aspect_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return aspect
        return None

    async def save_comments(self, task_id: str, bvid: str, comments: List[Dict]) -> int:
        """
        保存评论到数据库并进行情感分析

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
                    (comment_id, task_id, bvid, username, gender,
                     content, like_count, sentiment_score, sentiment_label, aspect, publish_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """

                inserted = 0
                for idx, comment in enumerate(comments):
                    content = comment.get('content', '')
                    if not content:
                        continue

                    # 情感分析
                    score, label = self.calculate_sentiment(content)

                    # 切面检测
                    aspect = self.detect_aspect(content)

                    # 解析时间戳
                    publish_time = None
                    if comment.get('create_time'):
                        try:
                            publish_time = datetime.fromtimestamp(comment['create_time'])
                        except:
                            pass

                    # 使用reply_id作为comment_id主键
                    comment_id = comment.get('reply_id', 0)
                    if not comment_id:
                        comment_id = abs(hash(f"{bvid}_{content}_{inserted}")) % (2**63)

                    cursor.execute(sql, (
                        comment_id,
                        task_id,
                        bvid,
                        comment.get('author', '未知用户'),
                        comment.get('gender', '未知'),
                        content,
                        comment.get('like', 0),
                        score,
                        label,
                        aspect,
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
        保存弹幕到数据库并进行情感分析

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
                    (danmaku_id, task_id, bvid, content, dm_time, appear_time, sentiment_score, sentiment_label)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                inserted = 0
                for idx, dm in enumerate(danmakus):
                    content = dm.get('content', '')
                    if not content:
                        continue

                    # 情感分析
                    score, label = self.calculate_sentiment(content)

                    dm_time = int(dm.get('dm_time', 0))
                    danmaku_id = abs(hash(f"{bvid}_{content}_{dm_time}_{inserted}")) % (2**63)

                    cursor.execute(sql, (
                        danmaku_id,
                        task_id,
                        bvid,
                        content,
                        dm_time,
                        dm_time,  # appear_time = dm_time
                        score,
                        label
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

    async def generate_sentiment_timeline(self, task_id: str, bvid: str) -> Dict:
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
                # 1. 按10秒间隔聚合弹幕情感得分
                logger.debug(f"[{task_id}] 查询弹幕数据生成时间轴")
                sql_timeline = """
                    SELECT
                        FLOOR(dm_time / 10) * 10 as time_bucket,
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
                        'score': round(float(row['avg_score']), 4),
                        'count': row['count']
                    }
                    for row in timeline_rows
                ]
                logger.info(f"[{task_id}] 生成时间轴数据点: {len(timeline)} 个")

                # 2. 计算切面情感得分（基于评论）
                logger.debug(f"[{task_id}] 查询评论数据生成切面分析")
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

                logger.debug(f"[{task_id}] 保存时间轴和切面数据到数据库")
                sql_insert = """
                    INSERT INTO sentiment_timeline (task_id, bvid, timeline_json, aspect_sentiment_json)
                    VALUES (%s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        timeline_json = VALUES(timeline_json),
                        aspect_sentiment_json = VALUES(aspect_sentiment_json)
                """
                cursor.execute(sql_insert, (task_id, bvid, timeline_json, aspect_json))
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
