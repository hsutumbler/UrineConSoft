from database.connection import DBContext

with DBContext() as (_, cur):
    cur.execute("SELECT batch_id, lot_number FROM reagent_batches")
    rb = cur.fetchall()
    print("Reagent Batches:", rb)
    
    cur.execute("SELECT DISTINCT lot FROM DailyQC")
    dqc_lots = cur.fetchall()
    print("DailyQC Lots:", dqc_lots)
