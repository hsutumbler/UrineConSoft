from database.connection import DBContext

def fix_lot_levels():
    with DBContext() as (conn, cursor):
        # Fetch all lots that were just created
        cursor.execute("SELECT lot FROM LotTable WHERE iUser='System_Sync'")
        lots = cursor.fetchall()
        for r in lots:
            lot_name = r['lot']
            # If lot ends with 1 -> level 1, 2 -> level 2
            if lot_name.endswith('1'):
                level = '1'
            elif lot_name.endswith('2'):
                level = '2'
            else:
                level = '1' # fallback
            
            cursor.execute("UPDATE LotTable SET lot_Level=%s WHERE lot=%s", (level, lot_name))
        print(f"Updated levels for {len(lots)} auto-generated lots.")

if __name__ == "__main__":
    fix_lot_levels()
