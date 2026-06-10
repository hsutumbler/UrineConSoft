-- ============================================================
-- UrineConSoft — 品管系統資料庫建立腳本
-- Database: qc_system
-- ============================================================

CREATE DATABASE IF NOT EXISTS qc_system
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE qc_system;

-- ------------------------------------------------------------
-- 建立資料庫使用者
-- ------------------------------------------------------------
CREATE USER IF NOT EXISTS 'qc_user'@'localhost' IDENTIFIED BY 'qc_pass';
GRANT ALL PRIVILEGES ON qc_system.* TO 'qc_user'@'localhost';
FLUSH PRIVILEGES;
-- ------------------------------------------------------------
-- 使用者
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    employee_id   VARCHAR(20)  NOT NULL UNIQUE COMMENT '帳號',
    name          VARCHAR(50)  NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role          TINYINT      NOT NULL DEFAULT 1
                  COMMENT '1=一般, 2=品管負責人, 3=組長/主任',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
) COMMENT='使用者';

-- ------------------------------------------------------------
-- 主檔（以下均為 seed 資料，不提供 UI 修改）
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS vendors (
    vendor_id   INT AUTO_INCREMENT PRIMARY KEY,
    vendor_name VARCHAR(100) NOT NULL
) COMMENT='廠商';

CREATE TABLE IF NOT EXISTS departments (
    dept_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_name VARCHAR(50) NOT NULL
) COMMENT='組別';

CREATE TABLE IF NOT EXISTS instruments (
    instrument_id   INT AUTO_INCREMENT PRIMARY KEY,
    dept_id         INT         NOT NULL,
    instrument_name VARCHAR(50) NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
) COMMENT='儀器';

CREATE TABLE IF NOT EXISTS reagents (
    reagent_id    INT AUTO_INCREMENT PRIMARY KEY,
    reagent_name  VARCHAR(20)  NOT NULL COMMENT 'pH/SG/PRO...',
    reagent_label VARCHAR(50)  NOT NULL COMMENT '中文名稱',
    brand         VARCHAR(50)  NOT NULL DEFAULT 'LabStrip',
    param_type    TINYINT      NOT NULL DEFAULT 2
                  COMMENT '1=定量, 2=半定量',
    display_order INT          NOT NULL DEFAULT 0
) COMMENT='測量參數';

CREATE TABLE IF NOT EXISTS qc_levels (
    level_id    INT AUTO_INCREMENT PRIMARY KEY,
    reagent_id  INT          NOT NULL,
    level_name  VARCHAR(20)  NOT NULL COMMENT 'Level 1 / Level 2',
    vendor_id   INT          NOT NULL,
    qc_material VARCHAR(100) NOT NULL DEFAULT 'Quantimetrix',
    FOREIGN KEY (reagent_id) REFERENCES reagents(reagent_id),
    FOREIGN KEY (vendor_id)  REFERENCES vendors(vendor_id)
) COMMENT='品管液濃度';

CREATE TABLE IF NOT EXISTS instrument_qc_items (
    iqi_id        INT AUTO_INCREMENT PRIMARY KEY,
    instrument_id INT NOT NULL,
    reagent_id    INT NOT NULL,
    level_id      INT NOT NULL,
    display_order INT NOT NULL DEFAULT 0,
    UNIQUE KEY uq_iqi (instrument_id, reagent_id, level_id),
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
    FOREIGN KEY (reagent_id)    REFERENCES reagents(reagent_id),
    FOREIGN KEY (level_id)      REFERENCES qc_levels(level_id)
) COMMENT='品管項目（儀器×參數×濃度）';

-- ------------------------------------------------------------
-- 批號管理
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reagent_batches (
    batch_id    INT AUTO_INCREMENT PRIMARY KEY,
    lot_number  VARCHAR(50)  NOT NULL COMMENT '試劑批號',
    expiry_date DATE         COMMENT '效期',
    open_date   DATE         COMMENT '開封日',
    is_active   BOOLEAN      NOT NULL DEFAULT FALSE
                COMMENT '是否為目前使用中批號',
    notes       TEXT,
    created_by  INT          NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) COMMENT='試劑批號（LabStrip）';

