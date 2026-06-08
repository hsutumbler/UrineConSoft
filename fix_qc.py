from database.connection import DBContext
from services.qc_service import QCResultService, TargetSettingService

def fix_all():
    with DBContext() as (conn, cur):
        cur.execute("SELECT result_id, iqi_id, result_date, measured_value, qualitative_result, qc_batch_id FROM qc_results")
        rows = cur.fetchall()
        
        updates = 0
        for r in rows:
            if r["measured_value"] is not None and r["qc_batch_id"] is not None:
                # Re-evaluate
                from services.qc_service import QCResultService
                is_acc, flag = QCResultService._check_westgard(
                    r["iqi_id"], r["result_date"], 
                    float(r["measured_value"]), r["qualitative_result"],
                    r["qc_batch_id"]
                )
                
                cur.execute(
                    "UPDATE qc_results SET is_accepted=%s, westgard_flag=%s WHERE result_id=%s",
                    (is_acc, flag, r["result_id"])
                )
                updates += 1
        conn.commit()
        print(f"Fixed {updates} quantitative records.")

if __name__ == '__main__':
    fix_all()
