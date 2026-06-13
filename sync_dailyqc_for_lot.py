import sys
from datetime import datetime
from database.connection import MSSQLContext, DBContext

def sync():
    lots = ['C252881', 'C252882', 'D252881', 'D252882']
    # MSSQL might have lowercase c252881
    
    print("Connecting to MS SQL...")
    try:
        with MSSQLContext() as (conn, cursor):
            cursor.execute("""
                SELECT 
                    mhId, cId, mtId, iValue, iDate, iUser, UPPER(lot) as lot, Check_Type, sdFlag
                FROM DailyQC
                WHERE iDate BETWEEN '2026-06-01' AND '2026-06-12 23:59:59'
                  AND UPPER(lot) IN ('C252881', 'C252882', 'D252881', 'D252882')
            """)
            records = cursor.fetchall()
    except Exception as e:
        print(f"Failed to fetch from MS SQL: {e}")
        return

    if not records:
        print("No records found in MS SQL!")
        return

    print(f"Fetched {len(records)} records from MS SQL. Inserting into SQLite...")
    
    with DBContext() as (_, cur):
        # Delete existing ones to avoid duplicates if running multiple times
        cur.execute("""
            DELETE FROM DailyQC
            WHERE iDate BETWEEN '2026-06-01' AND '2026-06-12 23:59:59'
              AND UPPER(lot) IN ('C252881', 'C252882', 'D252881', 'D252882')
        """)
        
        inserted = 0
        for r in records:
            check_type = r.get('Check_Type')
            if check_type is None: check_type = 'A'
            sd_flag = r.get('sdFlag')
            if sd_flag is None: sd_flag = 0
            
            cur.execute("""
                INSERT INTO DailyQC 
                (mhId, cId, mtId, iValue, iDate, iUser, lot, Check_Type, sdFlag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                r.get('mhId', ''),
                r.get('cId', ''),
                r.get('mtId', ''),
                r.get('iValue', ''),
                r.get('iDate'),
                r.get('iUser', ''),
                r.get('lot'),
                check_type,
                sd_flag
            ))
            inserted += 1
            
        print(f"Successfully synced {inserted} records!")

if __name__ == "__main__":
    sync()
