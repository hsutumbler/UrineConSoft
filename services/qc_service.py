# services/qc_service.py — 品管業務邏輯

import json
import math
from datetime import date
from database.connection import DBContext


# ── 主檔查詢（只讀 seed data） ────────────────────────────────

class MasterService:

    @staticmethod
    def get_instruments() -> list[dict]:
        with DBContext() as (_, cur):
            # 舊系統: MhMaster
            cur.execute("SELECT mhId AS instrument_id, mhName AS instrument_name FROM MhMaster WHERE mhName NOT IN ('77Urine', '77Urine-ec') ORDER BY mhId")
            return cur.fetchall()

    @staticmethod
    def get_reagents() -> list[dict]:
        with DBContext() as (_, cur):
            # 舊系統: MhItem
            # param_type 對應舊系統的 itemtype (Q: 定性/半定量, S: 定量)
            # 為了相容新系統 UI，我們把 Q 映射為 1 (定量), pH 映射為 3 (數值半定量), 其餘 S 映射為 2 (文字半定量)
            cur.execute(
                "SELECT mtId AS reagent_id, mhitem AS reagent_name, mhitem AS reagent_label, "
                "CASE WHEN mhitem='pH' THEN 3 WHEN itemtype='Q' THEN 1 ELSE 2 END AS param_type "
                "FROM MhItem ORDER BY CAST(mtId AS UNSIGNED)"
            )
            return cur.fetchall()

    @staticmethod
    def get_levels_for_reagent(reagent_id: int) -> list[dict]:
        # 舊系統沒有專門的 levels 表，只分 Level 1 (L) / Level 2 (H) 等等
        return [
            {"level_id": 1, "level_name": "Level 1", "qc_material": ""},
            {"level_id": 2, "level_name": "Level 2", "qc_material": ""}
        ]

    @staticmethod
    def get_all_levels() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT mtId AS reagent_id, mhitem AS reagent_name, mhitem AS reagent_label "
                "FROM MhItem ORDER BY CAST(mtId AS UNSIGNED)"
            )
            reagents = cur.fetchall()
            
        levels = []
        for r in reagents:
            levels.append({"level_id": 1, "level_name": "Level 1", "qc_material": "", "reagent_name": r["reagent_name"], "reagent_label": r["reagent_label"], "reagent_id": r["reagent_id"]})
            levels.append({"level_id": 2, "level_name": "Level 2", "qc_material": "", "reagent_name": r["reagent_name"], "reagent_label": r["reagent_label"], "reagent_id": r["reagent_id"]})
        return levels

    @staticmethod
    def get_iqi(instrument_id: str) -> list[dict]:
        """取得某儀器的所有品管項目。舊系統透過 mhcode 關聯 MhItem。"""
        with DBContext() as (_, cur):
            cur.execute("SELECT mhcode FROM MhMaster WHERE mhId=%s", (instrument_id,))
            row = cur.fetchone()
            if not row: return []
            
            cur.execute(
                "SELECT mtId AS reagent_id, mhitem AS reagent_name, mhitem AS reagent_label, "
                "CASE WHEN mhitem='pH' THEN 3 WHEN itemtype='Q' THEN 1 ELSE 2 END AS param_type "
                "FROM MhItem WHERE mhcode=%s ORDER BY CAST(mtId AS UNSIGNED)",
                (row["mhcode"],)
            )
            reagents = cur.fetchall()
            
        items = []
        # IQI ID = {reagent_id}_{level_id} 為了相容新系統
        for r in reagents:
            items.append({
                "iqi_id": f"{r['reagent_id']}_1",
                "reagent_id": r["reagent_id"],
                "reagent_name": r["reagent_name"],
                "reagent_label": r["reagent_label"],
                "param_type": r["param_type"],
                "level_id": 1,
                "level_name": "Level 1"
            })
            items.append({
                "iqi_id": f"{r['reagent_id']}_2",
                "reagent_id": r["reagent_id"],
                "reagent_name": r["reagent_name"],
                "reagent_label": r["reagent_label"],
                "param_type": r["param_type"],
                "level_id": 2,
                "level_name": "Level 2"
            })
        return items


# ── 試劑批號管理 ───────────────────────────────────────────────

