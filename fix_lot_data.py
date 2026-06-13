from database.connection import DBContext

def fix_data():
    with DBContext() as (conn, cursor):
        # 1. Normalize lot_Level string to just '1' or '2'
        cursor.execute("UPDATE LotTable SET lot_Level = '1' WHERE lot_Level = 'Level1' OR lot_Level = '1'")
        cursor.execute("UPDATE LotTable SET lot_Level = '2' WHERE lot_Level = 'Level2' OR lot_Level = '2'")
        
        # 2. Uppercase lot names so 'c252880' becomes 'C252880'
        cursor.execute("UPDATE LotTable SET lot = UPPER(lot), lot_id = UPPER(lot_id)")
        
        # 3. Set expiry_date to 2026-11-30
        cursor.execute("UPDATE LotTable SET expiry_date = '2026-11-30'")
        
        # Check results
        cursor.execute("SELECT lot, lot_id, lot_Level, expiry_date FROM LotTable")
        for r in cursor.fetchall():
            print(r)

if __name__ == "__main__":
    fix_data()
