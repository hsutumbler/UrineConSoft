import datetime
from database.connection import DBContext, MSSQLContext
from logger_setup import logger

class SyncService:
    @staticmethod
    def sync_daily_qc(force_start_date=None):
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

        logger.info(f"Syncing records from MS SQL since {last_sync}...")

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
            logger.info("No new records to sync.")
            return 0

        def get_qualitative_string(local_mtid, i_value):
            try:
                val = float(i_value)
            except:
                return str(i_value)

            # 定量項目不轉換
            if local_mtid in (1, 2, 12, 13): # SG, pH, RBC, WBC
                return ""
            
            # NIT (4) 只接受 Neg, Pos
            if local_mtid == 4:
                return "Neg" if val < 1.0 else "Pos"
            
            # UBG (8) 映射為 1+, 2+ 等
            if local_mtid == 8:
                if val <= -1.0: return "Neg"
                if val == 1.0 or val == 2.0: return "1+"
                if val == 3.0: return "2+"
                if val >= 4.0: return "3+"
                return "Neg"

            if val <= -1.0: return "Neg"
            elif val == 1.0: return "1+"
            elif val == 2.0: return "2+"
            elif val == 3.0: return "3+"
            elif val >= 4.0: return "4+"
            return str(val)[:10]

        inserted_count = 0
        with DBContext() as (conn, cursor):
            cursor.execute("DELETE FROM DailyQC WHERE iDate >= %s", (last_sync,))

            for r in records_to_sync:
                # 依據規定：只接收 77Urine_1 (對應 MSSQL 的 I003, 即 77Urine-dc) 與 77Urine_2 (I004) 的數據
                mh_id = str(r.get('mhId') or '').strip()
                if mh_id not in ('I003', 'I004'):
                    continue

                lot_id_str = str(r.get('lot') or '').upper()
                if lot_id_str.startswith("CH252880") or lot_id_str.startswith("SED252880") or lot_id_str.startswith("CHC240920"):
                    continue

                mssql_mtid = str(r.get('mtId') or '').strip()
                local_mtid = None

                is_sediment = lot_id_str.startswith('D') or lot_id_str.startswith('SED')
                is_chemistry = lot_id_str.startswith('C')

                if is_sediment:
                    if mssql_mtid == '1': local_mtid = 12
                    elif mssql_mtid == '2': local_mtid = 13
                elif is_chemistry:
                    if int(mssql_mtid) <= 13:
                        local_mtid = int(mssql_mtid)
                    elif mssql_mtid == '41': local_mtid = 1
                    elif mssql_mtid == '38': local_mtid = 2
                    elif mssql_mtid == '36': local_mtid = 5
                    elif mssql_mtid == '35': local_mtid = 6
                    elif mssql_mtid == '33': local_mtid = 7
                    elif mssql_mtid == '37': local_mtid = 10
                    elif mssql_mtid == '40': local_mtid = 3
                    elif mssql_mtid == '39': local_mtid = 4
                    elif mssql_mtid == '31': local_mtid = 9
                    elif mssql_mtid == '32': local_mtid = 8
                    elif mssql_mtid == '34': local_mtid = 11

                if not local_mtid:
                    local_mtid = int(mssql_mtid)

                r['mtId'] = local_mtid

                if lot_id_str:
                    cursor.execute("SELECT lot_id FROM LotTable WHERE lot_id=%s", (lot_id_str,))
                    if not cursor.fetchone():
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

                check_type_str = get_qualitative_string(local_mtid, r.get('iValue', 0))

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

        logger.info(f"Successfully synced {inserted_count} records to MySQL DailyQC.")
        return inserted_count

if __name__ == "__main__":
    SyncService.sync_daily_qc()
