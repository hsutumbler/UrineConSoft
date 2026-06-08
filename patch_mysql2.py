from database.connection import DBContext

def patch_db():
    with DBContext() as (conn, cursor):
        try:
            cursor.execute("ALTER TABLE qc_anomaly_records ADD COLUMN check_items VARCHAR(255)")
            print("Column check_items added.")
        except Exception as e:
            print(f"Error or column already exists: {e}")

if __name__ == '__main__':
    patch_db()
