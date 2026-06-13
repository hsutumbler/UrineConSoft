from database.connection import DBContext

# Map of iValue -> Check_Type for mtId 3 to 11 (Semi-quant)
mapping = {
    -1.0: "Neg",
    0.5: "Trace",
    1.0: "1+",
    2.0: "2+",
    3.0: "3+",
    4.0: "4+",
}

with DBContext() as (conn, cur):
    print("Fixing qualitative results...")
    for mtId in range(3, 12):
        for val, qual in mapping.items():
            cur.execute("""
                UPDATE DailyQC 
                SET Check_Type = %s 
                WHERE mtId = %s AND iValue = %s AND Check_Type = '0'
            """, (qual, str(mtId), val))
    
    conn.commit()
    print("Done!")
