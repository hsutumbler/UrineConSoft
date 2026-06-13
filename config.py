# config.py — UrineConSoft 設定
# 請依實際環境修改以下設定

# 系統環境設定: 'TEST' 或 'PROD' (主要影響除錯模式或後續其它設定)
ENV = "PROD"

# 本地 MySQL 設定 (測試用)
DB_CONFIG = {
    "host":               "127.0.0.1",
    "port":               3306,
    "user":               "qc_user",
    "password":           "qc_pass",
    "database":           "qc_system",
    "charset":            "utf8mb4",
    "connection_timeout": 10,
}

# 院方 SQL Server 設定 (PROD 模式使用)
MSSQL_CONFIG = {
    "server": "10.9.8.100",
    "user": "hitsrv",
    "password": "hitsrv",
    "database": "ULink",
    "charset": "utf8",
    "login_timeout": 5,
}

POOL_CONFIG = {
    "pool_name":          "qc_pool",
    "pool_size":          5,
    "pool_reset_session": True,
}

APP_NAME    = "UrineConSoft 品管系統"
APP_VERSION = "1.0.0"

import platform
IS_MAC = platform.system() == "Darwin"
DEFAULT_FONT = "PingFang TC" if IS_MAC else "Microsoft JhengHei"

# 儀器傳輸監聽資料夾（File Drop）
INSTRUMENT_WATCH_DIR = "instrument_data"
