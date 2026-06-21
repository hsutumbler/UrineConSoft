import os
import sys
import platform
import configparser

# 取得執行檔或腳本所在目錄，以確保設定檔與執行檔放在同一層
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

INI_PATH = os.path.join(BASE_DIR, "settings.ini")
config_parser = configparser.ConfigParser()

# 系統環境設定: 'TEST' 或 'PROD' (主要影響除錯模式或後續其它設定)
ENV = "PROD"

# 預設本地 MySQL 設定 (測試用)
DB_CONFIG = {
    "host":               "127.0.0.1",
    "port":               3306,
    "user":               "urine_admin",
    "password":           "12345678",
    "database":           "qc_system",
    "charset":            "utf8mb4",
    "connection_timeout": 10,
    "use_pure":           True,
}

# 預設院方 SQL Server 設定 (PROD 模式使用)
MSSQL_CONFIG = {
    "server": "10.9.8.100",
    "user": "hitsrv",
    "password": "hitsrv",
    "database": "ULink",
    "charset": "utf8",
    "login_timeout": 5,
}

# 讀取外部設定檔 (若不存在則自動建立)
if os.path.exists(INI_PATH):
    config_parser.read(INI_PATH, encoding='utf-8')
    if 'MySQL' in config_parser:
        DB_CONFIG['host'] = config_parser.get('MySQL', 'host', fallback=DB_CONFIG['host'])
        DB_CONFIG['user'] = config_parser.get('MySQL', 'user', fallback=DB_CONFIG['user'])
        DB_CONFIG['password'] = config_parser.get('MySQL', 'password', fallback=DB_CONFIG['password'])
        DB_CONFIG['database'] = config_parser.get('MySQL', 'database', fallback=DB_CONFIG['database'])
        DB_CONFIG['port'] = config_parser.getint('MySQL', 'port', fallback=DB_CONFIG['port'])
    if 'MSSQL' in config_parser:
        MSSQL_CONFIG['server'] = config_parser.get('MSSQL', 'server', fallback=MSSQL_CONFIG['server'])
        MSSQL_CONFIG['user'] = config_parser.get('MSSQL', 'user', fallback=MSSQL_CONFIG['user'])
        MSSQL_CONFIG['password'] = config_parser.get('MSSQL', 'password', fallback=MSSQL_CONFIG['password'])
        MSSQL_CONFIG['database'] = config_parser.get('MSSQL', 'database', fallback=MSSQL_CONFIG['database'])
else:
    # 建立預設 settings.ini 讓使用者未來可以直接修改
    config_parser['MySQL'] = {
        'host': DB_CONFIG['host'],
        'port': str(DB_CONFIG['port']),
        'user': DB_CONFIG['user'],
        'password': DB_CONFIG['password'],
        'database': DB_CONFIG['database'],
    }
    config_parser['MSSQL'] = {
        'server': MSSQL_CONFIG['server'],
        'user': MSSQL_CONFIG['user'],
        'password': MSSQL_CONFIG['password'],
        'database': MSSQL_CONFIG['database'],
    }
    try:
        with open(INI_PATH, 'w', encoding='utf-8') as f:
            config_parser.write(f)
    except Exception:
        pass

POOL_CONFIG = {
    "pool_name":          "qc_pool",
    "pool_size":          5,
    "pool_reset_session": True,
}

APP_NAME = "尿液品管系統"
APP_VERSION = "1.0.0"

IS_MAC = platform.system() == "Darwin"
DEFAULT_FONT = "PingFang TC" if IS_MAC else "Microsoft JhengHei"

# 儀器傳輸監聽資料夾（File Drop）
INSTRUMENT_WATCH_DIR = "instrument_data"
