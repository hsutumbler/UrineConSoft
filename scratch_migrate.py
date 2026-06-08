import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import DBContext

def migrate():
    with DBContext() as (conn, cur):
        try:
            cur.execute("ALTER TABLE qc_target_settings ADD COLUMN change_reason VARCHAR(255)")
            print("Migration successful: Added change_reason column.")
        except Exception as e:
            if "Duplicate column name" in str(e):
                print("Column already exists.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    migrate()
