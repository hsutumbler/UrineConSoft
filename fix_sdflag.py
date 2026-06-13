from database.connection import DBContext
from services.qc_service import QCResultService, TargetSettingService
from datetime import datetime

with DBContext() as (conn, cur):
    cur.execute("SELECT dqcId, mtId, lot, iDate, iValue, Check_Type FROM DailyQC")
    records = cur.fetchall()
    
    # Pre-fetch lot levels and batch ids
    cur.execute("SELECT lot, lot_Level, lot_id FROM LotTable")
    lot_map = {}
    for r in cur.fetchall():
        lot_map[r["lot_id"]] = r
        
    updated = 0
    for rec in records:
        dqcId = rec["dqcId"]
        mtId = str(rec["mtId"])
        lot = rec["lot"]
        
        lot_info = lot_map.get(lot)
        if not lot_info: continue
        
        level = str(lot_info["lot_Level"] or 1)
        batch_id = lot_info["lot_id"]
        iqi_id = f"{mtId}_{level}"
        
        # Manually evaluate
        is_accepted = True
        
        ts = TargetSettingService.get_for_batch(iqi_id, batch_id)
        if ts:
            if ts["tm"] is not None and ts["tsd"] is not None:
                # Quantitative
                val = rec["iValue"]
                if val is not None and val != -1.0: # -1.0 is sometimes empty
                    tm = float(ts["tm"])
                    tsd = float(ts["tsd"])
                    tea = ts.get("tea", None)
                    if tea is not None and tea > 0:
                        limit = tm * (tea / 100.0)
                        if abs(val - tm) > limit:
                            is_accepted = False
                    else:
                        if abs(val - tm) > 2 * tsd:
                            is_accepted = False
            elif ts.get("semi_target_min"):
                # Semi-quantitative
                qual = rec["Check_Type"]
                if qual:
                    levels = {"Neg": 0, "Norm": 1, "Trace": 2, "Pos": 3, "1+": 4, "2+": 5, "3+": 6, "4+": 7}
                    
                    s_min = ts.get("semi_target_min")
                    s_max = ts.get("semi_target_max")
                    
                    if s_min and s_max and qual in levels:
                        val = levels[qual]
                        if s_min in levels and s_max in levels:
                            min_val = levels[s_min]
                            max_val = levels[s_max]
                            if val < min_val or val > max_val:
                                is_accepted = False
                        else:
                            is_accepted = False
        
        sdFlag = 0 if is_accepted else 1
        
        cur.execute("UPDATE DailyQC SET sdFlag = %s WHERE dqcId = %s", (sdFlag, dqcId))
        updated += 1

    conn.commit()
    print(f"sdFlag fixed! {updated} records updated.")
