import sys
import os
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("SHOW COLUMNS FROM qc_results LIKE 'result_date'")
    print(cur.fetchone())
