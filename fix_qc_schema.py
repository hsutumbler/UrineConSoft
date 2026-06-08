with open("database/schema.sql", "r") as f:
    sql = f.read()

old_qc = """    expiry_date     DATE,
    open_date       DATE,
    is_active       BOOLEAN DEFAULT FALSE,
    created_by      INT          NOT NULL,"""

new_qc = """    expiry_date     DATE,
    open_date       DATE,
    is_active       BOOLEAN DEFAULT FALSE,
    acceptance_status INT DEFAULT 0 COMMENT '0=Pending, 1=Accepted, 2=Rejected',
    created_by      INT          NOT NULL,"""

sql = sql.replace(old_qc, new_qc)

with open("database/schema.sql", "w") as f:
    f.write(sql)
