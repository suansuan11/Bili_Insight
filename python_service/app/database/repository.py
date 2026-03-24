"""数据库操作模块"""
from typing import List, Dict, Optional
from contextlib import contextmanager
import pymysql.cursors
from .pool import pool


class DatabaseRepository:
    """数据库访问类"""

    @contextmanager
    def get_connection(self):
        """获取数据库连接（上下文管理器）"""
        conn = pool.get_connection()
        try:
            yield conn
        finally:
            conn.close()

    def update_task_progress(self, task_id: int, progress: int, current_step: str, status: str = 'RUNNING'):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度百分比 0-100
            current_step: 当前步骤描述
            status: 任务状态
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = """
                UPDATE analysis_task
                SET progress = %s, current_step = %s, status = %s,
                    completed_at = IF(%s IN ('COMPLETED', 'FAILED'), NOW(), completed_at)
                WHERE task_id = %s
                """
                cursor.execute(sql, (progress, current_step, status, status, task_id))
                conn.commit()
            finally:
                cursor.close()

    def update_task_status(self, task_id: int, status: str, error_message: Optional[str] = None):
        """
        更新任务状态

        Args:
            task_id: 任务ID
            status: 状态
            error_message: 错误信息（可选）
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                if error_message:
                    sql = """
                    UPDATE analysis_task
                    SET status = %s, error_message = %s, completed_at = NOW()
                    WHERE task_id = %s
                    """
                    cursor.execute(sql, (status, error_message, task_id))
                else:
                    sql = """
                    UPDATE analysis_task
                    SET status = %s, completed_at = NOW()
                    WHERE task_id = %s
                    """
                    cursor.execute(sql, (status, task_id))
                conn.commit()
            finally:
                cursor.close()

    def batch_insert_comments(self, task_id: int, bvid: str, comments: List[Dict]):
        """
        批量插入评论

        Args:
            task_id: 任务ID
            bvid: 视频BVID
            comments: 评论列表
        """
        if not comments:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = """
                INSERT INTO video_comment
                (bvid, task_id, username, gender, content, sentiment_score, sentiment_label)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = [
                    (
                        bvid,
                        task_id,
                        c.get('username', ''),
                        c.get('gender', ''),
                        c.get('content', ''),
                        c.get('sentiment_score'),
                        c.get('sentiment_label')
                    )
                    for c in comments
                ]
                cursor.executemany(sql, values)
                conn.commit()
                print(f"成功插入 {len(comments)} 条评论")
            except Exception as e:
                conn.rollback()
                print(f"插入评论失败: {e}")
                raise
            finally:
                cursor.close()

    def batch_insert_danmakus(self, task_id: int, bvid: str, danmakus: List[Dict]):
        """
        批量插入弹幕

        Args:
            task_id: 任务ID
            bvid: 视频BVID
            danmakus: 弹幕列表
        """
        if not danmakus:
            return

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = """
                INSERT INTO video_danmaku
                (bvid, task_id, content, dm_time, appear_time, sentiment_score, sentiment_label)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                values = [
                    (
                        bvid,
                        task_id,
                        d.get('content', ''),
                        d.get('dm_time', 0),
                        d.get('dm_time', 0),
                        d.get('sentiment_score'),
                        d.get('sentiment_label')
                    )
                    for d in danmakus
                ]
                cursor.executemany(sql, values)
                conn.commit()
                print(f"成功插入 {len(danmakus)} 条弹幕")
            except Exception as e:
                conn.rollback()
                print(f"插入弹幕失败: {e}")
                raise
            finally:
                cursor.close()

    def batch_insert_timeline(self, task_id: int, bvid: str, timeline_data: Dict):
        """
        插入时间轴数据（JSON格式）

        Args:
            task_id: 任务ID
            bvid: 视频BVID（保留参数兼容性，但不使用）
            timeline_data: 时间轴数据字典 {'timeline': [...], 'aspect_sentiment': {...}}
        """
        if not timeline_data:
            return

        import json

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 新表结构：使用JSON存储
                sql = """
                INSERT INTO sentiment_timeline
                (task_id, timeline_json, aspect_sentiment_json)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    timeline_json = VALUES(timeline_json),
                    aspect_sentiment_json = VALUES(aspect_sentiment_json)
                """

                # 转换为JSON字符串
                timeline_json = json.dumps(timeline_data.get('timeline', []))
                aspect_json = json.dumps(timeline_data.get('aspect_sentiment', {}))

                cursor.execute(sql, (task_id, timeline_json, aspect_json))
                conn.commit()
                timeline_count = len(timeline_data.get('timeline', []))
                print(f"成功插入时间轴数据（{timeline_count} 个数据点）")
            except Exception as e:
                conn.rollback()
                print(f"插入时间轴数据失败: {e}")
                raise
            finally:
                cursor.close()

    def get_task_info(self, task_id: int) -> Optional[Dict]:
        """
        获取任务信息

        Args:
            task_id: 任务ID

        Returns:
            任务信息字典或None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                sql = "SELECT * FROM analysis_task WHERE task_id = %s"
                cursor.execute(sql, (task_id,))
                return cursor.fetchone()
            finally:
                cursor.close()

    def clear_all_popular_videos(self):
        """清空所有热门视频"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = "DELETE FROM popular_videos"
                cursor.execute(sql)
                conn.commit()
                print(f"已清空 {cursor.rowcount} 个视频")
            finally:
                cursor.close()

    def insert_or_update_popular_video(self, video_info: Dict):
        """
        插入或更新热门视频信息

        Args:
            video_info: 视频信息字典，包含 bvid, title, author, author_mid 等字段
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                sql = """
                INSERT INTO popular_videos
                (bvid, aid, title, description, author, publish_date, duration,
                 view_count, like_count, coin_count, favorite_count, share_count,
                 danmaku_count, comment_count, cover_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    title = VALUES(title),
                    description = VALUES(description),
                    view_count = VALUES(view_count),
                    like_count = VALUES(like_count),
                    coin_count = VALUES(coin_count),
                    favorite_count = VALUES(favorite_count),
                    share_count = VALUES(share_count),
                    danmaku_count = VALUES(danmaku_count),
                    comment_count = VALUES(comment_count),
                    scraped_at = CURRENT_TIMESTAMP
                """

                # 兼容两种数据格式：B站API原始格式 和 爬虫脚本格式
                if 'owner' in video_info:
                    # B站API原始格式
                    author = video_info.get('owner', {}).get('name')
                    view_count = video_info.get('stat', {}).get('view')
                    like_count = video_info.get('stat', {}).get('like')
                    coin_count = video_info.get('stat', {}).get('coin')
                    favorite_count = video_info.get('stat', {}).get('favorite')
                    share_count = video_info.get('stat', {}).get('share')
                    danmaku_count = video_info.get('stat', {}).get('danmaku')
                    comment_count = video_info.get('comment_count', 0) # Already extracted in service
                    if not comment_count: # Fallback if direct not available (raw api response)
                         comment_count = video_info.get('stat', {}).get('reply', 0)

                    cover_url = video_info.get('pic')
                    publish_date = video_info.get('pubdate')
                else:
                    # 爬虫脚本格式 (已处理好的字段)
                    author = video_info.get('author')
                    view_count = video_info.get('view_count')
                    like_count = video_info.get('like_count')
                    coin_count = video_info.get('coin_count')
                    favorite_count = video_info.get('favorite_count')
                    share_count = video_info.get('share_count')
                    danmaku_count = video_info.get('danmaku_count')
                    comment_count = video_info.get('comment_count')
                    cover_url = video_info.get('cover_url')
                    publish_date = video_info.get('publish_date')

                # Ensure publish_date is formatted properly for MySQL if it's a timestamp
                import datetime
                if isinstance(publish_date, int):
                    publish_date = datetime.datetime.fromtimestamp(publish_date).strftime('%Y-%m-%d %H:%M:%S')
                elif not publish_date:
                    publish_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                cursor.execute(sql, (
                    video_info.get('bvid'),
                    video_info.get('aid', 0),
                    video_info.get('title'),
                    video_info.get('description', ''),
                    author,
                    publish_date,
                    video_info.get('duration', 0),
                    view_count or 0,
                    like_count or 0,
                    coin_count or 0,
                    favorite_count or 0,
                    share_count or 0,
                    danmaku_count or 0,
                    comment_count or 0,
                    cover_url
                ))
                conn.commit()
            except Exception as e:
                conn.rollback()
                print(f"插入热门视频失败: {e}")
                raise
            finally:
                cursor.close()

    def get_popular_videos(self, limit: int = 20) -> List[Dict]:
        """
        获取热门视频列表

        Args:
            limit: 返回数量限制

        Returns:
            热门视频列表
        """
        with self.get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                sql = """
                SELECT bvid, title, author, cover_url, view_count, like_count,
                       coin_count, favorite_count, share_count,
                       danmaku_count, comment_count, publish_date, scraped_at as created_at
                FROM popular_videos
                ORDER BY view_count DESC, scraped_at DESC
                LIMIT %s
                """
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
            finally:
                cursor.close()
