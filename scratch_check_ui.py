import sys
from PyQt6.QtWidgets import QApplication
from database.connection import DBContext

def check_batches():
    with DBContext() as (conn, cursor):
        cursor.execute("SELECT DISTINCT lot, lot_id, lot_Level FROM LotTable WHERE lot LIKE 'C25%' OR lot LIKE 'D25%'")
        for row in cursor.fetchall():
            print(row)
if __name__ == "__main__":
    check_batches()
