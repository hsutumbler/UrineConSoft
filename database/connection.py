# database/connection.py — 資料庫連線管理 (雙資料庫模式)

import config
from config import DB_CONFIG, POOL_CONFIG, MSSQL_CONFIG

class MockRow(dict):
    def __missing__(self, key):
        return None
    def get(self, key, default=None):
        if key in self:
            return super().get(key)
        return self.__missing__(key)

class MockCursor:
    def __init__(self, dictionary=True, as_dict=True):
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
    def cursor(self, dictionary=True, as_dict=True):
        return MockCursor(dictionary=dictionary, as_dict=as_dict)
    def commit(self): pass
    def rollback(self): pass
    def close(self): pass


class DatabasePool:
    """管理 MySQL 的連線池"""
    _mysql_pool = None
    _offline_mode = False

    @classmethod
    def set_offline_mode(cls, offline: bool):
        cls._offline_mode = offline
        if offline:
            cls._mysql_pool = None

    @classmethod
    def get_mysql_connection(cls):
        if cls._offline_mode:
            return MockConnection()
        try:
            import mysql.connector
            from mysql.connector import pooling
            if cls._mysql_pool is None:
                cls._mysql_pool = pooling.MySQLConnectionPool(
                    **POOL_CONFIG, **DB_CONFIG
                )
            return cls._mysql_pool.get_connection()
        except Exception as e:
            print(f"MySQL Connection Error: {e}")
            cls._offline_mode = True
            return MockConnection()

    @classmethod
    def get_mssql_connection(cls):
        if cls._offline_mode:
            return MockConnection()
        try:
            import pymssql
            return pymssql.connect(
                server=MSSQL_CONFIG['server'],
                user=MSSQL_CONFIG['user'],
                password=MSSQL_CONFIG['password'],
                database=MSSQL_CONFIG['database'],
                charset=MSSQL_CONFIG.get('charset', 'utf8'),
                login_timeout=MSSQL_CONFIG.get('login_timeout', 5)
            )
        except Exception as e:
            print(f"MSSQL Connection Error: {e}")
            # 不強制切換為 offline，避免單邊斷線影響另一邊
            return MockConnection()

    @classmethod
    def close_pool(cls):
        if cls._mysql_pool:
            cls._mysql_pool = None


class DBContext:
    """
    主要操作的 MySQL Context (qc_system)
    使用方式：
        with DBContext() as (conn, cursor):
            cursor.execute(...)
    """
    def __init__(self, dictionary=True):
        self._dictionary = dictionary
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = DatabasePool.get_mysql_connection()
        if isinstance(self._conn, MockConnection):
            self._cursor = self._conn.cursor(dictionary=self._dictionary)
        else:
            self._cursor = self._conn.cursor(dictionary=self._dictionary, buffered=True)
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


class ReadOnlyCursorWrapper:
    """強制攔截任何寫入指令的 Cursor 包裝器"""
    def __init__(self, cursor):
        self._cursor = cursor

    def _check_readonly(self, sql):
        sql_upper = sql.upper().strip()
        forbidden_keywords = ("INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "CREATE", "TRUNCATE", "REPLACE", "MERGE")
        if any(sql_upper.startswith(kw) or f" {kw} " in sql_upper for kw in forbidden_keywords):
            raise PermissionError(f"【嚴重警告】絕對禁止對 MS SQL 執行寫入操作: {sql}")

    def execute(self, sql, params=None):
        self._check_readonly(sql)
        if params:
            return self._cursor.execute(sql, params)
        return self._cursor.execute(sql)

    def executemany(self, sql, params):
        self._check_readonly(sql)
        return self._cursor.executemany(sql, params)

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class MSSQLContext:
    """
    讀取原始資料的 MS SQL Context (ULink) - 絕對唯讀
    使用方式：
        with MSSQLContext() as (conn, cursor):
            cursor.execute("SELECT ...")
    """
    def __init__(self, as_dict=True):
        self._as_dict = as_dict
        self._conn = None
        self._cursor = None

    def __enter__(self):
        self._conn = DatabasePool.get_mssql_connection()
        raw_cursor = self._conn.cursor(as_dict=self._as_dict)
        self._cursor = ReadOnlyCursorWrapper(raw_cursor)
        return self._conn, self._cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn is not None and self._cursor is not None:
            # 絕對唯讀，不需要 commit，一律 rollback 以防萬一有隱含的 transaction
            self._conn.rollback()
            self._cursor.close()
            self._conn.close()
        return False


def test_connection() -> bool:
    """測試兩個資料庫的連線狀態"""
    mysql_ok = False
    mssql_ok = False
    
    # Test MySQL
    try:
        import mysql.connector
        from mysql.connector import pooling
        pool = pooling.MySQLConnectionPool(**POOL_CONFIG, **DB_CONFIG)
        conn = pool.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS ok")
        cursor.fetchone()
        cursor.close()
        conn.close()
        DatabasePool._mysql_pool = pool
        mysql_ok = True
    except Exception as e:
        print(f"[❌ MySQL 連線失敗] {e}")
        DatabasePool._mysql_pool = None

    # Test MSSQL
    try:
        import pymssql
        conn = pymssql.connect(
            server=MSSQL_CONFIG['server'],
            user=MSSQL_CONFIG['user'],
            password=MSSQL_CONFIG['password'],
            database=MSSQL_CONFIG['database'],
            charset=MSSQL_CONFIG.get('charset', 'utf8'),
            login_timeout=MSSQL_CONFIG.get('login_timeout', 5)
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS ok")
        cursor.fetchone()
        cursor.close()
        conn.close()
        mssql_ok = True
    except Exception as e:
        print(f"[❌ MSSQL 連線失敗] {e}")
        
    if mysql_ok:
        DatabasePool._offline_mode = False
        if not mssql_ok:
            print("[⚠️ 注意] MySQL 成功，但 MSSQL 失敗，部分同步功能將受限。")
        return True
    else:
        DatabasePool._offline_mode = True
        return False
