from database.connection import DBContext

with DBContext() as (conn, cur):
    cur.execute("SELECT record_id, created_at, serial_number FROM qc_anomaly_records")
    records = cur.fetchall()
    print("Existing records:")
    for r in records:
        print(f"record_id: {r['record_id']}, created_at: {r['created_at']}, serial_number: {r['serial_number']}")
        
    print("\nFixing formatting string in query...")
    ym = "202606"
    cur.execute("SELECT COUNT(*) as c FROM qc_anomaly_records WHERE DATE_FORMAT(created_at, '%Y%m') = %s", (ym,))
    res1 = cur.fetchone()
    print(f"Count with '%Y%m': {res1}")
    
    cur.execute("SELECT COUNT(*) as c FROM qc_anomaly_records WHERE DATE_FORMAT(created_at, '%%Y%%m') = %s", (ym,))
    res2 = cur.fetchone()
    print(f"Count with '%%Y%%m': {res2}")
