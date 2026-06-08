with open("services/qc_service.py", "r") as f:
    sql = f.read()

# Fix get_all
old_all = """    @staticmethod
    def get_all() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT b.batch_id, b.lot_number, b.expiry_date, b.open_date, "
                "b.is_active, b.notes, b.created_at, u.name AS created_by_name "
                "FROM reagent_batches b "
                "JOIN users u ON b.created_by = u.user_id "
                "ORDER BY b.created_at DESC"
            )
            return cur.fetchall()"""

new_all = """    @staticmethod
    def get_all() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT b.batch_id, b.lot_number, b.expiry_date, b.open_date, "
                "b.is_active, b.acceptance_status, b.notes, b.created_at, u.name AS created_by_name "
                "FROM reagent_batches b "
                "JOIN users u ON b.created_by = u.user_id "
                "WHERE b.is_archived = FALSE "
                "ORDER BY b.created_at DESC"
            )
            return cur.fetchall()"""

sql = sql.replace(old_all, new_all)

# Fix get_active
old_active = """    @staticmethod
    def get_active() -> dict | None:
        with DBContext() as (_, cur):
            cur.execute(
            cur.execute("SELECT * FROM reagent_batches WHERE is_active=TRUE LIMIT 1")
            return cur.fetchone()"""

new_active = """    @staticmethod
    def get_active() -> dict | None:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT batch_id, lot_number, expiry_date, open_date "
                "FROM reagent_batches WHERE is_active=TRUE LIMIT 1"
            )
            return cur.fetchone()"""

sql = sql.replace(old_active, new_active)

with open("services/qc_service.py", "w") as f:
    f.write(sql)