CREATE TABLE IF NOT EXISTS qc_batches (
    batch_id    INT AUTO_INCREMENT PRIMARY KEY,
    level_id    INT          NOT NULL COMMENT 'Level 1 或 Level 2',
    lot_number  VARCHAR(50)  NOT NULL COMMENT '品管液批號',
    expiry_date DATE         COMMENT '效期',
    open_date   DATE         COMMENT '開封日',
    is_active   BOOLEAN      NOT NULL DEFAULT FALSE
                COMMENT '是否為目前使用中批號',
    notes       TEXT,
    created_by  INT          NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (level_id)   REFERENCES qc_levels(level_id),
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) COMMENT='品管液批號（Quantimetrix）';

-- ------------------------------------------------------------
-- 允收記錄
-- ------------------------------------------------------------



CREATE TABLE IF NOT EXISTS qc_batch_acceptance (
    accept_id       INT AUTO_INCREMENT PRIMARY KEY,
    qc_batch_id     INT          NOT NULL COMMENT '品管液批號',
    reagent_id      INT          NOT NULL COMMENT '測試的參數',
    accept_type     TINYINT      NOT NULL COMMENT '1=半定量, 2=定量',
    -- 半定量
    semi_result     VARCHAR(20),
    semi_expected   VARCHAR(20),
    semi_pass       BOOLEAN,
    -- 定量（行進允收）
    measured_values JSON         COMMENT '輸入數值 [v1, v2, ...]',
    calc_mean       DECIMAL(12,4),
    calc_sd         DECIMAL(12,4),
    result          BOOLEAN      NOT NULL DEFAULT TRUE,
    acceptance_status INT NOT NULL COMMENT '1=允收, 2=暫緩, 0=拒絕',
    accepted_by     INT          NOT NULL,
    accepted_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT,
    FOREIGN KEY (qc_batch_id) REFERENCES qc_batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (reagent_id)  REFERENCES reagents(reagent_id) ON DELETE CASCADE,
    FOREIGN KEY (accepted_by) REFERENCES users(user_id)
) COMMENT='品管液批次允收記錄';

CREATE TABLE IF NOT EXISTS reagent_batch_acceptance (
    acceptance_id      INT AUTO_INCREMENT PRIMARY KEY,
    reagent_batch_id   INT NOT NULL,
    status             INT NOT NULL COMMENT '1=允收, 2=暫緩, 0=拒絕',
    snapshot_data      JSON COMMENT '當時比對的快照資料',
    accepted_by        INT NOT NULL,
    accepted_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (reagent_batch_id) REFERENCES reagent_batches(batch_id) ON DELETE CASCADE,
    FOREIGN KEY (accepted_by) REFERENCES users(user_id)
) COMMENT='品管液批次允收記錄';

-- ------------------------------------------------------------
-- TM / TSD 設定（L-J chart 基準線）
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS qc_target_settings (
    setting_id     INT AUTO_INCREMENT PRIMARY KEY,
    iqi_id         INT           NOT NULL,
    qc_batch_id    INT           NOT NULL COMMENT '此批號有效',
    tm             DECIMAL(12,4) COMMENT 'Target Mean',
    tsd            DECIMAL(12,4) COMMENT 'Target SD',
    cva_percent    DECIMAL(5,2)  COMMENT 'CVa%',
    tea_percent    DECIMAL(5,2)  COMMENT 'TEa%',
    semi_target_min VARCHAR(20)  COMMENT '半定量最低可接受下限 (e.g. Neg, 1+)',
    semi_target_max VARCHAR(20)  COMMENT '半定量最高可接受上限',
    mode           TINYINT       NOT NULL DEFAULT 1
                   COMMENT '1=行進允收（累積計算）, 2=直接設定',
    effective_from DATE          NOT NULL,
    change_reason  VARCHAR(255)  COMMENT '變更原因',
    set_by         INT           NOT NULL,
    set_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iqi_id)      REFERENCES instrument_qc_items(iqi_id),
    FOREIGN KEY (qc_batch_id) REFERENCES qc_batches(batch_id),
    FOREIGN KEY (set_by)      REFERENCES users(user_id)
) COMMENT='品管目標值設定 (TM/TSD/CVa/TEa 及定性範圍)';

