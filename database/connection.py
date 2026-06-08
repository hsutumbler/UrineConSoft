# database/connection.py — MySQL 連線池管理

import mysql.connector
from mysql.connector import pooling, Error
from config import DB_CONFIG, POOL_CONFIG


class MockRow(dict):
    def __missing__(self, key):
        return None

    def get(self, key, default=None):
        if key in self:
            return super().get(key)
        return self.__missing__(key)


class MockCursor:
    def __init__(self, dictionary=True):
        self.dictionary = dictionary
        self.lastrowid = 1
        self.rowcount = 0
        self._last_sql = ""

    def execute(self, sql, params=None):
        self._last_sql = sql.upper() if sql else ""

    def fetchone(self):
        if any(x in self._last_sql for x in ("COUNT(", "MAX(", "MIN(", "SUM(", "AVG(")):
            return MockRow()
        return None

    def fetchall(self):
        return []

    def close(self):
        pass


class MockConnection:
    def cursor(self, dictionary=True):
        return MockCursor(dictionary=dictionary)

    def commit(self):
        pass

    def rollback(self):
        pass

    def close(self):
        pass


class DatabasePool:
    _pool: pooling.MySQLConnectionPool | None = None
    _offline_mode: bool = False

    @classmethod
    def set_offline_mode(cls, offline: bool):
        cls._offline_mode = offline
        if offline:
            cls._pool = None

    @classmethod
    def get_pool(cls) -> pooling.MySQLConnectionPool:
        if cls._offline_mode:
            raise ConnectionError("目前處於離線模式。")
        if cls._pool is None:
            try:
                cls._pool = pooling.MySQLConnectionPool(
                    **POOL_CONFIG, **DB_CONFIG,
                )
            except Error as e:
                raise ConnectionError(f"無法建立資料庫連線池：{e}") from e
        return cls._pool

    @classmethod
    def get_connection(cls):
        if cls._offline_mode:
            return MockConnection()
        try:
            return cls.get_pool().get_connection()
        except Exception:
            cls._offline_mode = True
            return MockConnection()

    @classmethod
    def close_pool(cls):
        if cls._pool:
            cls._pool = None


class DBContext:
    """
    使用方式：
        with DBContext() as (conn, cursor):
            cursor.execute(...)
    """
    def __init__(self, dictionary=True):
        self._dictionary = dictionary
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = DatabasePool.get_connection()
        self._cursor = self._conn.cursor(dictionary=self._dictionary)
        return self._conn, self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None and self._cursor is not None:
            if exc_type is None:
                self._conn.commit()
            else:
                self._conn.rollback()
            self._cursor.close()
            self._conn.close()
        return False


def test_connection() -> bool:
    try:
        pool = pooling.MySQLConnectionPool(**POOL_CONFIG, **DB_CONFIG)
        conn = pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS ok")
        cursor.fetchone()
        cursor.close()
        conn.close()
        DatabasePool._pool = pool
        DatabasePool._offline_mode = False
        return True
    except Exception as e:
        print(f"[❌ 連線失敗] {e}")
        DatabasePool._offline_mode = True
        DatabasePool._pool = None
        return False
