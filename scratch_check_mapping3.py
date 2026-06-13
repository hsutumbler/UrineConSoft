from database.connection import MSSQLContext
def check():
    try:
        with MSSQLContext() as (conn, cursor):
            for t in ['PResult', 'Phrase', 'Parameter', 'QCCode', 'LotTest']:
                print(f"\n--- {t} ---")
                try:
                    cursor.execute(f"SELECT TOP 3 * FROM {t}")
                    for r in cursor.fetchall(): print(r)
                except Exception as e: print(e)
    except Exception as e:
        print(e)
if __name__ == "__main__":
    check()
