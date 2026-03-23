"""数据库连接池模块"""
from dbutils.pooled_db import PooledDB
import pymysql
from ..config import settings

class ConnectionPool:
    _instance = None
    _pool = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._pool is None:
            self._pool = PooledDB(
                creator=pymysql,
                maxconnections=10,
                mincached=2,
                maxcached=5,
                blocking=True,
                ping=1,
                host=settings.db_host,
                port=settings.db_port,
                user=settings.db_user,
                password=settings.db_password,
                database=settings.db_name,
                charset='utf8mb4',
                connect_timeout=5
            )

    def get_connection(self):
        return self._pool.connection()

pool = ConnectionPool()
