from database.connection import DBContext, MSSQLContext

def sync_lots():
    with MSSQLContext() as (conn_ms, cursor_ms):
        print("Fetching LotTable from MS SQL...")
        cursor_ms.execute("SELECT od, mhId, lot, lot_id, lot_Level, QC_date, Writedate, iUser, lot_type, cName FROM LotTable")
        lottable_rows = cursor_ms.fetchall()
        
        print("Fetching LotTest from MS SQL...")
        # escape Range column because it's a keyword in MS SQL
        cursor_ms.execute("SELECT ltId, mhId, cId, mtId, lot, tMean, tSd, [Range], CVA, TEA, iDateTime, iUser, LotStyle, TA, SDI, SIGMA, BIAS FROM LotTest")
        lottest_rows = cursor_ms.fetchall()

    with DBContext() as (conn_my, cursor_my):
        print("Clearing local LotTable and LotTest...")
        cursor_my.execute("TRUNCATE TABLE LotTest")
        cursor_my.execute("TRUNCATE TABLE LotTable")
        
        print("Inserting LotTable...")
        for r in lottable_rows:
            cursor_my.execute("""
                INSERT INTO LotTable (od, mhId, lot, lot_id, lot_Level, QC_date, Writedate, iUser, lot_type, cName)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                r.get('od'), r.get('mhId'), r.get('lot'), r.get('lot_id'), r.get('lot_Level'),
                r.get('QC_date'), r.get('Writedate'), r.get('iUser'), r.get('lot_type'), r.get('cName')
            ))
            
        print("Inserting LotTest...")
        for r in lottest_rows:
            cursor_my.execute("""
                INSERT INTO LotTest (ltId, mhId, cId, mtId, lot, tMean, tSd, `Range`, CVA, TEA, iDateTime, iUser, LotStyle, TA, SDI, SIGMA, BIAS)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                r.get('ltId'), r.get('mhId'), r.get('cId'), r.get('mtId'), r.get('lot'),
                r.get('tMean'), r.get('tSd'), r.get('Range'), r.get('CVA'), r.get('TEA'),
                r.get('iDateTime'), r.get('iUser'), r.get('LotStyle'), r.get('TA'), r.get('SDI'),
                r.get('SIGMA'), r.get('BIAS')
            ))

    print(f"Successfully synced {len(lottable_rows)} LotTable rows and {len(lottest_rows)} LotTest rows.")

if __name__ == "__main__":
    sync_lots()