class ReagentBatchService:

    @staticmethod
    def get_all() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT b.batch_id, b.lot_number, b.expiry_date, b.open_date, "
                "b.is_active, b.is_archived, b.acceptance_status, b.notes, b.created_at, u.name AS created_by_name "
                "FROM reagent_batches b "
                "JOIN users u ON b.created_by = u.user_id "
                "ORDER BY b.created_at DESC"
            )
            return cur.fetchall()

    @staticmethod
    def get_active() -> dict | None:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT batch_id, lot_number, expiry_date, open_date "
                "FROM reagent_batches WHERE is_active=TRUE LIMIT 1"
            )
            return cur.fetchone()

    @staticmethod
    def create(lot_number: str, expiry_date, open_date, notes: str, created_by: int) -> int:
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO reagent_batches "
                "(lot_number, expiry_date, open_date, notes, created_by) "
                "VALUES (%s, %s, %s, %s, %s)",
                (lot_number, expiry_date, open_date, notes or None, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def set_active(batch_id: int):
        with DBContext() as (_, cur):
            # 將原本使用中的批號設定為已歸檔
            cur.execute("UPDATE reagent_batches SET is_archived=TRUE WHERE is_active=TRUE AND batch_id!=%s", (batch_id,))
            cur.execute("UPDATE reagent_batches SET is_active=FALSE")
            cur.execute("UPDATE reagent_batches SET is_active=TRUE WHERE batch_id=%s", (batch_id,))

    @staticmethod
    def delete(batch_id: int):
        with DBContext() as (_, cur):
            cur.execute("DELETE FROM reagent_batch_history WHERE batch_id=%s", (batch_id,))
            cur.execute("DELETE FROM reagent_batch_acceptance WHERE batch_id=%s", (batch_id,))
            cur.execute("DELETE FROM reagent_batches WHERE batch_id=%s", (batch_id,))

    @staticmethod
    def get_recent_qc_timepoints(reagent_batch_id: int, limit: int = 3) -> list:
        """獲取最近 N 次獨立的品管時間點"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT DISTINCT iDate AS result_date FROM DailyQC "
                "ORDER BY iDate DESC LIMIT %s",
                (limit,)
            )
            return [row["result_date"] for row in cur.fetchall()]

    @staticmethod
    def get_qc_results_by_time(reagent_batch_id: int, result_date) -> dict:
        """獲取特定時間點下的所有品管結果與目標範圍 (自 DailyQC 抓取)"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT d.mtId AS reagent_id, re.mhitem AS reagent_name, "
                "CASE WHEN re.mhitem='pH' THEN 3 WHEN re.itemtype='Q' THEN 1 ELSE 2 END AS param_type, "
                "b.lot_Level, d.lot AS lot_number, "
                "d.iValue AS measured_value, d.Check_Type AS qualitative_result "
                "FROM DailyQC d "
                "JOIN MhItem re ON d.mtId = re.mtId "
                "LEFT JOIN LotTable b ON d.lot = b.lot_id "
                "WHERE d.iDate=%s",
                (result_date,)
            )
            rows = cur.fetchall()
            
            data = {}
            for row in rows:
                rname = row["reagent_name"]
                if rname not in data:
                    data[rname] = {'param_type': row['param_type'], 'Level 1': None, 'Level 2': None, 'Target 1': None, 'Target 2': None}
                
                lvl_num = row["lot_Level"] or "1" # fallback if not joined
                lvl = f"Level {lvl_num}"
                
                val = row["measured_value"] if row["param_type"] in (1, 3) else row["qualitative_result"]
                data[rname][lvl] = val
                
                # Fetch target
                cur.execute(
                    "SELECT tMean AS tm, tSd AS tsd, `Range` AS semi_target FROM LotTest "
                    "WHERE mtId=%s AND lot=%s ORDER BY iDateTime DESC LIMIT 1",
                    (row["reagent_id"], row["lot_number"])
                )
                ts = cur.fetchone()
                target_str = "未設定"
                if ts:
                    if row["param_type"] == 1:
                        if ts["tm"] is not None and ts["tsd"] is not None:
                            tm, tsd = float(ts["tm"]), float(ts["tsd"])
                            target_str = f"{tm - 2*tsd:.4g} - {tm + 2*tsd:.4g}"
                    else:
                        target_str = ts["semi_target"] or "未設定"
                data[rname][f"Target {lvl_num}"] = target_str

            return data

    @staticmethod
    def save_batch_acceptance(reagent_batch_id: int, status: int, snapshot_data: dict, accepted_by: int):
        import json
        from decimal import Decimal
        class DecimalEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Decimal):
                    return float(obj)
                return super().default(obj)
                
        with DBContext() as (_, cur):
            cur.execute(
                "UPDATE reagent_batches SET acceptance_status=%s WHERE batch_id=%s",
                (status, reagent_batch_id)
            )
            cur.execute(
                "INSERT INTO reagent_batch_history (batch_id, status, snapshot_data, accepted_by) "
                "VALUES (%s, %s, %s, %s)",
                (reagent_batch_id, status, json.dumps(snapshot_data, cls=DecimalEncoder), accepted_by)
            )

    @staticmethod
    def get_acceptance_records(batch_id: int) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT a.accept_id, r.mhitem AS reagent_name, r.mhitem AS reagent_label, "
                "CONCAT('Level ', a.level_id) AS level_name, a.accept_type, a.semi_result, a.semi_expected, "
                "a.semi_pass, a.calc_mean, a.calc_sd, a.result, "
                "a.accepted_at, u.name AS accepted_by_name, a.notes "
                "FROM reagent_batch_acceptance a "
                "JOIN MhItem r ON a.reagent_id = r.mtId "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE a.batch_id=%s ORDER BY CAST(r.mtId AS UNSIGNED), a.level_id",
                (batch_id,)
            )
            return cur.fetchall()

    @staticmethod
    def save_acceptance(batch_id: int, reagent_id: int, level_id: int,
                        accept_type: int, semi_result: str, semi_expected: str,
                        semi_pass: bool, measured_values: list, calc_mean: float,
                        calc_sd: float, result: bool, notes: str, accepted_by: int):
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO reagent_batch_acceptance "
                "(batch_id, reagent_id, level_id, accept_type, semi_result, semi_expected, "
                "semi_pass, measured_values, calc_mean, calc_sd, result, notes, accepted_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (batch_id, reagent_id, level_id, accept_type,
                 semi_result, semi_expected, semi_pass,
                 json.dumps(measured_values) if measured_values else None,
                 calc_mean, calc_sd, result, notes or None, accepted_by)
            )