-- ------------------------------------------------------------
-- 每日品管結果（L-J chart 資料）
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS qc_results (
    result_id          INT AUTO_INCREMENT PRIMARY KEY,
    iqi_id             INT           NOT NULL,
    result_date        DATETIME      NOT NULL,
    reagent_batch_id   INT           COMMENT '當日使用的試劑批號',
    qc_batch_id        INT           COMMENT '當日使用的品管液批號',
    -- 定量（pH, SG, WBC, RBC）
    measured_value     DECIMAL(12,4),
    -- 半定量（PRO, GLU, KET, BLD, LEU, NIT, BIL, URO）
    qualitative_result VARCHAR(20)   COMMENT 'Neg/Trace/1+/2+/3+',
    is_accepted        BOOLEAN,
    westgard_flag      VARCHAR(20)   COMMENT '1-3S/2-2S/R-4S',
    source             TINYINT       NOT NULL DEFAULT 1
                       COMMENT '1=手動, 2=儀器傳輸',
    notes              TEXT,
    entered_by         INT           NOT NULL,
    entered_at         DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (iqi_id)           REFERENCES instrument_qc_items(iqi_id),
    FOREIGN KEY (reagent_batch_id) REFERENCES reagent_batches(batch_id),
    FOREIGN KEY (qc_batch_id)      REFERENCES qc_batches(batch_id),
    FOREIGN KEY (entered_by)       REFERENCES users(user_id),
    INDEX idx_iqi_date (iqi_id, result_date)
) COMMENT='每日品管結果';

-- ============================================================
-- SEED DATA（預建主檔，不提供 UI 修改）
-- ============================================================

-- 廠商
INSERT IGNORE INTO vendors (vendor_id, vendor_name) VALUES (1, '醫全實業');

-- 組別
INSERT IGNORE INTO departments (dept_id, dept_name) VALUES (1, '鏡檢組');

-- 儀器
INSERT IGNORE INTO instruments (instrument_id, dept_id, instrument_name) VALUES
(1, 1, '77-1'),
(2, 1, '77-2');

-- 12 個測量參數
INSERT IGNORE INTO reagents
    (reagent_id, reagent_name, reagent_label, brand, param_type, display_order)
VALUES
(1,  'pH',  '酸鹼值',        'LabStrip', 3, 1),
(2,  'SG',  '比重',          'LabStrip', 1, 2),
(3,  'PRO', '蛋白質',        'LabStrip', 2, 3),
(4,  'GLU', '葡萄糖',        'LabStrip', 2, 4),
(5,  'KET', '酮體',          'LabStrip', 2, 5),
(6,  'BLD', '潛血',          'LabStrip', 2, 6),
(7,  'LEU', '白血球酯酶',    'LabStrip', 2, 7),
(8,  'NIT', '亞硝酸鹽',      'LabStrip', 2, 8),
(9,  'BIL', '膽紅素',        'LabStrip', 2, 9),
(10, 'URO', '尿膽素原',      'LabStrip', 2, 10),
(11, 'WBC', 'WBC（鏡檢）',   'LabStrip', 1, 11),
(12, 'RBC', 'RBC（鏡檢）',   'LabStrip', 1, 12);

-- 品管液濃度（24 筆：12 參數 × 2 levels）
INSERT IGNORE INTO qc_levels
    (level_id, reagent_id, level_name, vendor_id, qc_material)
