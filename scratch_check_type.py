from database.connection import MSSQLContext
def check_type():
    with MSSQLContext() as (conn, cursor):
        cursor.execute("SELECT TOP 5 mtId, iValue, Check_Type FROM DailyQC WHERE Check_Type IS NOT NULL AND Check_Type != '' ORDER BY iDate DESC")
        for r in cursor.fetchall(): print(r)
if __name__ == "__main__":
    check_type()
