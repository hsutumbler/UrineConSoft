import pymssql

try:
    conn = pymssql.connect(
        server="10.9.8.100",
        user="hitsrv",
        password="hitsrv",
        database="ULink"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'")
    tables = cursor.fetchall()
    for t in tables:
        print(t[0])
    
    # Let's see columns in a potential QC table
    print("\n-- Columns in DailyQC if it exists --")
    cursor.execute("SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='DailyQC'")
    cols = cursor.fetchall()
    for c in cols:
        print(f"{c[0]}: {c[1]}")
        
    conn.close()
except Exception as e:
    print(f"Error: {e}")
