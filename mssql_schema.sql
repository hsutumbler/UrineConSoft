-- MS SQL 版本空白資料庫結構 (mssql_schema.sql)
-- 請在 MS SQL Server Management Studio (SSMS) 中執行

-- 假設您建立了一個新的 Database 叫做 UrineQC_DB
-- USE UrineQC_DB;
-- GO

-- --------------------------------------------------------
-- 表格結構建立
-- --------------------------------------------------------

IF OBJECT_ID('MhMaster', 'U') IS NULL
CREATE TABLE MhMaster (
    mhId VARCHAR(50) PRIMARY KEY,
    mhName NVARCHAR(50) NOT NULL,
    od VARCHAR(50),
    mhcode VARCHAR(50),
    DepartmentID VARCHAR(50)
);

IF OBJECT_ID('LotTable', 'U') IS NULL
CREATE TABLE LotTable (
    od VARCHAR(10),
    mhId VARCHAR(10),
    lot VARCHAR(40),
    lot_id VARCHAR(40),
    lot_Level VARCHAR(20),
    QC_date DATETIME2,
    expiry_date DATETIME2,
    Writedate DATETIME2,
    iUser NVARCHAR(40),
    lot_type VARCHAR(10),
    cName NVARCHAR(10),
    is_active BIT DEFAULT 0,
    is_archived BIT DEFAULT 0,
    acceptance_status VARCHAR(20) DEFAULT 'pending',
    acceptance_reason NVARCHAR(255) DEFAULT NULL
);

IF OBJECT_ID('LotTest', 'U') IS NULL
CREATE TABLE LotTest (
    ltId BIGINT IDENTITY(1,1) PRIMARY KEY,
    mhId CHAR(4),
    cId CHAR(4),
    mtId VARCHAR(10),
    lot VARCHAR(40),
    tMean REAL,
    tSd REAL,
    [Range] VARCHAR(20),
    CVA REAL,
    TEA VARCHAR(10),
    iDateTime DATETIME2,
    iUser NVARCHAR(20),
    LotStyle CHAR(1),
    TA VARCHAR(20),
    SDI VARCHAR(20),
    SIGMA VARCHAR(20),
    BIAS VARCHAR(20),
    change_reason NVARCHAR(255)
);

IF OBJECT_ID('DailyQC', 'U') IS NULL
CREATE TABLE DailyQC (
    dqcId BIGINT IDENTITY(1,1) PRIMARY KEY,
    mhId CHAR(4),
    cId CHAR(4),
    mtId VARCHAR(10),
    iValue REAL,
    iDate DATETIME2,
    iUser NVARCHAR(20),
    lot VARCHAR(40),
    ltId BIGINT,
    sdFlag SMALLINT,
    iFlag1 TINYINT,
    iFlag2 TINYINT,
    iFlag3 TINYINT,
    iFlag4 SMALLINT,
    iFlag5 TINYINT,
    vDate DATETIME2,
    sysTime DATETIME2,
    Check_Type VARCHAR(10)
);

IF OBJECT_ID('QCaberrant', 'U') IS NULL
CREATE TABLE QCaberrant (
    aberrantNO VARCHAR(50) PRIMARY KEY,
    dqcId BIGINT,
    UserName NVARCHAR(50),
    mhName NVARCHAR(50),
    WriteDate DATETIME2,
    IncidentTime DATETIME2,
    MhId VARCHAR(50),
    lot VARCHAR(50),
    Err_Lab NVARCHAR(50),
    RepeatChk CHAR(2),
    Repeatcycle VARCHAR(50),
    Cause NVARCHAR(MAX),
    UserFunction NVARCHAR(MAX),
    FunctionResult NVARCHAR(MAX),
    Precaution NVARCHAR(MAX),
    ClassSign1 NVARCHAR(50),
    inote1 NVARCHAR(MAX),
    ClassSign2 NVARCHAR(50),
    inote2 NVARCHAR(MAX),
    ClassSign3 NVARCHAR(50),
    inote3 NVARCHAR(MAX)
);

IF OBJECT_ID('Phrase', 'U') IS NULL
CREATE TABLE Phrase (
    preId BIGINT IDENTITY(1,1) PRIMARY KEY,
    wId VARCHAR(20),
    flag1 TINYINT,
    flag2 TINYINT,
    txt NVARCHAR(MAX)
);

IF OBJECT_ID('MhItem', 'U') IS NULL
CREATE TABLE MhItem (
    mhcode VARCHAR(50),
    mtId VARCHAR(10),
    mhitem NVARCHAR(50),
    itemtype VARCHAR(10)
);

IF OBJECT_ID('reagent_batches', 'U') IS NULL
CREATE TABLE reagent_batches (
    batch_id INT IDENTITY(1,1) PRIMARY KEY,
    lot_number VARCHAR(100) NOT NULL,
    expiry_date DATE,
    open_date DATE,
    is_active BIT DEFAULT 0,
    is_archived BIT DEFAULT 0,
    acceptance_status VARCHAR(50) DEFAULT 'pending',
    notes NVARCHAR(MAX),
    created_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,
    created_by INT
);

IF OBJECT_ID('users', 'U') IS NULL
CREATE TABLE users (
    user_id INT IDENTITY(1,1) PRIMARY KEY,
    employee_id VARCHAR(50),
    name NVARCHAR(50),
    password_hash VARCHAR(255),
    role INT,
    is_active BIT DEFAULT 1
);

IF OBJECT_ID('reagent_batch_acceptance', 'U') IS NULL
CREATE TABLE reagent_batch_acceptance (
    accept_id INT IDENTITY(1,1) PRIMARY KEY,
    batch_id INT,
    reagent_id VARCHAR(10),
    level_id INT,
    accept_type INT,
    semi_result NVARCHAR(50),
    semi_expected NVARCHAR(50),
    semi_pass BIT,
    measured_values NVARCHAR(MAX), -- JSON string in MSSQL
    calc_mean REAL,
    calc_sd REAL,
    result BIT,
    notes NVARCHAR(MAX),
    accepted_at DATETIME2 DEFAULT CURRENT_TIMESTAMP,
    accepted_by INT
);

GO

-- --------------------------------------------------------
-- 基礎預設資料 (Reference Data)
-- --------------------------------------------------------

-- 1. 預設系統管理員帳號 (密碼留空，可利用離線登入機制 'admin' / '0' 登入後再重設密碼)
IF NOT EXISTS (SELECT 1 FROM users WHERE employee_id = 'admin')
BEGIN
    INSERT INTO users (employee_id, name, password_hash, role) VALUES 
    ('admin', N'系統管理員', '', 3);
END

-- 2. 檢驗項目基本資料
IF NOT EXISTS (SELECT 1 FROM MhItem)
BEGIN
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
END

-- 3. 預設異常處理片語
IF NOT EXISTS (SELECT 1 FROM Phrase)
BEGIN
    INSERT INTO Phrase (txt) VALUES 
    (N'人為失誤'),
    (N'儀器故障'),
    (N'更換試劑');
END

-- 4. 本地儀器對應表 (I003對應到77Urine_1)
IF NOT EXISTS (SELECT 1 FROM MhMaster)
BEGIN
    INSERT INTO MhMaster (mhId, mhName, od, mhcode, DepartmentID) VALUES 
    ('I003', '77Urine_1', 'EDAD', '7701', 'LB');
END
GO
