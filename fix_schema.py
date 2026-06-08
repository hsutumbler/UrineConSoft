with open("database/schema.sql", "r") as f:
    sql = f.read()

# First, revert the bad patch
bad_patch = """    measured_values JSON         COMMENT '輸入數值 [v1, v2, ...]',
    calc_mean       DECIMAL(12,4),
    calc_sd         DECIMAL(12,4),
    expiry_date        DATE,
    open_date          DATE,
    is_active          BOOLEAN DEFAULT FALSE,
    is_archived        BOOLEAN DEFAULT FALSE,
    acceptance_status  INT DEFAULT 0 COMMENT '0=Pending, 1=Accepted, 2=Hold, 3=Rejected',
    accepted_by     INT          NOT NULL,
    accepted_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,"""

good_revert = """    measured_values JSON         COMMENT '輸入數值 [v1, v2, ...]',
    calc_mean       DECIMAL(12,4),
    calc_sd         DECIMAL(12,4),
    result          BOOLEAN      NOT NULL DEFAULT TRUE,
    acceptance_status INT NOT NULL COMMENT '1=允收, 2=暫緩, 0=拒絕',
    accepted_by     INT          NOT NULL,
    accepted_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,"""

sql = sql.replace(bad_patch, good_revert)

# Next, apply the good patch to reagent_batches table
old_rb = """    expiry_date        DATE,
    open_date          DATE,
    is_active          BOOLEAN DEFAULT FALSE,
    acceptance_status  INT DEFAULT 0 COMMENT '0=Pending, 1=Accepted, 2=Hold, 3=Rejected',
    notes              TEXT,"""

new_rb = """    expiry_date        DATE,
    open_date          DATE,
    is_active          BOOLEAN DEFAULT FALSE,
    is_archived        BOOLEAN DEFAULT FALSE,
    acceptance_status  INT DEFAULT 0 COMMENT '0=Pending, 1=Accepted, 2=Hold, 3=Rejected',
    notes              TEXT,"""

sql = sql.replace(old_rb, new_rb)

with open("database/schema.sql", "w") as f:
    f.write(sql)
