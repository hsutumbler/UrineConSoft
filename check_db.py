from database.connection import DBContext
def check():
    with DBContext() as (conn, cur):
        cur.execute("DESCRIBE qc_anomaly_records")
        for r in cur.fetchall():
            print(f"{r['Field']}: {r['Type']}")

if __name__ == "__main__":
    check()
