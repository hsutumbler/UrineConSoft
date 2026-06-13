from database.connection import MSSQLContext

def check_mapping():
    try:
        with MSSQLContext() as (conn, cursor):
            print("--- MhItem ---")
            cursor.execute("SELECT TOP 5 * FROM MhItem")
            for r in cursor.fetchall():
                print(r)
                
            print("\n--- MhTest ---")
            cursor.execute("SELECT TOP 5 * FROM MhTest")
            for r in cursor.fetchall():
                print(r)
                
            print("\n--- Parameter ---")
            cursor.execute("SELECT TOP 5 * FROM Parameter")
            for r in cursor.fetchall():
                print(r)
    except Exception as e:
        print(e)

if __name__ == "__main__":
    check_mapping()
