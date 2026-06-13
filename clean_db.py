from database.connection import DBContext

def clean():
    with DBContext() as (_, cur):
        cur.execute("DELETE FROM LotTable")
        cur.execute("DELETE FROM LotTest")
        print("Cleaned LotTable and LotTest")

if __name__ == '__main__':
    clean()
