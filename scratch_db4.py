import sys
import os
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("""
        SELECT r.result_id, r.result_date, b.lot_number, r.iqi_id 
        FROM qc_results r 
        JOIN qc_batches b ON r.qc_batch_id = b.batch_id 
        WHERE b.lot_number = 'UQC060101' 
        ORDER BY r.result_date DESC LIMIT 20
    """)
    for r in cur.fetchall():
        print(f"Lot: {r['lot_number']}, IQI: {r['iqi_id']}, Date: {r['result_date']}")
