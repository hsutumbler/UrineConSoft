from database.connection import DBContext

def check_asc():
    try:
        with DBContext() as (conn, cursor):
            cursor.execute("SELECT reagent_id, reagent_name, reagent_label FROM reagents")
            for r in cursor.fetchall():
                print(r)
    except Exception as e:
        print(e)
if __name__ == "__main__":
    check_mapping()
