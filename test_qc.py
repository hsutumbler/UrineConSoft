from database.connection import DBContext
from services.qc_service import ReagentBatchService
from datetime import datetime
import pprint

# Let's check how many qc_results we have for reagent batches
with DBContext() as (conn, cur):
    cur.execute("SELECT result_id, reagent_batch_id, result_date, iqi_id FROM qc_results LIMIT 10")
    pprint.pprint(cur.fetchall())
