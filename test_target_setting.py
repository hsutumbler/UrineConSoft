from database.connection import DBContext
with DBContext() as (conn, cur):
    cur.execute("SELECT * FROM qc_target_settings LIMIT 1")
    print(cur.fetchall())
