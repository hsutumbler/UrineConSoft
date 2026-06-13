from database.connection import MSSQLContext
def check_mapping():
    try:
        with MSSQLContext() as (conn, cursor):
            cursor.execute("SELECT mtId, mtName, itemtype FROM MhTest WHERE mhId='I001' ORDER BY mtId")
            for r in cursor.fetchall():
                print(r)
    except Exception as e:
        print(e)
if __name__ == "__main__":
    check_mapping()
