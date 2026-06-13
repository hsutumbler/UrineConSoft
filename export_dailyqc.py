import csv
from datetime import date
from database.connection import MSSQLContext

def export_today_qc():
    today_str = date.today().strftime('%Y-%m-%d')
    output_file = f"DailyQC_{today_str}.csv"
    
    try:
        with MSSQLContext() as (conn, cursor):
            # iDate is datetime, so we filter by today's date
            query = f"""
                SELECT dqcId, mhId, cId, mtId, iValue, iDate, iUser, lot
                FROM DailyQC
                WHERE CAST(iDate AS DATE) = '{today_str}'
                ORDER BY iDate DESC, mtId ASC
            """
            cursor.execute(query)
            records = cursor.fetchall()
            
            if not records:
                print(f"No records found for today ({today_str}).")
                # Fallback to fetching top 100 recent records if today is empty
                print("Fetching the latest 100 records instead...")
                cursor.execute("""
                    SELECT TOP 100 dqcId, mhId, cId, mtId, iValue, iDate, iUser, lot
                    FROM DailyQC
                    ORDER BY iDate DESC, mtId ASC
                """)
                records = cursor.fetchall()
            
            if not records:
                print("Still no records found.")
                return

            with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['dqcId', 'Instrument (mhId)', 'cId', 'Test ID (mtId)', 'Value (iValue)', 'Date (iDate)', 'User (iUser)', 'Lot (lot)'])
                for r in records:
                    writer.writerow([
                        r.get('dqcId', ''),
                        r.get('mhId', ''),
                        r.get('cId', ''),
                        r.get('mtId', ''),
                        r.get('iValue', ''),
                        str(r.get('iDate', ''))[:19],
                        r.get('iUser', ''),
                        r.get('lot', '')
                    ])
            print(f"Successfully exported {len(records)} records to {output_file}")
            
    except Exception as e:
        print(f"Export failed: {e}")

if __name__ == "__main__":
    export_today_qc()
