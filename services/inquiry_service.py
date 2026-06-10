import json
import math
from datetime import date
from database.connection import DBContext

class InquiryService:
    @staticmethod
    def get_reagent_acceptances(from_date: date, to_date: date, lot_number: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT a.acceptance_id, a.reagent_batch_id, a.status, a.snapshot_data, "
                "a.accepted_at, u.name AS accepted_by_name, "
                "b.lot_number, b.expiry_date, b.open_date "
                "FROM reagent_batch_acceptance a "
                "JOIN reagent_batches b ON a.reagent_batch_id = b.batch_id "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE DATE(a.accepted_at) >= %s AND DATE(a.accepted_at) <= %s "
            )
            params = [from_date, to_date]
            
            if lot_number and lot_number != "全部":
                query += "AND b.lot_number = %s "
                params.append(lot_number)
                
            query += "ORDER BY a.accepted_at DESC"
            cur.execute(query, params)
            return cur.fetchall()

    @staticmethod
    def get_qc_acceptances(from_date: date, to_date: date) -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute(
                "SELECT a.accept_id, a.qc_batch_id, a.reagent_id, a.accept_type, "
                "a.semi_result, a.semi_expected, a.semi_pass, "
                "a.calc_mean, a.calc_sd, a.result, "
                "a.accepted_at, a.notes, u.name AS accepted_by_name, "
                "b.lot_number, b.level_id, l.level_name, r.reagent_label, r.reagent_name "
                "FROM qc_batch_acceptance a "
                "JOIN qc_batches b ON a.qc_batch_id = b.batch_id "
                "JOIN qc_levels l ON b.level_id = l.level_id "
                "JOIN reagents r ON a.reagent_id = r.reagent_id "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE DATE(a.accepted_at) >= %s AND DATE(a.accepted_at) <= %s "
                "ORDER BY a.accepted_at DESC",
                (from_date, to_date)
            )
            return cur.fetchall()

    @staticmethod
    def get_qc_target_history(from_date: date, to_date: date, inst_id: int = None, lot_number: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT s.*, "
                "u.name AS set_by_name, "
                "i.instrument_name, "
                "r.reagent_name, r.param_type, "
                "b.lot_number, b.expiry_date, l.level_name "
                "FROM qc_target_settings s "
                "JOIN instrument_qc_items iqi ON s.iqi_id = iqi.iqi_id "
                "JOIN instruments i ON iqi.instrument_id = i.instrument_id "
                "JOIN reagents r ON iqi.reagent_id = r.reagent_id "
                "JOIN qc_batches b ON s.qc_batch_id = b.batch_id "
                "JOIN qc_levels l ON b.level_id = l.level_id "
                "JOIN users u ON s.set_by = u.user_id "
                "WHERE 1=1 "
            )
            params = []
            
            if inst_id:
                query += "AND i.instrument_id = %s "
                params.append(inst_id)
                
            query += "ORDER BY s.iqi_id, s.set_at DESC"
            cur.execute(query, params)
            rows = cur.fetchall()
            
            results = []
            for i, row in enumerate(rows):
                dt = row["set_at"].date() if hasattr(row["set_at"], 'date') else row["set_at"]
                
                prev_row = None
                for j in range(i + 1, len(rows)):
                    if rows[j]["iqi_id"] == row["iqi_id"]:
                        prev_row = rows[j]
                        break
                
                row["prev_tm"] = prev_row["tm"] if prev_row else None
                row["prev_tsd"] = prev_row["tsd"] if prev_row else None
                row["prev_semi_min"] = prev_row["semi_target_min"] if prev_row else None
                row["prev_semi_max"] = prev_row["semi_target_max"] if prev_row else None
                
                # Check filters that must apply to the target setting
                if from_date <= dt <= to_date:
                    if lot_number and lot_number != "全部":
                        if row["lot_number"] != lot_number:
                            continue
                    results.append(row)
                    
            results.sort(key=lambda x: x["set_at"], reverse=True)
            return results

    @staticmethod
    def get_qc_acceptance_summary(from_date: date, to_date: date, lot_number: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT b.batch_id, b.lot_number, l.level_name, "
                "MAX(a.accepted_at) as accepted_at, u.name as accepted_by_name "
                "FROM qc_batch_acceptance a "
                "JOIN qc_batches b ON a.qc_batch_id = b.batch_id "
                "JOIN qc_levels l ON b.level_id = l.level_id "
                "JOIN users u ON a.accepted_by = u.user_id "
                "WHERE DATE(a.accepted_at) >= %s AND DATE(a.accepted_at) <= %s "
            )
            params = [from_date, to_date]
            
            if lot_number and lot_number != "全部":
                query += "AND b.lot_number = %s "
                params.append(lot_number)
                
            query += "GROUP BY b.batch_id, b.lot_number, l.level_name, u.name ORDER BY accepted_at DESC"
            cur.execute(query, params)
            return cur.fetchall()

    @staticmethod
    def get_qc_reports(from_date: date, to_date: date, instrument_id: int, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT r.result_id, r.iqi_id, r.measured_value, r.is_accepted, re.param_type, "
                "re.reagent_name, re.reagent_label, "
                "l.level_name, b.lot_number, r.qc_batch_id "
                "FROM qc_results r "
                "JOIN instrument_qc_items i ON r.iqi_id = i.iqi_id "
                "JOIN reagents re ON i.reagent_id = re.reagent_id "
                "JOIN qc_levels l ON i.level_id = l.level_id "
                "LEFT JOIN qc_batches b ON r.qc_batch_id = b.batch_id "
                "WHERE i.instrument_id = %s "
                "AND r.result_date >= %s AND r.result_date <= %s "
            )
            params = [instrument_id, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND b.lot_number = %s "
                params.append(lot_number)
                
            query += " ORDER BY re.display_order, l.level_name, r.result_date"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            
            cur.execute(
                "SELECT iqi_id, qc_batch_id, tm, tsd, cva_percent, tea_percent "
                "FROM qc_target_settings"
            )
            settings = cur.fetchall()
            
        settings_map = {}
        for s in settings:
            key = (s["iqi_id"], s["qc_batch_id"])
            settings_map[key] = s

        # Group by item (iqi_id -> level_name, reagent_name, lot_number)
        stats_map = {}
        for row in results:
            # key can be iqi_id + lot_number to separate stats if lot changes
            key = (row["iqi_id"], row["qc_batch_id"])
            if key not in stats_map:
                stats_map[key] = {
                    "reagent_name": row["reagent_name"],
                    "reagent_label": row["reagent_label"],
                    "param_type": row["param_type"],
                    "level_name": row["level_name"],
                    "lot_number": row["lot_number"] or "未設定",
                    "n": 0,
                    "values": [],
                    "accepts": 0,
                    "rejects": 0,
                    "target": settings_map.get((row["iqi_id"], row["qc_batch_id"]), {})
                }
            
            stats_map[key]["n"] += 1
            if row["param_type"] == 1 and row["measured_value"] is not None:
                stats_map[key]["values"].append(float(row["measured_value"]))
            
            if row["is_accepted"]:
                stats_map[key]["accepts"] += 1
            else:
                stats_map[key]["rejects"] += 1

        final_stats = []
        for k, v in stats_map.items():
            s = dict(v)
            if s["param_type"] == 1:
                vals = s["values"]
                n = len(vals)
                if n > 0:
                    mean = sum(vals) / n
                    s["mean"] = mean
                    if n > 1:
                        var = sum((x - mean) ** 2 for x in vals) / (n - 1)
                        sd = math.sqrt(var)
                        s["sd"] = sd
                        s["cv"] = (sd / mean * 100) if mean != 0 else 0
                    else:
                        s["sd"] = 0
                        s["cv"] = 0
                else:
                    s["mean"] = s["sd"] = s["cv"] = 0
                    
                target = s["target"]
                tm = float(target.get("tm")) if target and target.get("tm") is not None else None
                tsd = float(target.get("tsd")) if target and target.get("tsd") is not None else None
                tea = float(target.get("tea_percent")) if target and target.get("tea_percent") is not None else None
                
                s["tm"] = tm
                s["tsd"] = tsd
                s["tea_percent"] = tea
                
                if tm is not None and tm != 0 and s["mean"] != 0:
                    bias_pct = (abs(s["mean"] - tm) / tm) * 100
                    s["bias_pct"] = bias_pct
                    s["te"] = bias_pct + (2 * s["cv"])
                else:
                    s["bias_pct"] = None
                    s["te"] = None
            else:
                s["mean"] = s["sd"] = s["cv"] = s["te"] = s["tm"] = s["tsd"] = s["tea_percent"] = s["bias_pct"] = None
            
            final_stats.append(s)
            
        # Sort by reagent_name, then level_name
        return sorted(final_stats, key=lambda x: (x["reagent_name"], x["level_name"], x["lot_number"]))

    @staticmethod
    def get_measurement_uncertainty(from_date: date, to_date: date, instrument_id: int, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            # Only fetch quantitative params (param_type = 1)
            query = (
                "SELECT r.result_id, r.iqi_id, r.measured_value, r.result_date, "
                "re.reagent_name, re.reagent_label, "
                "l.level_name, b.lot_number, r.qc_batch_id "
                "FROM qc_results r "
                "JOIN instrument_qc_items i ON r.iqi_id = i.iqi_id "
                "JOIN reagents re ON i.reagent_id = re.reagent_id "
                "JOIN qc_levels l ON i.level_id = l.level_id "
                "LEFT JOIN qc_batches b ON r.qc_batch_id = b.batch_id "
                "WHERE i.instrument_id = %s AND re.param_type = 1 "
                "AND r.result_date >= %s AND r.result_date <= %s "
                "AND r.measured_value IS NOT NULL "
            )
            params = [instrument_id, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND b.lot_number = %s "
                params.append(lot_number)
                
            query += " ORDER BY re.display_order, l.level_name, r.result_date"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            
            # Fetch target settings for Bias calculation
            cur.execute(
                "SELECT iqi_id, qc_batch_id, tm, tsd, cva_percent, tea_percent "
                "FROM qc_target_settings"
            )
            settings = cur.fetchall()

        # Build setting lookup: (iqi_id, qc_batch_id) -> setting
        settings_map = {}
        for s in settings:
            key = (s["iqi_id"], s["qc_batch_id"])
            # Assuming we take the latest setting for that batch
            settings_map[key] = s

        stats_map = {}
        for row in results:
            key = (row["iqi_id"], row["qc_batch_id"])
            if key not in stats_map:
                stats_map[key] = {
                    "reagent_name": row["reagent_name"],
                    "reagent_label": row["reagent_label"],
                    "level_name": row["level_name"],
                    "lot_number": row["lot_number"] or "未設定",
                    "n": 0,
                    "values": [],
                    "target": settings_map.get(key, {})
                }
            stats_map[key]["values"].append(float(row["measured_value"]))
            stats_map[key]["n"] += 1
            
        final_stats = []
        for k, v in stats_map.items():
            s = dict(v)
            vals = s["values"]
            n = len(vals)
            target = s["target"]
            tm = float(target.get("tm")) if target and target.get("tm") is not None else None
            tea = float(target.get("tea_percent")) if target and target.get("tea_percent") is not None else None
            
            if n > 0:
                mean = sum(vals) / n
                s["mean"] = mean
                if n > 1:
                    var = sum((x - mean) ** 2 for x in vals) / (n - 1)
                    sd = math.sqrt(var)
                    s["sd"] = sd
                    cv = (sd / mean * 100) if mean != 0 else 0
                    s["cv"] = cv
                else:
                    s["sd"] = 0
                    cv = s["cv"] = 0
            else:
                s["mean"] = s["sd"] = s["cv"] = 0
                cv = 0
                mean = 0
                
            if tm is not None and tm != 0:
                bias_abs = abs(mean - tm)
                bias_pct = (bias_abs / tm) * 100
            else:
                bias_abs = None
                bias_pct = None
                
            s["tm"] = tm
            s["tea"] = tea
            s["bias_abs"] = bias_abs
            s["bias_pct"] = bias_pct
            
            # Expanded uncertainty U = 2 * sqrt(CV^2 + Bias%^2) -> this is a common clinical lab formula
            if bias_pct is not None:
                uc = math.sqrt((cv ** 2) + (bias_pct ** 2))
                s["u_expanded"] = 2 * uc
            else:
                s["u_expanded"] = None
                
            final_stats.append(s)

        return sorted(final_stats, key=lambda x: (x["reagent_name"], x["level_name"], x["lot_number"]))

    @staticmethod
    def get_qc_raw_data(from_date: date, to_date: date, instrument_id: int, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT r.result_id, r.result_date, r.measured_value, r.qualitative_result, "
                "r.is_accepted, r.westgard_flag, re.reagent_name, re.reagent_label, re.param_type, "
                "l.level_name, b.lot_number, r.qc_batch_id "
                "FROM qc_results r "
                "JOIN instrument_qc_items i ON r.iqi_id = i.iqi_id "
                "JOIN reagents re ON i.reagent_id = re.reagent_id "
                "JOIN qc_levels l ON i.level_id = l.level_id "
                "LEFT JOIN qc_batches b ON r.qc_batch_id = b.batch_id "
                "WHERE i.instrument_id = %s "
                "AND r.result_date >= %s AND r.result_date <= %s "
            )
            params = [instrument_id, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND b.lot_number = %s "
                params.append(lot_number)
                
            query += " ORDER BY r.result_date, l.level_name, re.display_order"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            return results
