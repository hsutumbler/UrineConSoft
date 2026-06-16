import logging
import os
from datetime import datetime

def get_logger(name="UrineConSoft"):
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        
    # 以「年_月」為檔名，例如 app_2026_06.log，達成一個月一個檔案的需求
    current_month = datetime.now().strftime("%Y_%m")
    log_filename = os.path.join(log_dir, f"app_{current_month}.log")
    
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
        
        file_handler = logging.FileHandler(log_filename, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
    return logger

# 提供全域 logger 實例
logger = get_logger()
