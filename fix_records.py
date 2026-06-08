from database.connection import DBContext

with DBContext() as (conn, cur):
    cur.execute("SELECT record_id, created_at, serial_number FROM qc_anomaly_records ORDER BY created_at ASC")
    records = cur.fetchall()
    
    counter = 1
    for r in records:
        ym = r['created_at'].strftime("%Y%m")
        new_sn = f"CE{ym}{counter:03d}"
        cur.execute("UPDATE qc_anomaly_records SET serial_number = %s WHERE record_id = %s", (new_sn, r['record_id']))
        counter += 1
        print(f"Updated record {r['record_id']} to {new_sn}")
        
    conn.commit()
    print("All existing records updated.")
