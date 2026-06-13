from datetime import date
from database.connection import MSSQLContext

def fetch_recent_qc():
    print("Connecting to MS SQL...")
    try:
        with MSSQLContext() as (conn, cursor):
            print("Connected! Fetching the latest 10 QC records from DailyQC...")
            # We fetch top 10 descending by iDate
            cursor.execute("""
                SELECT TOP 10 
                    dqcId, mhId, cId, mtId, iValue, iDate, iUser, lot
                FROM DailyQC
                ORDER BY iDate DESC
            """)
            records = cursor.fetchall()
            
            if not records:
                print("No records found in DailyQC.")
                return

            print(f"\nFound {len(records)} records. Most recent:")
            print("-" * 80)
            print(f"{'Date':<20} | {'Instrument':<10} | {'Test':<8} | {'Value':<10} | {'Lot':<15}")
            print("-" * 80)
            for r in records:
                iDate = str(r.get('iDate', ''))[:19]
                mhId = str(r.get('mhId', ''))
                mtId = str(r.get('mtId', ''))
                iValue = str(r.get('iValue', ''))
                lot = str(r.get('lot', ''))
                print(f"{iDate:<20} | {mhId:<10} | {mtId:<8} | {iValue:<10} | {lot:<15}")
            print("-" * 80)
    except Exception as e:
        print(f"Failed to fetch data: {e}")

if __name__ == "__main__":
    fetch_recent_qc()
