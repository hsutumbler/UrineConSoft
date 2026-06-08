import sys
import os
sys.path.append(os.path.abspath('.'))

import random
from datetime import datetime, timedelta
from database.connection import DBContext
from services.qc_service import QCResultService, TargetSettingService, QCBatchService

def get_batch_by_lot(lot_number):
    with DBContext() as (_, cur):
        cur.execute("SELECT batch_id FROM qc_batches WHERE lot_number=%s", (lot_number,))
        res = cur.fetchone()
        return res["batch_id"] if res else None

def main():
    lots = {
        "Level 1": ["UQC01", "UQC060101"],
        "Level 2": ["UQC02", "UQC060102"]
    }
    
    with DBContext() as (_, cur):
        cur.execute("""
            SELECT iqi.iqi_id, iqi.level_id, r.param_type 
            FROM instrument_qc_items iqi
            JOIN qc_levels l ON iqi.level_id = l.level_id
            JOIN reagents r ON l.reagent_id = r.reagent_id
        """)
        iqis = cur.fetchall()
        
        cur.execute("SELECT level_id, level_name FROM qc_levels")
        level_map = {r["level_id"]: r["level_name"] for r in cur.fetchall()}
        
    for iqi in iqis:
        iqi_id = iqi["iqi_id"]
        level_name = level_map[iqi["level_id"]]
        param_type = iqi["param_type"]
        
        ts = TargetSettingService.get_current(iqi_id)
        if not ts:
            continue
            
        for lot in lots.get(level_name, []):
            batch_id = get_batch_by_lot(lot)
            if not batch_id:
                continue
                
            base_date = datetime.now() - timedelta(days=5)
            for i in range(5):
                q_date = base_date + timedelta(days=i)
                mval = None
                qual = None
                
                if param_type == 1: # 定量
                    if ts["tm"] is not None and ts["tsd"] is not None:
                        tm = float(ts["tm"])
                        tsd = float(ts["tsd"])
                        # Generate value around tm, occasionally outside 2SD (about 10% chance)
                        if random.random() < 0.1:
                            mval = tm + random.choice([2.5, -2.5, 3.0, -3.0]) * tsd
                        else:
                            mval = tm + random.uniform(-1.5, 1.5) * tsd
                        mval = round(mval, 3)
                    else:
                        mval = 1.0
                elif param_type == 2: # 定性
                    # Just pick a random semi-quant value
                    semi_opts = ["Neg", "Trace", "1+", "2+", "3+", "4+"]
                    qual = random.choice(semi_opts)
                    
                QCResultService.save_result(
                    iqi_id=iqi_id,
                    result_date=q_date,
                    reagent_batch_id=None,
                    qc_batch_id=batch_id,
                    measured_value=mval,
                    qualitative_result=qual,
                    notes="Test Data",
                    entered_by=1,
                    source=1
                )

if __name__ == "__main__":
    main()
    print("Test data inserted successfully.")