# ── 品管液批號管理 ─────────────────────────────────────────────

class QCBatchService:

    @staticmethod
    def save_qc_batch_acceptance(batch_id: str, status: int):
        with DBContext() as (_, cur):
            cur.execute("UPDATE LotTable SET acceptance_status=%s WHERE lot_id=%s", (str(status), batch_id))

    @staticmethod
    def get_qc_batch_stats(batch_id: str, start_date, end_date) -> dict:
        stats = {"qual": {}, "quant": {}}
        import math
        
        with DBContext() as (_, cur):
            cur.execute("SELECT lot, lot_Level FROM LotTable WHERE lot_id=%s", (batch_id,))
            b_row = cur.fetchone()
            if not b_row: return stats
            lot = b_row["lot"]
            level_id = b_row["lot_Level"]
            
            cur.execute(
                "SELECT mtId AS reagent_id, mhitem AS reagent_name, "
                "CASE WHEN mhitem='pH' THEN 3 WHEN itemtype='Q' THEN 1 ELSE 2 END AS param_type "
                "FROM MhItem"
            )
            is_chem_lot = lot.upper().startswith('C')
            is_sed_lot = lot.upper().startswith('D')
            
            reagents = {}
            for r in cur.fetchall():
                is_sed_reagent = r["reagent_name"] in ("RBC", "WBC")
                if is_chem_lot and is_sed_reagent:
                    continue
                if is_sed_lot and not is_sed_reagent:
                    continue
                reagents[str(r["reagent_id"])] = r
            
            cur.execute(
                "SELECT mtId, iValue, Check_Type, sdFlag "
                "FROM DailyQC "
                "WHERE lot=%s AND iDate BETWEEN %s AND %s",
                (batch_id, f"{start_date} 00:00:00", f"{end_date} 23:59:59")
            )
            rows = cur.fetchall()
            
            for rid, rinfo in reagents.items():
                iqi_id = f"{rid}_{level_id}"
                ts = TargetSettingService.get_for_batch(iqi_id, batch_id)
                if not ts: ts = TargetSettingService.get_current(iqi_id)
                
                if rinfo["param_type"] in (2, 3):
                    rng_str = "—"
                    s_min, s_max = None, None
                    if ts and ts.get("semi_target_min"):
                        s_min = ts.get("semi_target_min")
                        s_max = ts.get("semi_target_max")
                        rng_str = f"{s_min} ~ {s_max}" if s_min != s_max else str(s_min)
                    
                    stats["qual"][rinfo["reagent_name"]] = {
                        "n": 0, "passed": 0, "failed": 0, "range": rng_str, "reagent_id": rid,
                        "s_min": s_min, "s_max": s_max
                    }
                else:
                    tm = ts["tm"] if ts and ts.get("tm") is not None else None
                    tsd = ts["tsd"] if ts and ts.get("tsd") is not None else None
                    stats["quant"][rinfo["reagent_name"]] = {
                        "n": 0, "tm": tm, "tsd": tsd, "am": None, "asd": None,
                        "values": [], "reagent_id": rid
                    }
                    
            for row in rows:
                rid = str(row["mtId"])
                rinfo = reagents.get(rid)
                if not rinfo: continue
                rname = rinfo["reagent_name"]
                
                if rinfo["param_type"] in (2, 3):
                    stats["qual"][rname]["n"] += 1
                    if row["sdFlag"] == 0:
                        stats["qual"][rname]["passed"] += 1
                    else:
                        stats["qual"][rname]["failed"] += 1
                else:
                    v = row["iValue"]
                    if v is not None:
                        stats["quant"][rname]["n"] += 1
                        stats["quant"][rname]["values"].append(v)
                        
            for rname, data in stats["quant"].items():
                vals = data["values"]
                if len(vals) > 0:
                    am = sum(vals) / len(vals)
                    data["am"] = am
                    if len(vals) > 1:
                        variance = sum((x - am) ** 2 for x in vals) / (len(vals) - 1)
                        data["asd"] = math.sqrt(variance)
                    else:
                        data["asd"] = 0.0
                del data["values"]
                
        return stats

    @staticmethod
    def get_all() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT lot_id AS batch_id, "
                "CASE WHEN lot_Level='1' THEN 1 ELSE 2 END AS level_id, "
                "CASE WHEN lot_Level='1' THEN 'Level 1' ELSE 'Level 2' END AS level_name, "
                "lot AS lot_number, QC_date AS open_date, expiry_date, Writedate AS created_at, "
                "iUser AS created_by_name, is_active, is_archived, acceptance_status, '' AS notes "
                "FROM LotTable ORDER BY lot, lot_Level"
            )
            rows = cur.fetchall()
            
            groups = {}
            for r in rows:
                lot = r["lot_number"]
                if lot not in groups:
                    groups[lot] = {
                        "lot_number": lot,
                        "open_date": r["open_date"],
                        "expiry_date": r["expiry_date"],
                        "created_at": r["created_at"],
                        "created_by_name": r["created_by_name"],
                        "is_active": r["is_active"],
                        "is_archived": r["is_archived"],
                        "acceptance_status": r["acceptance_status"],
                        "notes": r["notes"],
                        "sub_lots": []
                    }
                groups[lot]["sub_lots"].append({
                    "batch_id": r["batch_id"],
                    "level_id": r["level_id"],
                    "level_name": r["level_name"]
                })
            
            # Sort by created_at descending
            def get_time(dt):
                if not dt: return ""
                if isinstance(dt, str): return dt
                return dt.strftime("%Y-%m-%d %H:%M:%S")
                
            return sorted(list(groups.values()), key=lambda x: get_time(x["created_at"]), reverse=True)

    @staticmethod
    def get_active_sub_batch_id(level_id: str, prefix: str) -> str | None:
        from database.connection import DBContext
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT lot_id FROM LotTable "
                "WHERE lot_Level=%s AND is_active=1 AND UPPER(lot) LIKE %s "
                "ORDER BY Writedate DESC LIMIT 1",
                (level_id, f"{prefix}%")
            )
            row = cur.fetchone()
            return row["lot_id"] if row else None

    @staticmethod
    def get_active_batches() -> list[dict]:
        """取得目前使用中的品管液批號。舊系統只分 Level 1 和 Level 2，用 lot_Level 區分。"""
        with DBContext() as (_, cur):
            # 取最新的一筆 level 1 和 level 2
            batches = []
            cur.execute("SELECT lot_id AS batch_id, 1 AS level_id, 'Level 1' AS level_name, lot AS lot_number, expiry_date FROM LotTable WHERE lot_Level='1' AND is_active=1 ORDER BY Writedate DESC LIMIT 1")
            l1 = cur.fetchone()
            if l1: batches.append(l1)
            
            cur.execute("SELECT lot_id AS batch_id, 2 AS level_id, 'Level 2' AS level_name, lot AS lot_number, expiry_date FROM LotTable WHERE lot_Level='2' AND is_active=1 ORDER BY Writedate DESC LIMIT 1")
            l2 = cur.fetchone()
            if l2: batches.append(l2)
            
            return batches

    @staticmethod
    def create_mother_batch(mother_lot: str, l1_lot_id: str, l2_lot_id: str, expiry_date, open_date,
                            notes: str, created_by: int) -> str:
        with DBContext() as (_, cur):
            from datetime import datetime
            import uuid
            now = datetime.now()
            
            l1_id = l1_lot_id if l1_lot_id else str(uuid.uuid4())
            l2_id = l2_lot_id if l2_lot_id else str(uuid.uuid4())
            
            # Insert L1
            cur.execute(
                "INSERT INTO LotTable (lot, lot_id, lot_Level, QC_date, expiry_date, Writedate, iUser, is_active, is_archived, acceptance_status) "
                "VALUES (%s,%s,'1',%s,%s,%s,%s, 0, 0, 'pending')",
                (mother_lot, l1_id, open_date, expiry_date, now, "Admin"),
            )
            # Insert L2
            cur.execute(
                "INSERT INTO LotTable (lot, lot_id, lot_Level, QC_date, expiry_date, Writedate, iUser, is_active, is_archived, acceptance_status) "
                "VALUES (%s,%s,'2',%s,%s,%s,%s, 0, 0, 'pending')",
                (mother_lot, l2_id, open_date, expiry_date, now, "Admin"),
            )
            return mother_lot

    @staticmethod
    def toggle_active(mother_lot: str, is_active: bool):
        with DBContext() as (_, cur):
            if is_active:
                cur.execute("UPDATE LotTable SET is_active=1, is_archived=0 WHERE lot=%s", (mother_lot,))
            else:
                cur.execute("UPDATE LotTable SET is_active=0, is_archived=1 WHERE lot=%s", (mother_lot,))

    @staticmethod
    def delete(mother_lot: str):
        with DBContext() as (_, cur):
            # Also delete associated Target Settings (LotTest uses lot_id as lot)
            cur.execute("SELECT lot_id FROM LotTable WHERE lot=%s", (mother_lot,))
            rows = cur.fetchall()
            for row in rows:
                cur.execute("DELETE FROM LotTest WHERE lot=%s", (row["lot_id"],))
            cur.execute("DELETE FROM LotTable WHERE lot=%s", (mother_lot,))

    @staticmethod
    def get_acceptance_records(qc_batch_id: int) -> list[dict]:
        return []

    @staticmethod
    def save_acceptance(*args, **kwargs):
        pass


