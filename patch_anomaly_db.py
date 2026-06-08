import sqlite3
import os

DB_PATH = 'database/urine_con.db'
SCHEMA_PATH = 'database/schema.sql'

def patch_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 建立異常紀錄表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS qc_anomaly_records (
        record_id INTEGER PRIMARY KEY AUTOINCREMENT,
        result_id INTEGER NOT NULL,
        anomaly_data VARCHAR(100),
        occurrence_time DATETIME,
        instrument_name VARCHAR(50),
        qc_lot_number VARCHAR(50),
        qc_level VARCHAR(20),
        violated_rule VARCHAR(50),
        anomaly_cause TEXT,
        corrective_action TEXT,
        corrective_result TEXT,
        preventive_action TEXT,
        created_by INTEGER NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (result_id) REFERENCES qc_results(result_id) ON DELETE CASCADE,
        FOREIGN KEY (created_by) REFERENCES users(user_id)
    )
    """)
    
    # 建立片語表
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS phrase_templates (
        template_id INTEGER PRIMARY KEY AUTOINCREMENT,
        category VARCHAR(50) NOT NULL,
        phrase_text TEXT NOT NULL,
        created_by INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print("Database patched successfully.")

def patch_schema():
    with open(SCHEMA_PATH, 'a', encoding='utf-8') as f:
        f.write("\n\n-- ------------------------------------------------------------\n")
        f.write("-- 品管異常紀錄與片語\n")
        f.write("-- ------------------------------------------------------------\n\n")
        
        f.write("""CREATE TABLE IF NOT EXISTS qc_anomaly_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    anomaly_data VARCHAR(100),
    occurrence_time DATETIME,
    instrument_name VARCHAR(50),
    qc_lot_number VARCHAR(50),
    qc_level VARCHAR(20),
    violated_rule VARCHAR(50),
    anomaly_cause TEXT,
    corrective_action TEXT,
    corrective_result TEXT,
    preventive_action TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES qc_results(result_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) COMMENT='品管異常紀錄';\n\n""")

        f.write("""CREATE TABLE IF NOT EXISTS phrase_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    phrase_text TEXT NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='輸入片語範本';\n""")
        
    print("Schema.sql updated.")

if __name__ == '__main__':
    patch_db()
    patch_schema()
