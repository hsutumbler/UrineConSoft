from database.connection import DBContext

with DBContext() as (_, cur):
    cur.execute("SELECT DISTINCT iDate, lot FROM DailyQC ORDER BY iDate DESC LIMIT 10")
    print(cur.fetchall())
