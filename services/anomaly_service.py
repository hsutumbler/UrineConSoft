# services/anomaly_service.py

from database.connection import DBContext
import json

class AnomalyService:
    
    @staticmethod
    def get_phrases(category: str):
        # 舊系統的 Phrase 沒有分類 (category)，我們全部回傳
        with DBContext() as (conn, cursor):
            cursor.execute(
                "SELECT preId AS template_id, txt AS phrase_text FROM Phrase ORDER BY preId DESC"
            )
            return [{"id": row['template_id'], "text": row['phrase_text']} for row in cursor.fetchall()]

    @staticmethod
    def add_phrase(category: str, phrase_text: str, created_by: int):
        with DBContext() as (conn, cursor):
            cursor.execute(
                "SELECT preId FROM Phrase WHERE txt = %s",
                (phrase_text,)
            )
            if cursor.fetchone():
                return
            cursor.execute(
                "INSERT INTO Phrase (txt) VALUES (%s)",
                (phrase_text,)
            )

    @staticmethod
    def delete_phrase(template_id: int):
        with DBContext() as (conn, cursor):
            cursor.execute("DELETE FROM Phrase WHERE preId = %s", (template_id,))

    @staticmethod
    def update_phrase(template_id: int, phrase_text: str):
        with DBContext() as (conn, cursor):
            cursor.execute(
                "UPDATE Phrase SET txt = %s WHERE preId = %s",
                (phrase_text, template_id)
            )

    @staticmethod
    def get_record_by_result_id(result_id: int):
        with DBContext() as (conn, cursor):
            cursor.execute(
                "SELECT aberrantNO AS serial_number, aberrantNO AS record_id, dqcId AS result_id, "
                "Cause AS anomaly_cause, UserFunction AS corrective_action, "
                "FunctionResult AS corrective_result, Precaution AS preventive_action, "
                "inote1 AS check_items, IncidentTime AS occurrence_time, "
                "mhName AS instrument_name, lot AS qc_lot_number, Err_Lab AS violated_rule "
                "FROM QCaberrant WHERE dqcId = %s",
                (result_id,)
            )
            return cursor.fetchone()

    @staticmethod
    def save_record(data: dict):
        with DBContext() as (conn, cursor):
            cursor.execute("SELECT aberrantNO FROM QCaberrant WHERE dqcId = %s", (data["result_id"],))
            existing = cursor.fetchone()
            
            from datetime import datetime
            now = datetime.now()
            ym = now.strftime("%Y%m")
            
            if existing:
                cursor.execute("""
                    UPDATE QCaberrant 
                    SET Cause = %s, UserFunction = %s, FunctionResult = %s, Precaution = %s, inote1 = %s
                    WHERE dqcId = %s
                """, (
                    data.get("anomaly_cause", ""),
                    data.get("corrective_action", ""),
                    data.get("corrective_result", ""),
                    data.get("preventive_action", ""),
                    data.get("check_items", ""),
                    data["result_id"]
                ))
            else:
                cursor.execute("SELECT COUNT(*) as c FROM QCaberrant WHERE aberrantNO LIKE %s", (f"CE{ym}%",))
                c_row = cursor.fetchone()
                c = c_row['c'] if c_row else 0
                sn = f"CE{ym}{c+1:03d}"
                
                cursor.execute("""
                    INSERT INTO QCaberrant (
                        aberrantNO, dqcId, UserName, mhName, WriteDate, IncidentTime,
                        lot, Err_Lab, Cause, UserFunction, FunctionResult, Precaution, inote1
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    sn, data["result_id"], "Admin", data.get("instrument_name", ""),
                    now, data.get("occurrence_time", now), data.get("qc_lot_number", ""),
                    data.get("violated_rule", ""), data.get("anomaly_cause", ""),
                    data.get("corrective_action", ""), data.get("corrective_result", ""),
                    data.get("preventive_action", ""), data.get("check_items", "")
                ))

    @staticmethod
    def get_all_records(start_date, end_date, instrument_id=None):
        with DBContext() as (conn, cursor):
            query = """
                SELECT a.aberrantNO AS record_id, a.aberrantNO AS serial_number, a.dqcId AS result_id, 
                a.IncidentTime AS occurrence_time, a.mhName AS instrument_name, a.lot AS qc_lot_number,
                a.Err_Lab AS violated_rule, a.Cause AS anomaly_cause, a.UserName AS creator_name,
                r.iDate AS result_date, r.Check_Type AS qualitative_result, r.iValue AS measured_value,
                r.mtId AS reagent_id, rg.mhitem AS reagent_name, l.lot_Level AS qc_level
                FROM QCaberrant a
                LEFT JOIN DailyQC r ON a.dqcId = r.dqcId
                LEFT JOIN MhItem rg ON r.mtId = rg.mtId
                LEFT JOIN LotTable l ON r.lot = l.lot_id
                WHERE a.IncidentTime >= %s AND a.IncidentTime <= %s
            """
            params = [f"{start_date} 00:00:00"]
            
            from datetime import datetime, timedelta
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            ed = (end_date + timedelta(days=1)).strftime("%Y-%m-%d")
            params.append(f"{ed} 23:59:59")
            
            if instrument_id:
                # 舊系統的 QCaberrant 沒有 MhId 或是 r.mhId 可能可以用
                query += " AND (a.MhId = %s OR r.mhId = %s)"
                params.extend([instrument_id, instrument_id])
                
            query += " ORDER BY a.IncidentTime DESC"
            
            cursor.execute(query, tuple(params))
            return cursor.fetchall()
