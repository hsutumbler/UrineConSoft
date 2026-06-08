import sys
import os
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("SELECT result_id, result_date, qc_batch_id FROM qc_results ORDER BY result_date ASC LIMIT 20")
    for r in cur.fetchall():
        print(f"ID: {r['result_id']}, Date: {r['result_date']}")
