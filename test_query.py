from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("SELECT * FROM reagent_batches")
    batches = cur.fetchall()
    print("Batches:", batches)
    
    cur.execute("SELECT lot, lot_id, lot_Level FROM LotTable")
    print("LotTable:", cur.fetchall())

    cur.execute("SELECT lot, mtId, iDate FROM DailyQC LIMIT 10")
    print("DailyQC:", cur.fetchall())
