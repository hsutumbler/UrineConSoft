from database.connection import DBContext
with DBContext() as (_, cur):
    cur.execute("SELECT * FROM qc_batch_acceptance")
    rows = cur.fetchall()
    print("COUNT:", len(rows))
    for r in rows:
        print(r)
