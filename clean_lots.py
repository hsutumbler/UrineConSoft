from database.connection import DBContext

def clean_lots():
    with DBContext() as (conn, cursor):
        cursor.execute("SELECT COUNT(*) as c FROM LotTable")
        print(f"Before LotTable count: {cursor.fetchone()['c']}")
        
        cursor.execute("SELECT COUNT(*) as c FROM LotTest")
        print(f"Before LotTest count: {cursor.fetchone()['c']}")
        
        # Only keep lot = 'C252880' or 'D252880'
        cursor.execute("DELETE FROM LotTable WHERE lot NOT IN ('C252880', 'D252880')")
        cursor.execute("DELETE FROM LotTest WHERE lot NOT IN ('C252880', 'D252880', 'C252881', 'C252882', 'D252881', 'D252882', 'c252881', 'c252882', 'd252881', 'd252882')")
        
        cursor.execute("SELECT COUNT(*) as c FROM LotTable")
        print(f"After LotTable count: {cursor.fetchone()['c']}")
        
        cursor.execute("SELECT COUNT(*) as c FROM LotTest")
        print(f"After LotTest count: {cursor.fetchone()['c']}")

if __name__ == "__main__":
    clean_lots()
