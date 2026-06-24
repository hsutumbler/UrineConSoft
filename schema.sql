-- 建立空白資料庫結構 (schema.sql)
-- 使用前請先確認您已在 MySQL 建立 `qc_system` 資料庫，並已選擇使用該資料庫：
-- CREATE DATABASE IF NOT EXISTS qc_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE qc_system;

SET FOREIGN_KEY_CHECKS = 0;

-- --------------------------------------------------------
-- 表格結構建立
-- --------------------------------------------------------

CREATE TABLE IF NOT EXISTS MhMaster (
    mhId VARCHAR(50) PRIMARY KEY,
    mhName VARCHAR(50) NOT NULL,
    od VARCHAR(50),
    mhcode VARCHAR(50),
    DepartmentID VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS LotTable (
    od VARCHAR(10),
    mhId VARCHAR(10),
    lot VARCHAR(40),
    lot_id VARCHAR(40),
    lot_Level VARCHAR(20),
    QC_date DATETIME,
    expiry_date DATETIME,
    Writedate DATETIME,
    iUser VARCHAR(40),
    lot_type VARCHAR(10),
    cName VARCHAR(10),
    is_active TINYINT(1) DEFAULT 0,
    is_archived TINYINT(1) DEFAULT 0,
    acceptance_status VARCHAR(20) DEFAULT 'pending',
    acceptance_reason VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS LotTest (
    ltId BIGINT AUTO_INCREMENT PRIMARY KEY,
    mhId CHAR(4),
    cId CHAR(4),
    mtId VARCHAR(10),
    lot VARCHAR(40),
    tMean REAL,
    tSd REAL,
    `Range` VARCHAR(20),
    CVA REAL,
    TEA VARCHAR(10),
    iDateTime DATETIME,
    iUser VARCHAR(20),
    LotStyle CHAR(1),
    TA VARCHAR(20),
    SDI VARCHAR(20),
    SIGMA VARCHAR(20),
    BIAS VARCHAR(20),
    change_reason VARCHAR(255)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS DailyQC (
    dqcId BIGINT AUTO_INCREMENT PRIMARY KEY,
    mhId CHAR(4),
    cId CHAR(4),
    mtId VARCHAR(10),
    iValue REAL,
    iDate DATETIME,
    iUser VARCHAR(20),
    lot VARCHAR(40),
    ltId BIGINT,
    sdFlag SMALLINT,
    iFlag1 TINYINT,
    iFlag2 TINYINT,
    iFlag3 TINYINT,
    iFlag4 SMALLINT,
    iFlag5 TINYINT,
    vDate DATETIME,
    sysTime DATETIME,
    Check_Type CHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS QCaberrant (
    aberrantNO VARCHAR(50) PRIMARY KEY,
    dqcId BIGINT,
    UserName VARCHAR(50),
    mhName VARCHAR(50),
    WriteDate DATETIME,
    IncidentTime DATETIME,
    MhId VARCHAR(50),
    lot VARCHAR(50),
    Err_Lab VARCHAR(50),
    RepeatChk CHAR(2),
    Repeatcycle VARCHAR(50),
    Cause TEXT,
    UserFunction TEXT,
    FunctionResult TEXT,
    Precaution TEXT,
    ClassSign1 VARCHAR(50),
    inote1 TEXT,
    ClassSign2 VARCHAR(50),
    inote2 TEXT,
    ClassSign3 VARCHAR(50),
    inote3 TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS Phrase (
    preId BIGINT AUTO_INCREMENT PRIMARY KEY,
    wId VARCHAR(20),
    flag1 TINYINT,
    flag2 TINYINT,
    txt TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS MhItem (
    mhcode VARCHAR(50),
    mtId VARCHAR(10),
    mhitem VARCHAR(50),
    itemtype VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reagent_batches (
    batch_id INT AUTO_INCREMENT PRIMARY KEY,
    lot_number VARCHAR(100) NOT NULL,
    expiry_date DATE,
    open_date DATE,
    is_active BOOLEAN DEFAULT FALSE,
    is_archived BOOLEAN DEFAULT FALSE,
    acceptance_status VARCHAR(50) DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id VARCHAR(50),
    name VARCHAR(50),
    password_hash VARCHAR(255),
    role INT,
    is_active BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reagent_batch_acceptance (
    accept_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT,
    reagent_id VARCHAR(10),
    level_id INT,
    accept_type INT,
    semi_result VARCHAR(50),
    semi_expected VARCHAR(50),
    semi_pass BOOLEAN,
    measured_values JSON,
    calc_mean REAL,
    calc_sd REAL,
    result BOOLEAN,
    notes TEXT,
    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accepted_by INT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS reagent_batch_history (
    history_id INT AUTO_INCREMENT PRIMARY KEY,
    batch_id INT,
    status INT,
    snapshot_data JSON,
    accepted_by INT,
    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS DailyQC_notes (
    dqcId BIGINT PRIMARY KEY,
    notes TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SET FOREIGN_KEY_CHECKS = 1;


-- --------------------------------------------------------
-- 基礎預設資料 (Reference Data)
-- --------------------------------------------------------

-- 1. 預設系統管理員帳號 (密碼留空，可利用離線登入機制 'admin' / '0' 登入後再重設密碼)
INSERT INTO users (user_id, employee_id, name, password_hash, role) VALUES 
(1, 'admin', '系統管理員', '', 3);

-- 2. 檢驗項目基本資料
INSERT INTO MhItem (mhcode, mtId, mhitem, itemtype) VALUES 
('7701', '1', 'SG', 'Q'),
('7701', '2', 'pH', 'Q'),
('7701', '3', 'LEU', 'S'),
('7701', '4', 'NIT', 'S'),
('7701', '5', 'PRO', 'S'),
('7701', '6', 'GLU', 'S'),
('7701', '7', 'KET', 'S'),
('7701', '8', 'UBG', 'S'),
('7701', '9', 'BIL', 'S'),
('7701', '10', 'ERY', 'S'),
('7701', '11', 'ASC', 'S'),
('7701', '12', 'RBC', 'Q'),
('7701', '13', 'WBC', 'Q');

-- 3. 預設異常處理片語
INSERT INTO Phrase (txt) VALUES 
('人為失誤'),
('儀器故障'),
('更換試劑');

-- 4. 本地儀器對應表 (I003對應到77Urine_1)
INSERT INTO MhMaster (mhId, mhName, od, mhcode, DepartmentID) VALUES 
('I003', '77Urine_1', 'EDAD', '7701', 'LB');
