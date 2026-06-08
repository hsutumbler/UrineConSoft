# config.py — UrineConSoft 設定
# 請依實際環境修改以下設定

DB_CONFIG = {
    "host":               "127.0.0.1",
    "port":               3306,
    "user":               "qc_user",
    "password":           "qc_pass",
    "database":           "qc_system",
    "charset":            "utf8mb4",
    "connection_timeout": 10,
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
