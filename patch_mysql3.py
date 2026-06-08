from database.connection import DBContext

def patch_db():
    with DBContext() as (conn, cursor):
        try:
            cursor.execute("ALTER TABLE qc_anomaly_records ADD COLUMN serial_number VARCHAR(20)")
            print("Column serial_number added.")
        except Exception as e:
            print(f"Error or column exists: {e}")
            
        try:
            cursor.execute("SELECT record_id, created_at FROM qc_anomaly_records ORDER BY created_at, record_id")
            records = cursor.fetchall()
            from collections import defaultdict
            counts = defaultdict(int)
            for r in records:
                ym = r['created_at'].strftime("%Y%m")
                counts[ym] += 1
                sn = f"{ym}{counts[ym]:03d}"
                cursor.execute("UPDATE qc_anomaly_records SET serial_number = %s WHERE record_id = %s", (sn, r['record_id']))
            print("Existing records updated.")
        except Exception as e:
            print(f"Update error: {e}")

if __name__ == '__main__':
    patch_db()
