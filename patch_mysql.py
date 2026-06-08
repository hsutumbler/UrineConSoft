from database.connection import DBContext

def patch_mysql_db():
    with DBContext() as (conn, cursor):
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS qc_anomaly_records (
            record_id INT AUTO_INCREMENT PRIMARY KEY,
            result_id INT NOT NULL,
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
            created_by INT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (result_id) REFERENCES qc_results(result_id) ON DELETE CASCADE,
            FOREIGN KEY (created_by) REFERENCES users(user_id)
        ) COMMENT='品管異常紀錄'
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS phrase_templates (
            template_id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            phrase_text TEXT NOT NULL,
            created_by INT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ) COMMENT='輸入片語範本'
        """)
        print("MySQL Database patched successfully.")

if __name__ == '__main__':
    patch_mysql_db()
