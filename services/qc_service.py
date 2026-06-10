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
            cur.execute("SELECT instrument_id, instrument_name FROM instruments ORDER BY instrument_id")
            return cur.fetchall()

    @staticmethod
    def get_reagents() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT reagent_id, reagent_name, reagent_label, param_type "
                "FROM reagents ORDER BY display_order"
            )
            return cur.fetchall()

    @staticmethod
    def get_levels_for_reagent(reagent_id: int) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT level_id, level_name, qc_material FROM qc_levels "
                "WHERE reagent_id=%s ORDER BY level_id",
                (reagent_id,)
            )
            return cur.fetchall()

    @staticmethod
    def get_all_levels() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT l.level_id, l.level_name, l.qc_material, "
                "r.reagent_name, r.reagent_label "
                "FROM qc_levels l JOIN reagents r ON l.reagent_id=r.reagent_id "
                "ORDER BY l.reagent_id, l.level_id"
            )
            return cur.fetchall()

    @staticmethod
    def get_iqi(instrument_id: int) -> list[dict]:
        """取得某儀器的所有品管項目（含參數和濃度資訊）。"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT i.iqi_id, r.reagent_id, r.reagent_name, r.reagent_label, "
                "r.param_type, l.level_id, l.level_name "
                "FROM instrument_qc_items i "
                "JOIN reagents r ON i.reagent_id = r.reagent_id "
                "JOIN qc_levels l ON i.level_id = l.level_id "
                "WHERE i.instrument_id = %s "
                "ORDER BY r.display_order, l.level_id",
                (instrument_id,)
            )
            return cur.fetchall()


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
    def get_recent_qc_timepoints(reagent_batch_id: int, limit: int = 3) -> list:
        """獲取某試劑批號最近 N 次獨立的品管時間點"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT DISTINCT result_date FROM qc_results "
                "WHERE reagent_batch_id=%s ORDER BY result_date DESC LIMIT %s",
                (reagent_batch_id, limit)
            )
            return [row["result_date"] for row in cur.fetchall()]

    @staticmethod
    def get_qc_results_by_time(reagent_batch_id: int, result_date) -> dict:
        """獲取特定時間點下，該試劑批號的所有品管結果與目標範圍 (以 iqi_id 抓取範圍)"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT res.iqi_id, r.reagent_name, l.level_name, r.param_type, "
                "res.measured_value, res.qualitative_result "
                "FROM qc_results res "
                "JOIN instrument_qc_items iqi ON res.iqi_id = iqi.iqi_id "
                "JOIN qc_levels l ON iqi.level_id = l.level_id "
                "JOIN reagents r ON l.reagent_id = r.reagent_id "
                "WHERE res.reagent_batch_id=%s AND res.result_date=%s",
                (reagent_batch_id, result_date)
            )
            rows = cur.fetchall()
            
            # Fetch targets
            data = {}
            for row in rows:
                rname = row["reagent_name"]
                if rname not in data:
                    data[rname] = {'param_type': row['param_type'], 'Level 1': None, 'Level 2': None, 'Target 1': None, 'Target 2': None}
                
                lvl = row["level_name"]
                val = row["measured_value"] if row["param_type"] in (1, 3) else row["qualitative_result"]
                data[rname][lvl] = val
                
                # Fetch target
                cur.execute(
                    "SELECT tm, tsd, semi_target_min, semi_target_max FROM qc_target_settings "
                    "WHERE iqi_id=%s ORDER BY effective_from DESC, set_at DESC LIMIT 1",
                    (row["iqi_id"],)
                )
                ts = cur.fetchone()
                target_str = "未設定"
                if ts:
                    if row["param_type"] == 1:
                        if ts["tm"] is not None and ts["tsd"] is not None:
                            tm, tsd = float(ts["tm"]), float(ts["tsd"])
                            target_str = f"{tm - 2*tsd:.4g} - {tm + 2*tsd:.4g}"
                    else:
                        s_min = ts["semi_target_min"]
                        s_max = ts["semi_target_max"]
                        if s_min and s_max:
                            target_str = f"{s_min} - {s_max}" if s_min != s_max else s_min
                data[rname][f"Target {lvl[-1]}"] = target_str

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
                "INSERT INTO reagent_batch_acceptance (reagent_batch_id, status, snapshot_data, accepted_by) "
                "VALUES (%s, %s, %s, %s)",
                (reagent_batch_id, status, json.dumps(snapshot_data, cls=DecimalEncoder), accepted_by)
            )

    @staticmethod
    def get_acceptance_records(batch_id: int) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT a.accept_id, r.reagent_name, r.reagent_label, "
                "l.level_name, a.accept_type, a.semi_result, a.semi_expected, "
                "a.semi_pass, a.calc_mean, a.calc_sd, a.result, "
                "a.accepted_at, u.name AS accepted_by_name, a.notes "
                "FROM reagent_batch_acceptance a "
                "JOIN reagents r ON a.reagent_id = r.reagent_id "
                "JOIN qc_levels l ON a.level_id = l.level_id "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE a.batch_id=%s ORDER BY r.display_order, l.level_id",
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
    def save_qc_batch_acceptance(batch_id: int, status: int):
        from database.connection import DBContext
        with DBContext() as (_, cur):
            cur.execute("UPDATE qc_batches SET acceptance_status=%s WHERE batch_id=%s", (status, batch_id))

    @staticmethod
    def get_qc_batch_stats(batch_id: int, start_date, end_date) -> dict:
        from database.connection import DBContext
        import statistics
        
        # We need to get all qc_results for this batch between dates
        stats = {"qual": {}, "quant": {}}
        
        with DBContext() as (_, cur):
            # Fetch qualitative results
            cur.execute(
                "SELECT res.iqi_id, r.reagent_name, r.reagent_label, "
                "COALESCE(res.qualitative_result, CAST(res.measured_value AS CHAR)) AS qualitative_result, "
                "ts.semi_target_min, ts.semi_target_max "
                "FROM qc_results res "
                "JOIN instrument_qc_items iqi ON res.iqi_id = iqi.iqi_id "
                "JOIN reagents r ON iqi.reagent_id = r.reagent_id "
                "LEFT JOIN qc_target_settings ts ON ts.setting_id = ("
                "  SELECT setting_id FROM qc_target_settings ts2 "
                "  WHERE ts2.iqi_id = res.iqi_id AND ts2.qc_batch_id = res.qc_batch_id "
                "  ORDER BY set_at DESC LIMIT 1"
                ") "
                "WHERE res.qc_batch_id=%s AND r.param_type IN (2, 3) "
                "AND DATE(res.result_date) BETWEEN %s AND %s",
                (batch_id, start_date, end_date)
            )
            qual_rows = cur.fetchall()
            
            # Fetch quantitative results
            cur.execute(
                "SELECT res.iqi_id, r.reagent_name, r.reagent_label, res.measured_value, "
                "ts.tm, ts.tsd "
                "FROM qc_results res "
                "JOIN instrument_qc_items iqi ON res.iqi_id = iqi.iqi_id "
                "JOIN reagents r ON iqi.reagent_id = r.reagent_id "
                "LEFT JOIN qc_target_settings ts ON ts.setting_id = ("
                "  SELECT setting_id FROM qc_target_settings ts2 "
                "  WHERE ts2.iqi_id = res.iqi_id AND ts2.qc_batch_id = res.qc_batch_id "
                "  ORDER BY set_at DESC LIMIT 1"
                ") "
                "WHERE res.qc_batch_id=%s AND r.param_type=1 "
                "AND DATE(res.result_date) BETWEEN %s AND %s",
                (batch_id, start_date, end_date)
            )
            quant_rows = cur.fetchall()
            
            # Process Qual
            for row in qual_rows:
                rname = row["reagent_name"]
                if rname not in stats["qual"]:
                    rng = "未設定"
                    if row["semi_target_min"] and row["semi_target_max"]:
                        rng = f"{row['semi_target_min']} - {row['semi_target_max']}" if row['semi_target_min'] != row['semi_target_max'] else row['semi_target_min']
                    
                    stats["qual"][rname] = {
                        "label": row["reagent_label"],
                        "range": rng,
                        "s_min": row["semi_target_min"],
                        "s_max": row["semi_target_max"],
                        "n": 0,
                        "passed": 0,
                        "failed": 0
                    }
                
                # Check pass/fail (simple matching for now, as we don't have full ordinal comparison in SQL easily)
                res = row["qualitative_result"]
                s_min = row["semi_target_min"]
                s_max = row["semi_target_max"]
                
                passed = False
                if res and s_min and s_max:
                    SEMI_ORDER = {"Neg": 0, "Trace": 1, "1+": 2, "2+": 3, "3+": 4}
                    if res in SEMI_ORDER and s_min in SEMI_ORDER and s_max in SEMI_ORDER:
                        if SEMI_ORDER[s_min] <= SEMI_ORDER[res] <= SEMI_ORDER[s_max]:
                            passed = True
                
                stats["qual"][rname]["n"] += 1
                if passed:
                    stats["qual"][rname]["passed"] += 1
                else:
                    stats["qual"][rname]["failed"] += 1
                    
            # Process Quant
            quant_grouped = {}
            for row in quant_rows:
                rname = row["reagent_name"]
                if rname not in quant_grouped:
                    quant_grouped[rname] = {
                        "label": row["reagent_label"],
                        "values": [],
                        "tm": row["tm"],
                        "tsd": row["tsd"]
                    }
                val = row["measured_value"]
                if val is not None:
                    quant_grouped[rname]["values"].append(float(val))
                    
            for rname, data in quant_grouped.items():
                vals = data["values"]
                am = statistics.mean(vals) if vals else None
                asd = statistics.stdev(vals) if len(vals) > 1 else (0.0 if len(vals)==1 else None)
                
                stats["quant"][rname] = {
                    "label": data["label"],
                    "tm": data["tm"],
                    "tsd": data["tsd"],
                    "am": am,
                    "asd": asd,
                    "n": len(vals)
                }
                
        return stats

    @staticmethod
    def get_all() -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT b.batch_id, b.level_id, l.level_name, "
                "r.reagent_name, r.reagent_label, "
                "b.lot_number, b.expiry_date, b.open_date, b.is_active, b.is_archived, "
                "b.notes, b.created_at, u.name AS created_by_name "
                "FROM qc_batches b "
                "JOIN qc_levels l ON b.level_id = l.level_id "
                "JOIN reagents r ON l.reagent_id = r.reagent_id "
                "JOIN users u ON b.created_by = u.user_id "
                "ORDER BY b.created_at DESC"
            )
            return cur.fetchall()

    @staticmethod
    def get_active_batches() -> list[dict]:
        """取得目前使用中的品管液批號（Level 1 & Level 2，每個 level 各一筆）。"""
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT b.batch_id, b.level_id, l.level_name, b.lot_number, b.expiry_date "
                "FROM qc_batches b JOIN qc_levels l ON b.level_id = l.level_id "
                "WHERE b.is_active=TRUE"
            )
            return cur.fetchall()

    @staticmethod
    def create(level_id: int, lot_number: str, expiry_date, open_date,
               notes: str, created_by: int) -> int:
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO qc_batches "
                "(level_id, lot_number, expiry_date, open_date, notes, created_by) "
                "VALUES (%s,%s,%s,%s,%s,%s)",
                (level_id, lot_number, expiry_date, open_date, notes or None, created_by),
            )
            return cur.lastrowid

    @staticmethod
    def set_active(batch_id: int, level_id: int):
        """將指定 level 的其他批號停用並退役，啟用此批號。"""
        with DBContext() as (_, cur):
            cur.execute(
                "UPDATE qc_batches SET is_archived=TRUE WHERE is_active=TRUE AND level_id=%s AND batch_id!=%s",
                (level_id, batch_id)
            )
            cur.execute(
                "UPDATE qc_batches SET is_active=FALSE WHERE level_id=%s", (level_id,)
            )
            cur.execute(
                "UPDATE qc_batches SET is_active=TRUE, is_archived=FALSE WHERE batch_id=%s", (batch_id,)
            )

    @staticmethod
    def get_acceptance_records(qc_batch_id: int) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT a.accept_id, r.reagent_name, r.reagent_label, "
                "a.accept_type, a.semi_result, a.semi_expected, a.semi_pass, "
                "a.calc_mean, a.calc_sd, a.result, "
                "a.accepted_at, u.name AS accepted_by_name, a.notes, a.measured_values "
                "FROM qc_batch_acceptance a "
                "JOIN reagents r ON a.reagent_id = r.reagent_id "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE a.qc_batch_id=%s ORDER BY r.display_order",
                (qc_batch_id,)
            )
            return cur.fetchall()

    @staticmethod
    def save_acceptance(qc_batch_id: int, reagent_id: int, accept_type: int,
                        semi_result: str, semi_expected: str, semi_pass: bool,
                        measured_values: list, calc_mean: float, calc_sd: float,
                        result: bool, notes: str, accepted_by: int):
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO qc_batch_acceptance "
                "(qc_batch_id, reagent_id, accept_type, semi_result, semi_expected, "
                "semi_pass, measured_values, calc_mean, calc_sd, result, notes, accepted_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (qc_batch_id, reagent_id, accept_type,
                 semi_result, semi_expected, semi_pass,
                 json.dumps(measured_values) if measured_values else None,
                 calc_mean, calc_sd, result, notes or None, accepted_by)
            )


# ── TM / TSD 設定 ─────────────────────────────────────────────

class TargetSettingService:

    @staticmethod
    def get_current(iqi_id: int) -> dict | None:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT setting_id, tm, tsd, cva_percent, tea_percent, semi_target_min, semi_target_max, mode, effective_from, set_at, change_reason "
                "FROM qc_target_settings "
                "WHERE iqi_id=%s ORDER BY effective_from DESC, set_at DESC LIMIT 1",
                (iqi_id,)
            )
            return cur.fetchone()

    @staticmethod
    def get_for_batch(iqi_id: int, qc_batch_id: int) -> dict | None:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT setting_id, tm, tsd, cva_percent, tea_percent, semi_target_min, semi_target_max, mode, effective_from, set_at, change_reason "
                "FROM qc_target_settings "
                "WHERE iqi_id=%s AND qc_batch_id=%s ORDER BY set_at DESC LIMIT 1",
                (iqi_id, qc_batch_id)
            )
            return cur.fetchone()

    @staticmethod
    def get_history(iqi_id: int) -> list[dict]:
        from database.connection import DBContext
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT s.*, u.name as set_by_name "
                "FROM qc_target_settings s "
                "JOIN users u ON s.set_by = u.user_id "
                "WHERE s.iqi_id = %s "
                "ORDER BY s.effective_from DESC, s.set_at DESC",
                (iqi_id,)
            )
            return cur.fetchall()

    @staticmethod
    def get_by_batch(qc_batch_id: int) -> dict:
        """Returns a dict mapping iqi_id to its target setting for a given batch."""
        from database.connection import DBContext
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT iqi_id, tm, tsd, cva_percent, tea_percent, semi_target_min, semi_target_max, mode, effective_from, set_at, change_reason "
                "FROM qc_target_settings "
                "WHERE qc_batch_id=%s ORDER BY set_at DESC",
                (qc_batch_id,)
            )
            rows = cur.fetchall()
            res = {}
            for r in rows:
                if r["iqi_id"] not in res:
                    res[r["iqi_id"]] = r
            return res

    @staticmethod
    def save(iqi_id: int, qc_batch_id: int, tm: float, tsd: float,
             cva: float, tea: float, mode: int, effective_from: date, set_by: int, change_reason: str = None):
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO qc_target_settings "
                "(iqi_id, qc_batch_id, tm, tsd, cva_percent, tea_percent, mode, effective_from, set_by, change_reason) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (iqi_id, qc_batch_id, tm, tsd, cva, tea, mode, effective_from, set_by, change_reason)
            )

    @staticmethod
    def save_semi_target(iqi_id: int, qc_batch_id: int, semi_min: str, semi_max: str,
                         mode: int, effective_from: date, set_by: int, change_reason: str = None):
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO qc_target_settings "
                "(iqi_id, qc_batch_id, semi_target_min, semi_target_max, mode, effective_from, set_by, change_reason) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                (iqi_id, qc_batch_id, semi_min, semi_max, mode, effective_from, set_by, change_reason)
            )


# ── 每日品管結果 ───────────────────────────────────────────────

class QCResultService:

    @staticmethod
    def save_result(iqi_id: int, result_date: date,
                    reagent_batch_id: int | None, qc_batch_id: int | None,
                    measured_value: float | None, qualitative_result: str | None,
                    notes: str, entered_by: int, source: int = 1) -> int:
        """儲存單筆品管結果，自動進行 Westgard 判斷。"""
        is_accepted, westgard_flag = QCResultService._check_westgard(
            iqi_id, result_date, measured_value, qualitative_result, qc_batch_id
        )
        with DBContext() as (_, cur):
            cur.execute(
                "INSERT INTO qc_results "
                "(iqi_id, result_date, reagent_batch_id, qc_batch_id, "
                "measured_value, qualitative_result, is_accepted, westgard_flag, "
                "source, notes, entered_by) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (iqi_id, result_date, reagent_batch_id, qc_batch_id,
                 measured_value, qualitative_result, is_accepted, westgard_flag,
                 source, notes or None, entered_by)
            )
            return cur.lastrowid

    @staticmethod
    def get_results(iqi_id: int, from_date: date, to_date: date) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT r.result_id, r.result_date, r.measured_value, r.qc_batch_id, "
                "r.qualitative_result, r.is_accepted, r.westgard_flag, "
                "r.source, r.notes, r.entered_at, u.name AS entered_by_name, "
                "EXISTS(SELECT 1 FROM qc_anomaly_records a WHERE a.result_id = r.result_id) AS has_anomaly "
                "FROM qc_results r JOIN users u ON r.entered_by = u.user_id "
                "WHERE r.iqi_id=%s AND r.result_date >= %s AND r.result_date <= %s "
                "ORDER BY r.result_date ASC, r.entered_at ASC",
                (iqi_id, f"{from_date} 00:00:00", f"{to_date} 23:59:59")
            )
            return cur.fetchall()

    @staticmethod
    def update_note(result_id: int, notes: str):
        with DBContext() as (_, cur):
            cur.execute(
                "UPDATE qc_results SET notes=%s WHERE result_id=%s",
                (notes, result_id)
            )

    @staticmethod
    def get_total_stats(iqi_id: int, qc_batch_id: int = None) -> dict:
        with DBContext() as (_, cur):
            if qc_batch_id is not None:
                cur.execute(
                    "SELECT measured_value, qualitative_result, is_accepted "
                    "FROM qc_results WHERE iqi_id=%s AND qc_batch_id=%s",
                    (iqi_id, qc_batch_id)
                )
            else:
                cur.execute(
                    "SELECT measured_value, qualitative_result, is_accepted "
                    "FROM qc_results WHERE iqi_id=%s",
                    (iqi_id,)
                )
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
            # None or 1 is considered accepted in legacy data, 0 is rejected
            if r["is_accepted"] is False or r["is_accepted"] == 0:
                stats["reject"] += 1
            else:
                stats["accept"] += 1
            
        return stats

    @staticmethod
    def _check_westgard(iqi_id: int, result_date: date,
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
                
            levels = {"Neg": 0, "Trace": 0.5, "1+": 1, "2+": 2, "3+": 3}
            q_val = levels.get(qualitative)
            min_val = levels.get(s_min)
            max_val = levels.get(s_max)
            
            if q_val is not None and min_val is not None and max_val is not None:
                if min_val <= q_val <= max_val:
                    return True, None
                else:
                    return False, "Out of Range"
            return True, None

        # 數值半定量判定 (param_type=3)
        if value is not None and ts and ts.get("semi_target_min") is not None and ts.get("tm") is None:
            try:
                min_val = float(ts["semi_target_min"])
                max_val = float(ts["semi_target_max"])
                if min_val <= value <= max_val:
                    return True, None
                else:
                    return False, "Out of Range"
            except (ValueError, TypeError):
                return True, None

        if not ts or ts.get("tm") is None or ts.get("tsd") is None:
            return True, None

        tm  = float(ts["tm"])
        tsd = float(ts["tsd"])
        if tsd == 0:
            return True, None

        z = (value - tm) / tsd

        # 1-3S：超出 ±3SD
        if abs(z) > 3:
            return False, "1-3S"

        # 2-2S 和 R-4S 需要前一筆
        prev = QCResultService._get_previous_value(iqi_id, result_date)
        if prev is not None:
            z_prev = (prev - tm) / tsd
            # 2-2S：連續兩點同側超出 ±2SD
            if z > 2 and z_prev > 2:
                return False, "2-2S"
            if z < -2 and z_prev < -2:
                return False, "2-2S"
            # R-4S：相鄰兩點差距 > 4SD
            if abs(z - z_prev) > 4:
                return False, "R-4S"

        return True, None

    @staticmethod
    def _get_previous_value(iqi_id: int, before_date: date) -> float | None:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT measured_value FROM qc_results "
                "WHERE iqi_id=%s AND result_date < %s AND measured_value IS NOT NULL "
                "ORDER BY result_date DESC LIMIT 1",
                (iqi_id, before_date)
            )
            row = cur.fetchone()
        return float(row["measured_value"]) if row and row["measured_value"] is not None else None


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
