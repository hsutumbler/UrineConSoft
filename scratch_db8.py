import sys
import os
sys.path.append(os.path.abspath('.'))
from database.connection import DBContext

with DBContext() as (_, cur):
    cur.execute("DELETE FROM qc_results WHERE notes='Test Data'")
