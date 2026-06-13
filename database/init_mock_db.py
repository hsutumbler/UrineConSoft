import os
import sys
import pandas as pd
import mysql.connector

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def init_mock_db():
    print("Connecting to local MySQL...")
    # Ensure the database exists
    conn = mysql.connector.connect(
        host=DB_CONFIG['host'],
        port=DB_CONFIG['port'],
        user=DB_CONFIG['user'],
        password=DB_CONFIG['password']
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_CONFIG['database']}")
    cursor.close()
    conn.close()

    # Connect to the DB
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Drop existing old mock tables if any
    print("Dropping old tables...")
    # Disable foreign key checks to allow dropping tables with dependencies
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    
    cursor.execute("DROP TABLE IF EXISTS MhMaster")
    cursor.execute("DROP TABLE IF EXISTS LotTable")
    cursor.execute("DROP TABLE IF EXISTS LotTest")
    cursor.execute("DROP TABLE IF EXISTS DailyQC")
    cursor.execute("DROP TABLE IF EXISTS QCaberrant")
    cursor.execute("DROP TABLE IF EXISTS Phrase")
    cursor.execute("DROP TABLE IF EXISTS MhItem")
    
    # Drop new feature tables to ensure a complete wipe
    cursor.execute("DROP TABLE IF EXISTS reagent_batch_acceptance")
    cursor.execute("DROP TABLE IF EXISTS reagent_batches")
    cursor.execute("DROP TABLE IF EXISTS qc_batch_acceptance")
    cursor.execute("DROP TABLE IF EXISTS qc_target_settings")
    cursor.execute("DROP TABLE IF EXISTS qc_results")
    cursor.execute("DROP TABLE IF EXISTS qc_anomaly_records")
    cursor.execute("DROP TABLE IF EXISTS instrument_qc_items")
    cursor.execute("DROP TABLE IF EXISTS qc_batches")
    cursor.execute("DROP TABLE IF EXISTS users")
    
    # Re-enable foreign key checks
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    # Create tables
    print("Creating tables...")
    schema = """
    CREATE TABLE MhMaster (
        mhId VARCHAR(50) PRIMARY KEY,
        mhName VARCHAR(50) NOT NULL,
        od VARCHAR(50),
        mhcode VARCHAR(50),
        DepartmentID VARCHAR(50)
    );

    CREATE TABLE LotTable (
        od VARCHAR(10),
        mhId VARCHAR(10),
        lot VARCHAR(40),
        lot_id VARCHAR(40),
        lot_Level VARCHAR(20),
        QC_date DATETIME,
        Writedate DATETIME,
        iUser VARCHAR(40),
        lot_type VARCHAR(10),
        cName VARCHAR(10)
    );

    CREATE TABLE LotTest (
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
        BIAS VARCHAR(20)
    );

    CREATE TABLE DailyQC (
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
    );

    CREATE TABLE QCaberrant (
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
    );

    CREATE TABLE Phrase (
        preId BIGINT AUTO_INCREMENT PRIMARY KEY,
        wId VARCHAR(20),
        flag1 TINYINT,
        flag2 TINYINT,
        txt TEXT
    );

    CREATE TABLE MhItem (
        mhcode VARCHAR(50),
        mtId VARCHAR(10),
        mhitem VARCHAR(50),
        itemtype VARCHAR(10)
    );

    CREATE TABLE reagent_batches (
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
    );

    CREATE TABLE users (
        user_id INT AUTO_INCREMENT PRIMARY KEY,
        employee_id VARCHAR(50),
        name VARCHAR(50),
        role INT,
        is_active BOOLEAN DEFAULT TRUE
    );

    CREATE TABLE reagent_batch_acceptance (
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
    );
    """

    for stmt in schema.split(';'):
        if stmt.strip():
            cursor.execute(stmt)

    conn.commit()

    # Load data from Excel
    xls_path = '/Users/hsutumbler/Project/UrineConSoft/MeLinkU_QC/QC_Data.xls'
    if os.path.exists(xls_path):
        try:
            print("Loading data from Excel...")
            xls = pd.ExcelFile(xls_path)
            
            if 'MhMaster' in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name='MhMaster').fillna('')
                for _, row in df.iterrows():
                    cursor.execute(
                        "INSERT INTO MhMaster (mhId, mhName, od, mhcode, DepartmentID) VALUES (%s, %s, %s, %s, %s)",
                        (row['mhId'], row['mhName'], row['od'], row['mhcode'], row['DepartmentID'])
                    )
                    
            # 關閉舊歷史數據的匯入，只保留儀器 (MhMaster) 設定，給予乾淨的測試環境
            # if 'LotTable' in xls.sheet_names:
            #     df = pd.read_excel(xls, sheet_name='LotTable').fillna('')
            #     for _, row in df.iterrows():
            #         qc_date = None if row['QC_date'] == '' else row['QC_date']
            #         write_date = None if row['Writedate'] == '' else row['Writedate']
            #         cursor.execute(
            #             "INSERT INTO LotTable (od, mhId, lot, lot_id, lot_Level, QC_date, Writedate, iUser, lot_type, cName) "
            #             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            #             (row['od'], row['mhId'], row['lot'], row['lot_id'], row['lot_Level'], qc_date, write_date, row['iUser'], row['lot_type'], row['cName'])
            #         )
            #         
            # if 'LotTest' in xls.sheet_names:
            #     df = pd.read_excel(xls, sheet_name='LotTest').fillna('')
            #     for _, row in df.iterrows():
            #         cursor.execute(
            #             "INSERT INTO LotTest (ltId, mhId, cId, mtId, lot, tMean, tSd, `Range`, CVA, TEA, iDateTime, iUser, LotStyle, TA, SDI, SIGMA, BIAS) "
            #             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            #             (row['ltId'], row['mhId'], row['cId'], row['mtId'], row['lot'], 
            #              None if row['tMean'] == '' else row['tMean'], 
            #              None if row['tSd'] == '' else row['tSd'], 
            #              row['Range'], 
            #              None if row['CVA'] == '' else row['CVA'], 
            #              row['TEA'], 
            #              None if row['iDateTime'] == '' else row['iDateTime'], 
            #              row['iUser'], row['LotStyle'], row['TA'], row['SDI'], row['SIGMA'], row['BIAS'])
            #         )
            # 
            # if 'DailyQC' in xls.sheet_names:
            #     df = pd.read_excel(xls, sheet_name='DailyQC').fillna('')
            #     for _, row in df.iterrows():
            #         cursor.execute(
            #             "INSERT INTO DailyQC (dqcId, mhId, cId, mtId, iValue, iDate, iUser, lot, ltId, sdFlag, iFlag1, iFlag2, iFlag3, iFlag4, iFlag5, vDate, sysTime, Check_Type) "
            #             "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
            #             (row['dqcId'], row['mhId'], row['cId'], row['mtId'], 
            #              None if row['iValue'] == '' else row['iValue'], 
            #              None if row['iDate'] == '' else row['iDate'], 
            #              row['iUser'], row['lot'], row['ltId'], 
            #              None if row['sdFlag'] == '' else row['sdFlag'], 
            #              None if row['iFlag1'] == '' else row['iFlag1'], 
            #              None if row['iFlag2'] == '' else row['iFlag2'], 
            #              None if row['iFlag3'] == '' else row['iFlag3'], 
            #              None if row['iFlag4'] == '' else row['iFlag4'], 
            #              None if row['iFlag5'] == '' else row['iFlag5'], 
            #              None if row['vDate'] == '' else row['vDate'], 
            #              None if row['sysTime'] == '' else row['sysTime'], row['Check_Type'])
            #         )

            conn.commit()
            print("Basic config data loaded successfully.")
            
        except Exception as e:
            print(f"Error reading Excel: {e}")
            conn.rollback()

    # csv_path = '/Users/hsutumbler/Project/UrineConSoft/recent_data.csv'
    # if os.path.exists(csv_path):
    #     try:
    #         print("Loading custom data from CSV...")
    #         df = pd.read_csv(csv_path).fillna('')
    #         for _, row in df.iterrows():
    #             cursor.execute(
    #                 "INSERT INTO DailyQC (mhId, mtId, lot, iValue, Check_Type, iDate, iUser, sdFlag) "
    #                 "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
    #                 (row['儀器代碼(mhId)'], row['項目代碼(mtId)'], row['批號(lot)'], 
    #                  None if row['定量數值(iValue)'] == '' else row['定量數值(iValue)'], 
    #                  row['半定量字串(Check_Type)'], 
    #                  None if row['檢驗時間(iDate)'] == '' else row['檢驗時間(iDate)'], 
    #                  row['檢驗人員(iUser)'], 
    #                  None if row['允收註記(sdFlag:0=允收,1=拒絕)'] == '' else row['允收註記(sdFlag:0=允收,1=拒絕)'])
    #             )
    #         conn.commit()
    #         print("Custom CSV data loaded successfully.")
    #     except Exception as e:
    #         print(f"Error reading CSV: {e}")
    #         conn.rollback()
    
    # Insert some basic phrases and items manually
    print("Inserting basic reference data...")
    try:
        phrases = ["人為失誤", "儀器故障", "更換試劑"]
        for p in phrases:
            cursor.execute("INSERT INTO Phrase (txt) VALUES (%s)", (p,))
            
        items = [
            ("7701", "1", "SG", "Q"),
            ("7701", "2", "pH", "Q"),
            ("7701", "3", "LEU", "S"),
            ("7701", "4", "NIT", "S"),
            ("7701", "5", "PRO", "S"),
            ("7701", "6", "GLU", "S"),
            ("7701", "7", "KET", "S"),
            ("7701", "8", "UBG", "S"),
            ("7701", "9", "BIL", "S"),
            ("7701", "10", "ERY", "S"),
            ("7701", "11", "ASC", "S"),
            ("7701", "12", "RBC", "Q"),
            ("7701", "13", "WBC", "Q")
        ]
        for i in items:
            cursor.execute("INSERT INTO MhItem (mhcode, mtId, mhitem, itemtype) VALUES (%s, %s, %s, %s)", i)
            
        cursor.execute("INSERT INTO users (user_id, employee_id, name, role) VALUES (1, 'admin', '系統管理員', 3)")

        conn.commit()
        print("Initialization complete!")
    except Exception as e:
        print(f"Error inserting ref data: {e}")
        conn.rollback()

    cursor.close()
    conn.close()

if __name__ == "__main__":
    init_mock_db()