VALUES
(1,  1,  'Level 1', 1, 'Quantimetrix'),
(2,  1,  'Level 2', 1, 'Quantimetrix'),
(3,  2,  'Level 1', 1, 'Quantimetrix'),
(4,  2,  'Level 2', 1, 'Quantimetrix'),
(5,  3,  'Level 1', 1, 'Quantimetrix'),
(6,  3,  'Level 2', 1, 'Quantimetrix'),
(7,  4,  'Level 1', 1, 'Quantimetrix'),
(8,  4,  'Level 2', 1, 'Quantimetrix'),
(9,  5,  'Level 1', 1, 'Quantimetrix'),
(10, 5,  'Level 2', 1, 'Quantimetrix'),
(11, 6,  'Level 1', 1, 'Quantimetrix'),
(12, 6,  'Level 2', 1, 'Quantimetrix'),
(13, 7,  'Level 1', 1, 'Quantimetrix'),
(14, 7,  'Level 2', 1, 'Quantimetrix'),
(15, 8,  'Level 1', 1, 'Quantimetrix'),
(16, 8,  'Level 2', 1, 'Quantimetrix'),
(17, 9,  'Level 1', 1, 'Quantimetrix'),
(18, 9,  'Level 2', 1, 'Quantimetrix'),
(19, 10, 'Level 1', 1, 'Quantimetrix'),
(20, 10, 'Level 2', 1, 'Quantimetrix'),
(21, 11, 'Level 1', 1, 'Quantimetrix'),
(22, 11, 'Level 2', 1, 'Quantimetrix'),
(23, 12, 'Level 1', 1, 'Quantimetrix'),
(24, 12, 'Level 2', 1, 'Quantimetrix');

-- 品管項目（48 筆：2台 × 12參數 × 2levels）
-- 77-1 (instrument_id=1): iqi_id 1~24
-- 77-2 (instrument_id=2): iqi_id 25~48
INSERT IGNORE INTO instrument_qc_items
    (iqi_id, instrument_id, reagent_id, level_id, display_order)
VALUES
-- 77-1
(1,  1, 1,  1,  1), (2,  1, 1,  2,  2),
(3,  1, 2,  3,  3), (4,  1, 2,  4,  4),
(5,  1, 3,  5,  5), (6,  1, 3,  6,  6),
(7,  1, 4,  7,  7), (8,  1, 4,  8,  8),
(9,  1, 5,  9,  9), (10, 1, 5,  10, 10),
(11, 1, 6,  11, 11),(12, 1, 6,  12, 12),
(13, 1, 7,  13, 13),(14, 1, 7,  14, 14),
(15, 1, 8,  15, 15),(16, 1, 8,  16, 16),
(17, 1, 9,  17, 17),(18, 1, 9,  18, 18),
(19, 1, 10, 19, 19),(20, 1, 10, 20, 20),
(21, 1, 11, 21, 21),(22, 1, 11, 22, 22),
(23, 1, 12, 23, 23),(24, 1, 12, 24, 24),
-- 77-2
(25, 2, 1,  1,  1), (26, 2, 1,  2,  2),
(27, 2, 2,  3,  3), (28, 2, 2,  4,  4),
(29, 2, 3,  5,  5), (30, 2, 3,  6,  6),
(31, 2, 4,  7,  7), (32, 2, 4,  8,  8),
(33, 2, 5,  9,  9), (34, 2, 5,  10, 10),
(35, 2, 6,  11, 11),(36, 2, 6,  12, 12),
(37, 2, 7,  13, 13),(38, 2, 7,  14, 14),
(39, 2, 8,  15, 15),(40, 2, 8,  16, 16),
(41, 2, 9,  17, 17),(42, 2, 9,  18, 18),
(43, 2, 10, 19, 19),(44, 2, 10, 20, 20),
(45, 2, 11, 21, 21),(46, 2, 11, 22, 22),
(47, 2, 12, 23, 23),(48, 2, 12, 24, 24);

-- 預設管理員（密碼: Admin1234）
INSERT IGNORE INTO users (employee_id, name, password_hash, role)
VALUES (
    'admin',
    '系統管理員',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TiGwmGhvQLHx3hIBJIL7m8VCKJvK',
    3
);


-- ------------------------------------------------------------
-- 品管異常紀錄與片語
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS qc_anomaly_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL,
    anomaly_data VARCHAR(100),
    occurrence_time DATETIME,
    instrument_name VARCHAR(50),
    qc_lot_number VARCHAR(50),
    qc_level VARCHAR(20),
    violated_rule VARCHAR(50),
    anomaly_cause TEXT,
    corrective_action TEXT,
    corrective_result TEXT,
    preventive_action TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (result_id) REFERENCES qc_results(result_id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
) COMMENT='品管異常紀錄';

CREATE TABLE IF NOT EXISTS phrase_templates (
    template_id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    phrase_text TEXT NOT NULL,
    created_by INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) COMMENT='輸入片語範本';
