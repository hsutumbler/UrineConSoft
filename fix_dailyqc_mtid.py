from database.connection import DBContext

# Map of MS SQL mtId -> Local mtId
mapping_c = {
    "41": "1",  # SG
    "38": "2",  # pH
    "40": "3",  # LEU
    "39": "4",  # NIT
    "36": "5",  # PRO
    "35": "6",  # GLU
    "33": "7",  # KET
    "32": "8",  # UBG
    "31": "9",  # BIL
    "37": "10", # BLD -> ERY
    "34": "11"  # ASC
}

mapping_d = {
    "1": "12",  # RBC
    "2": "13",  # WBC
}

with DBContext() as (conn, cur):
    print("Fixing C252881 / C252882...")
    for old_id, new_id in mapping_c.items():
        cur.execute("""
            UPDATE DailyQC 
            SET mtId = %s 
            WHERE mtId = %s AND UPPER(lot) IN ('C252881', 'C252882')
        """, (new_id, old_id))
    
    print("Fixing D252881 / D252882...")
    for old_id, new_id in mapping_d.items():
        cur.execute("""
            UPDATE DailyQC 
            SET mtId = %s 
            WHERE mtId = %s AND UPPER(lot) IN ('D252881', 'D252882')
        """, (new_id, old_id))
    
    conn.commit()
    print("Done!")
