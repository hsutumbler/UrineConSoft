# services/anomaly_service.py

from database.connection import DBContext
import json

class AnomalyService:
    
    @staticmethod
    def get_phrases(category: str):
        with DBContext() as (conn, cursor):
            cursor.execute(
                "SELECT template_id, phrase_text FROM phrase_templates WHERE category = %s ORDER BY template_id DESC",
                (category,)
            )
            return [{"id": row['template_id'], "text": row['phrase_text']} for row in cursor.fetchall()]

    @staticmethod
    def add_phrase(category: str, phrase_text: str, created_by: int):
        with DBContext() as (conn, cursor):
            # 檢查是否已存在
            cursor.execute(
                "SELECT template_id FROM phrase_templates WHERE category = %s AND phrase_text = %s",
                (category, phrase_text)
            )
            if cursor.fetchone():
                return
            cursor.execute(
                "INSERT INTO phrase_templates (category, phrase_text, created_by) VALUES (%s, %s, %s)",
                (category, phrase_text, created_by)
            )

    @staticmethod
    def delete_phrase(template_id: int):
        with DBContext() as (conn, cursor):
            cursor.execute("DELETE FROM phrase_templates WHERE template_id = %s", (template_id,))

    @staticmethod
    def get_record_by_result_id(result_id: int):
        with DBContext() as (conn, cursor):
            cursor.execute(
                "SELECT * FROM qc_anomaly_records WHERE result_id = %s",
                (result_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def save_record(data: dict):
        with DBContext() as (conn, cursor):
            # 檢查是否已經有這個 result_id 的紀錄
            cursor.execute("SELECT record_id FROM qc_anomaly_records WHERE result_id = %s", (data["result_id"],))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE qc_anomaly_records 
                    SET anomaly_cause = %s, corrective_action = %s, corrective_result = %s, preventive_action = %s, check_items = %s
                    WHERE record_id = %s
                """, (
                    data.get("anomaly_cause", ""),
                    data.get("corrective_action", ""),
                    data.get("corrective_result", ""),
                    data.get("preventive_action", ""),
                    data.get("check_items", ""),
                    existing['record_id']
                ))
            else:
                from datetime import datetime
                now = datetime.now()
                ym = now.strftime("%Y%m")
                cursor.execute("SELECT COUNT(*) as c FROM qc_anomaly_records WHERE serial_number LIKE %s", (f"CE{ym}%",))
                c_row = cursor.fetchone()
                c = c_row['c'] if c_row else 0
                sn = f"CE{ym}{c+1:03d}"
                
                cursor.execute("""
                    INSERT INTO qc_anomaly_records (
                        result_id, anomaly_data, occurrence_time, instrument_name,
                        qc_lot_number, qc_level, violated_rule, 
                        anomaly_cause, corrective_action, corrective_result, preventive_action,
                        check_items, created_by, serial_number
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    data["result_id"], data.get("anomaly_data", ""), data.get("occurrence_time", ""),
                    data.get("instrument_name", ""), data.get("qc_lot_number", ""), data.get("qc_level", ""),
                    data.get("violated_rule", ""), data.get("anomaly_cause", ""),
                    data.get("corrective_action", ""), data.get("corrective_result", ""),
                    data.get("preventive_action", ""), data.get("check_items", ""), data["created_by"], sn
                ))

    @staticmethod
    def get_all_records(start_date, end_date, instrument_id=None):
        with DBContext() as (conn, cursor):
            query = """
                SELECT a.*, u.name as creator_name, r.result_date, r.qualitative_result, r.measured_value, iqi.reagent_id, rg.reagent_name
                FROM qc_anomaly_records a
                LEFT JOIN users u ON a.created_by = u.user_id
                LEFT JOIN qc_results r ON a.result_id = r.result_id
                LEFT JOIN instrument_qc_items iqi ON r.iqi_id = iqi.iqi_id
                LEFT JOIN reagents rg ON iqi.reagent_id = rg.reagent_id
                WHERE a.occurrence_time >= %s AND a.occurrence_time <= %s
            """
            params = [start_date]
            
            from datetime import datetime, timedelta
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            ed = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
            params.append(ed)
            
            if instrument_id:
                query += " AND iqi.instrument_id = %s"
                params.append(instrument_id)
                
            query += " ORDER BY a.occurrence_time DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