# ── TM / TSD 設定 ─────────────────────────────────────────────

class TargetSettingService:

    @staticmethod
    def _parse_semi_range(row: dict | None) -> dict | None:
        if row and row.get("semi_target_min"):
            rng = row["semi_target_min"]
            if "-" in rng and not rng.startswith("-"):
                parts = rng.split("-")
                if len(parts) == 2:
                    row["semi_target_min"] = parts[0].strip()
                    row["semi_target_max"] = parts[1].strip()
        return row

    @staticmethod
    def get_current(iqi_id: str) -> dict | None:
        return TargetSettingService.get_for_batch(iqi_id, None)

    @staticmethod
    def get_for_batch(iqi_id: str, qc_batch_id: int | None) -> dict | None:
        # iqi_id = f"{reagent_id}_{level_id}"
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            if qc_batch_id:
                lot = qc_batch_id
            else:
                cur.execute("SELECT lot_id FROM LotTable WHERE lot_Level=%s AND is_active=1 ORDER BY Writedate DESC LIMIT 1", (level_id,))
                row = cur.fetchone()
                if not row: return None
                lot = row["lot_id"]
                
            cur.execute(
                "SELECT ltId AS setting_id, tMean AS tm, tSd AS tsd, TEA AS tea_percent, "
                "`Range` AS semi_target_min, `Range` AS semi_target_max, "
                "0 AS mode, iDateTime AS effective_from, iDateTime AS set_at, '' AS change_reason "
                "FROM LotTest "
                "WHERE mtId=%s AND lot=%s ORDER BY iDateTime DESC LIMIT 1",
                (reagent_id, lot)
            )
            return TargetSettingService._parse_semi_range(cur.fetchone())

    @staticmethod
    def get_history(iqi_id: str) -> list[dict]:
        reagent_id, _ = iqi_id.split('_')
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT ltId AS setting_id, tMean AS tm, tSd AS tsd, TEA AS tea_percent, "
                "`Range` AS semi_target_min, `Range` AS semi_target_max, "
                "iDateTime AS effective_from, iDateTime AS set_at, "
                "iUser AS set_by_name, '' AS change_reason "
                "FROM LotTest "
                "WHERE mtId=%s ORDER BY iDateTime DESC",
                (reagent_id,)
            )
            return [TargetSettingService._parse_semi_range(r) for r in cur.fetchall()]

    @staticmethod
    def get_by_batch(qc_batch_id: int) -> dict:
        """Returns a dict mapping iqi_id to its target setting for a given batch."""
        with DBContext() as (_, cur):
            cur.execute("SELECT lot, lot_Level FROM LotTable WHERE lot_id=%s", (qc_batch_id,))
            b_row = cur.fetchone()
            if not b_row: return {}
            
            cur.execute(
                "SELECT mtId AS reagent_id, ltId AS setting_id, tMean AS tm, tSd AS tsd, TEA AS tea_percent, "
                "`Range` AS semi_target_min, `Range` AS semi_target_max, "
                "0 AS mode, iDateTime AS effective_from, iDateTime AS set_at, '' AS change_reason "
                "FROM LotTest WHERE lot=%s ORDER BY iDateTime DESC",
                (qc_batch_id,)
            )
            rows = cur.fetchall()
            res = {}
            for r in rows:
                iqi = f"{r['reagent_id']}_{b_row['lot_Level']}"
                if iqi not in res:
                    res[iqi] = TargetSettingService._parse_semi_range(r)
            return res

    @staticmethod
    def save(iqi_id: str, qc_batch_id: str, tm: float, tsd: float,
             cva: float, tea: float, mode: int, effective_from: date, set_by: int, change_reason: str = None):
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            cur.execute("SELECT mhId FROM LotTable WHERE lot_id=%s", (qc_batch_id,))
            b_row = cur.fetchone()
            if not b_row: return
            from datetime import datetime
            
            cur.execute(
                "INSERT INTO LotTest "
                "(mhId, cId, mtId, lot, tMean, tSd, CVA, TEA, iDateTime, iUser, LotStyle) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (b_row["mhId"], "", reagent_id, qc_batch_id, tm, tsd, cva, tea, datetime.now(), "Admin", "N")
            )

    @staticmethod
    def save_semi_target(iqi_id: str, qc_batch_id: str, semi_min: str, semi_max: str,
                         mode: int, effective_from: date, set_by: int, change_reason: str = None):
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            cur.execute("SELECT mhId FROM LotTable WHERE lot_id=%s", (qc_batch_id,))
            b_row = cur.fetchone()
            if not b_row: return
            from datetime import datetime
            
            # Use semi_max for range
            rng = f"{semi_min}-{semi_max}" if semi_min != semi_max else semi_max
            cur.execute(
                "INSERT INTO LotTest "
                "(mhId, cId, mtId, lot, `Range`, iDateTime, iUser, LotStyle) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (b_row["mhId"], "", reagent_id, qc_batch_id, rng, datetime.now(), "Admin", "N")
            )


