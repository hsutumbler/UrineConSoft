import sys
import os
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("SELECT result_id, result_date FROM qc_results ORDER BY result_id DESC LIMIT 10")
    for r in cur.fetchall():
        print(f"ID: {r['result_id']}, Date: {r['result_date']}")
