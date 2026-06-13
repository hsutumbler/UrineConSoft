import datetime
from database.connection import DBContext, MSSQLContext

class SyncService:
    @staticmethod
    def sync_daily_qc(force_start_date=None):
        """
        從 MS SQL 撈取新的 DailyQC 資料，寫入本地 MySQL。
        """
        # 1. 取得最後同步時間
        last_sync = None
        if force_start_date:
            last_sync = datetime.datetime.strptime(force_start_date, '%Y-%m-%d')
        else:
            with DBContext() as (conn, cursor):
                cursor.execute("SELECT MAX(iDate) AS max_date FROM DailyQC")
                res = cursor.fetchone()
                if res and res['max_date']:
                    last_sync = res['max_date']

            if not last_sync or last_sync < datetime.datetime(2026, 6, 1):
                last_sync = datetime.datetime(2026, 6, 1)

        print(f"Syncing records from MS SQL since {last_sync}...")

        # 2. 從 MS SQL 抓取新資料
        records_to_sync = []
        with MSSQLContext() as (conn, cursor):
            cursor.execute(
                "SELECT dqcId, mhId, cId, mtId, iValue, iDate, iUser, lot, "
                "ltId, sdFlag, iFlag1, iFlag2, iFlag3, iFlag4, iFlag5, vDate, sysTime "
                "FROM DailyQC WHERE iDate >= %s ORDER BY iDate ASC",
                (last_sync,)
            )
            records_to_sync = cursor.fetchall()

        if not records_to_sync:
            print("No new records to sync.")
            return 0

        # 定性數值對應表
        def get_qualitative_string(mt_id_str, i_value):
            try:
                val = float(i_value)
            except:
                return str(i_value)

            # UBG / URO (mtId=32)
            if mt_id_str == '32':
                return "Neg" if val < 2.0 else "Pos"
            
            # 定量項目 (RBC=1, WBC=2, SG=41, pH=38) 不轉換
            if mt_id_str in ('1', '2', '38', '41'):
                return ""

            # 其餘定性項目
            if val <= -1.0:
                return "Neg"
            elif val == 1.0:
                return "Trace"
            elif val == 2.0:
                return "1+"
            elif val == 3.0:
                return "2+"
            elif val == 4.0:
                return "3+"
            elif val >= 5.0:
                return "4+"
            return str(val)[:10]

        # 3. 寫入 MySQL 並處理未知批號
        inserted_count = 0
        with DBContext() as (conn, cursor):
            # 為了避免重複插入相同的資料，先刪除已存在於 MySQL 中且時間 >= last_sync 的記錄
            # 這樣保證重新抓取 2026-06-01 以來的資料不會發生重複
            cursor.execute("DELETE FROM DailyQC WHERE iDate >= %s", (last_sync,))

            for r in records_to_sync:
                # 檢查 Lot_id 是否存在於 LotTable
                # 備註: DailyQC 中的 'lot' 其實是 LotTable 中的 'lot_id' (例如 C252881)
                lot_id_str = r.get('lot') or ''
                if lot_id_str:
                    cursor.execute("SELECT lot_id FROM LotTable WHERE lot_id=%s", (lot_id_str,))
                    if not cursor.fetchone():
                        # 新建待允收批號
                        # 解析出 base_lot (例如 C252880) 與 level (例如 1)
                        if lot_id_str[-1] in ('1', '2'):
                            base_lot = lot_id_str[:-1] + '0'
                            level = lot_id_str[-1]
                        else:
                            base_lot = lot_id_str
                            level = '1'

                        cursor.execute(
                            "INSERT INTO LotTable (lot, lot_id, iUser, lot_Level) VALUES (%s, %s, 'System_Sync', %s)",
                            (base_lot, lot_id_str, level)
                        )

                check_type_str = get_qualitative_string(str(r.get('mtId')), r.get('iValue', 0))

                # Insert
                cursor.execute("""
                    INSERT INTO DailyQC (
                        mhId, cId, mtId, iValue, iDate, iUser, lot, ltId,
                        sdFlag, iFlag1, iFlag2, iFlag3, iFlag4, iFlag5, vDate, sysTime, Check_Type
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    r.get('mhId'), r.get('cId'), r.get('mtId'), r.get('iValue'),
                    r.get('iDate'), r.get('iUser'), r.get('lot'), r.get('ltId'),
                    r.get('sdFlag'), r.get('iFlag1'), r.get('iFlag2'), r.get('iFlag3'),
                    r.get('iFlag4'), r.get('iFlag5'), r.get('vDate'), r.get('sysTime'),
                    check_type_str
                ))
                inserted_count += 1

        print(f"Successfully synced {inserted_count} records to MySQL DailyQC.")
        return inserted_count

if __name__ == "__main__":
    SyncService.sync_daily_qc()