# ── 每日品管結果 ───────────────────────────────────────────────

class QCResultService:

    @staticmethod
    def save_result(iqi_id: str, result_date: date,
                    reagent_batch_id: int | None, qc_batch_id: int | None,
                    measured_value: float | None, qualitative_result: str | None,
                    notes: str, entered_by: int, source: int = 1, instrument_id: str = None) -> int:
        """儲存單筆品管結果，自動進行 Westgard 判斷。"""
        is_accepted, westgard_flag = QCResultService._check_westgard(
            iqi_id, result_date, measured_value, qualitative_result, qc_batch_id
        )
        
        reagent_id, level_id = iqi_id.split('_')
        
        with DBContext() as (_, cur):
            # Fetch lot name and mhId
            lot_id_to_save = qc_batch_id if qc_batch_id else ""
            mhId = instrument_id if instrument_id else ""
            if qc_batch_id:
                cur.execute("SELECT mhId FROM LotTable WHERE lot_id=%s", (qc_batch_id,))
                r = cur.fetchone()
                if r and not mhId and r["mhId"]:
                    mhId = r["mhId"]
                    
            from datetime import datetime
            now = datetime.now()
            # source=1 usually means manual entry
            check_type = qualitative_result if qualitative_result else ""
            sd_flag_val = 0 if is_accepted else 1 # Simple mapping for sdFlag
            
            if isinstance(result_date, datetime):
                dt_val = result_date
            else:
                dt_val = datetime.combine(result_date, datetime.min.time())
                
            cur.execute(
                "INSERT INTO DailyQC "
                "(mhId, mtId, iValue, iDate, iUser, lot, sdFlag, sysTime, Check_Type) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (mhId, reagent_id, measured_value, dt_val, 
                 "Admin", lot_id_to_save, sd_flag_val, now, check_type)
            )
            return cur.lastrowid

    @staticmethod
    def get_results(iqi_id: str, from_date: date, to_date: date, instrument_id: str = None) -> list[dict]:
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            query = (
                "SELECT d.dqcId AS result_id, d.iDate AS result_date, d.iValue AS measured_value, "
                "d.lot AS qc_batch_id, b.lot AS base_lot_number, d.Check_Type AS qualitative_result, "
                "CASE WHEN d.sdFlag=0 THEN 1 ELSE 0 END AS is_accepted, '' AS westgard_flag, "
                "1 AS source, IFNULL(n.notes, '') AS notes, d.sysTime AS entered_at, d.iUser AS entered_by_name, "
                "EXISTS(SELECT 1 FROM QCaberrant a WHERE a.dqcId = d.dqcId) AS has_anomaly "
                "FROM DailyQC d "
                "LEFT JOIN DailyQC_notes n ON d.dqcId = n.dqcId "
                "JOIN LotTable b ON b.lot_id = d.lot AND b.lot_Level=%s "
                "WHERE d.mtId=%s AND d.iDate >= %s AND d.iDate <= %s "
            )
            params = [level_id, reagent_id, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if instrument_id:
                query += " AND d.mhId=%s "
                params.append(instrument_id)
                
            query += "ORDER BY d.iDate ASC, d.sysTime ASC"
            
            cur.execute(query, params)
            return cur.fetchall()

    @staticmethod
    def update_note(result_id: int, notes: str):
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO DailyQC_notes (dqcId, notes) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE notes = VALUES(notes)",
                (result_id, notes)
            )

    @staticmethod
    def get_total_stats(iqi_id: str, qc_batch_id: int = None, instrument_id: str = None) -> dict:
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            if qc_batch_id is not None:
                cur.execute("SELECT lot FROM LotTable WHERE lot_id=%s", (qc_batch_id,))
                r = cur.fetchone()
                if not r: return {"n": 0, "mean": None, "sd": None, "accept": 0, "reject": 0}
                
                query = (
                    "SELECT iValue AS measured_value, Check_Type AS qualitative_result, "
                    "CASE WHEN sdFlag=0 THEN 1 ELSE 0 END AS is_accepted "
                    "FROM DailyQC WHERE mtId=%s AND lot=%s"
                )
                params = [reagent_id, qc_batch_id]
            else:
                query = (
                    "SELECT iValue AS measured_value, Check_Type AS qualitative_result, "
                    "CASE WHEN sdFlag=0 THEN 1 ELSE 0 END AS is_accepted "
                    "FROM DailyQC WHERE mtId=%s"
                )
                params = [reagent_id]
                
            if instrument_id:
                query += " AND mhId=%s"
                params.append(instrument_id)
                
            cur.execute(query, params)
            rows = cur.fetchall()
            
        stats = {"n": len(rows), "mean": None, "sd": None, "accept": 0, "reject": 0}
        if not rows: return stats
        
        valid_vals = [float(r["measured_value"]) for r in rows if r["measured_value"] is not None]
        if valid_vals:
            import numpy as np
            stats["mean"] = float(np.mean(valid_vals))
            if len(valid_vals) > 1:
                stats["sd"] = float(np.std(valid_vals, ddof=1))
        
        for r in rows:
            if r["is_accepted"] == 0:
                stats["reject"] += 1
            else:
                stats["accept"] += 1
            
        return stats

    @staticmethod
    def _check_westgard(iqi_id: str, result_date: date,
                        value: float | None, qualitative: str | None,
                        qc_batch_id: int | None = None
                        ) -> tuple[bool, str | None]:
        """
        檢查 Westgard rules：1-3S、2-2S、R-4S
        回傳 (is_accepted, flag_string)
        如果是半定量，則檢查是否在設定的文字範圍內。
        """
        if qc_batch_id:
            ts = TargetSettingService.get_for_batch(iqi_id, qc_batch_id)
        else:
            ts = TargetSettingService.get_current(iqi_id)
            
        if not ts:
            return True, None

        if value is None and qualitative is not None:
            # 半定量判定
            s_min = ts.get("semi_target_min")
            s_max = ts.get("semi_target_max")
            if not s_min or not s_max:
                return True, None
                
            reagent_id = iqi_id.split('_')[0]
            rname = ""
            from database.connection import DBContext
            with DBContext() as (_, cur):
                cur.execute("SELECT mhitem FROM MhItem WHERE mtId=%s", (reagent_id,))
                r = cur.fetchone()
                if r: rname = r["mhitem"]
                
            if rname == "NIT":
                levels = {"Neg": 0, "Pos": 1}
            else:
                levels = {"Neg": 0, "1+": 1, "2+": 2, "3+": 3, "4+": 4}
            q_val = levels.get(qualitative)
            
            min_lbl = str(s_min)
            max_lbl = str(s_max)
                
            min_val = levels.get(min_lbl)
            max_val = levels.get(max_lbl)
            
            if q_val is not None and min_val is not None and max_val is not None:
                if min_val <= q_val <= max_val:
                    return True, None
                else:
                    return False, "Out of Range"
            return True, None

        if not ts or ts.get("tm") is None or ts.get("tsd") is None:
            return True, None

        tm  = float(ts["tm"])
        tsd = float(ts["tsd"])
        if tsd == 0:
            return True, None

        z = round((value - tm) / tsd, 6)

        # 1-3S：超出 ±3SD
        if abs(z) > 3:
            return False, "1-3S"

        # 2-2S 需要前一筆
        prev = QCResultService._get_previous_value(iqi_id, result_date)
        if prev is not None:
            z_prev = round((prev - tm) / tsd, 6)
            # 2-2S：連續兩點同側超出 ±2SD
            if z > 2 and z_prev > 2:
                return False, "2-2S"
            if z < -2 and z_prev < -2:
                return False, "2-2S"

        # 1-2S：超出 ±2SD
        if abs(z) > 2:
            return False, "1-2S"

        return True, None

    @staticmethod
    def _get_previous_value(iqi_id: str, before_date: date) -> float | None:
        reagent_id, level_id = iqi_id.split('_')
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT iValue FROM DailyQC "
                "WHERE mtId=%s AND iDate < %s AND iValue IS NOT NULL "
                "ORDER BY iDate DESC LIMIT 1",
                (reagent_id, f"{before_date} 00:00:00")
            )
            row = cur.fetchone()
        return float(row["iValue"]) if row and row["iValue"] is not None else None


# ── 統計計算工具 ───────────────────────────────────────────────

def calc_stats(values: list[float]) -> tuple[float, float, float]:
    """回傳 (mean, sd, cv%)"""
    if not values:
        return 0.0, 0.0, 0.0
    n = len(values)
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n if n > 1 else 0
    sd = math.sqrt(variance)
    cv = (sd / mean * 100) if mean != 0 else 0.0
    return round(mean, 4), round(sd, 4), round(cv, 2)
