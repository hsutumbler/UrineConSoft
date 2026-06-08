import sys
import os
from datetime import date
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext

with DBContext() as (_, cur):
    cur.execute("""
        SELECT r.result_date, r.entered_at, r.iqi_id
        FROM qc_results r 
        JOIN qc_batches b ON r.qc_batch_id = b.batch_id 
        WHERE b.lot_number = 'UQC060101' AND r.iqi_id = 23
        ORDER BY r.result_date ASC, r.entered_at ASC
    """)
    for r in cur.fetchall():
        print(f"Date: {r['result_date']}, Entered: {r['entered_at']}")
