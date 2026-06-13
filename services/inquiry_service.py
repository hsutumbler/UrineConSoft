import json
import math
from datetime import date
from database.connection import DBContext

class InquiryService:
    @staticmethod
    def get_reagent_acceptances(from_date: date, to_date: date, lot_number: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT h.history_id, h.batch_id AS reagent_batch_id, h.snapshot_data, h.accepted_at, "
                "u.name AS accepted_by_name, "
                "b.lot_number, b.expiry_date, b.open_date "
                "FROM reagent_batch_history h "
                "JOIN reagent_batches b ON h.batch_id = b.batch_id "
                "LEFT JOIN users u ON h.accepted_by = u.user_id "
                "WHERE DATE(h.accepted_at) >= %s AND DATE(h.accepted_at) <= %s "
            )
            params = [from_date, to_date]
            
            if lot_number and lot_number != "全部":
                query += " AND b.lot_number = %s "
                params.append(lot_number)
                
            query += " ORDER BY h.accepted_at DESC"
            
            cur.execute(query, tuple(params))
            return cur.fetchall()

    @staticmethod
    def get_qc_acceptances(from_date: date, to_date: date) -> list[dict]:
        return []

    @staticmethod
    def get_qc_target_history(from_date: date, to_date: date, inst_id: str = None, lot_number: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = (
                "SELECT t.ltId AS setting_id, t.tMean AS tm, t.tSd AS tsd, "
                "t.`Range` AS semi_target_min, t.`Range` AS semi_target_max, "
                "t.iDateTime AS set_at, t.iUser AS set_by_name, "
                "COALESCE(m.mhName, '全部儀器') AS instrument_name, "
                "r.mhitem AS reagent_name, CASE WHEN r.mhitem='pH' THEN 3 WHEN r.itemtype='Q' THEN 1 ELSE 2 END AS param_type, "
                "b.lot AS lot_number, b.lot_Level AS level_name, CONCAT(t.mtId, '_', b.lot_Level) AS iqi_id "
                "FROM LotTest t "
                "LEFT JOIN MhMaster m ON t.mhId = m.mhId "
                "JOIN MhItem r ON t.mtId = r.mtId "
                "JOIN LotTable b ON t.lot = b.lot_id "
                "WHERE 1=1 "
            )
            params = []
            
            if inst_id:
                query += "AND (t.mhId = %s OR t.mhId IS NULL OR t.mhId = '') "
                params.append(inst_id)
                
            query += "ORDER BY t.mtId, t.iDateTime DESC"
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
        from services.qc_service import QCBatchService
        batches = QCBatchService.get_all()
        results = []
        for b in batches:
            if b["acceptance_status"] not in ("1", "2"):
                continue
                
            dt = b["created_at"].date() if b["created_at"] else b["open_date"].date() if b["open_date"] else None
            if not dt: continue
            
            if from_date <= dt <= to_date:
                if lot_number and lot_number != "全部" and b["lot_number"] != lot_number:
                    continue
                    
                b["accepted_at"] = b["created_at"] or b["open_date"]
                b["accepted_by_name"] = b["created_by_name"]
                results.append(b)
                
        return results

    @staticmethod
    def get_qc_report_batches(from_date: date, to_date: date, instrument_id: str = None) -> list[dict]:
        with DBContext() as (_, cur):
            query = """
                SELECT d.mhId as instrument_id_or_code, 
                       IFNULL(b.lot, d.lot) as lot_number, 
                       GROUP_CONCAT(DISTINCT b.lot_Level ORDER BY b.lot_Level SEPARATOR '/') as level_name, 
                       MAX(b.expiry_date) as expiry_date
                FROM DailyQC d
                LEFT JOIN LotTable b ON d.lot = b.lot_id
                WHERE d.iDate >= %s AND d.iDate <= %s
            """
            params = [f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if instrument_id:
                cur.execute("SELECT mhcode FROM MhMaster WHERE mhId=%s", (instrument_id,))
                row = cur.fetchone()
                if row:
                    query += " AND d.mhId IN (%s, %s)"
                    params.extend([instrument_id, row["mhcode"]])
                else:
                    query += " AND d.mhId = %s"
                    params.append(instrument_id)
            
            query += " GROUP BY d.mhId, IFNULL(b.lot, d.lot)"
            
            cur.execute(query, params)
            rows = cur.fetchall()

            cur.execute("SELECT mhId, mhcode, mhName FROM MhMaster WHERE mhName NOT IN ('77Urine', '77Urine-ec')")
            masters = cur.fetchall()
            id_to_master = {str(m["mhId"]): m for m in masters}
            code_to_master = {str(m["mhcode"]): m for m in masters if m["mhcode"]}

            results = []
            seen = set()
            for r in rows:
                inst_val = str(r["instrument_id_or_code"])
                lot = r["lot_number"]
                if not lot: continue

                m = id_to_master.get(inst_val) or code_to_master.get(inst_val)
                if not m: continue
                
                key = (m["mhId"], lot)
                if key not in seen:
                    seen.add(key)
                    results.append({
                        "instrument_id": m["mhId"],
                        "instrument_name": m["mhName"],
                        "lot_number": lot,
                        "level_name": r["level_name"] or "",
                        "expiry_date": r["expiry_date"]
                    })

            return sorted(results, key=lambda x: (x["instrument_name"], x["lot_number"]))

    @staticmethod
    def get_qc_reports(from_date: date, to_date: date, instrument_id: str, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute("SELECT mhcode FROM MhMaster WHERE mhId=%s", (instrument_id,))
            row = cur.fetchone()
            if not row: return []
            mhcode = row["mhcode"]
            
            query = (
                "SELECT d.dqcId AS result_id, d.mtId AS reagent_id, d.iValue AS measured_value, "
                "CASE WHEN d.sdFlag=0 THEN 1 ELSE 0 END AS is_accepted, "
                "CASE WHEN re.mhitem='pH' THEN 3 WHEN re.itemtype='Q' THEN 1 ELSE 2 END AS param_type, "
                "re.mhitem AS reagent_name, re.mhitem AS reagent_label, "
                "b.lot_Level AS level_name, d.lot AS lot_number "
                "FROM DailyQC d "
                "JOIN MhItem re ON d.mtId = re.mtId "
                "LEFT JOIN LotTable b ON d.lot = b.lot_id "
                "WHERE d.mhId IN (%s, %s) "
                "AND d.iDate >= %s AND d.iDate <= %s "
            )
            params = [instrument_id, mhcode, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND IFNULL(b.lot, d.lot) = %s "
                params.append(lot_number)
                
            query += " ORDER BY CAST(re.mtId AS UNSIGNED), b.lot_Level, d.iDate"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            
            cur.execute(
                "SELECT mtId, lot, tMean AS tm, tSd AS tsd, CVA AS cva_percent, TEA AS tea_percent "
                "FROM LotTest ORDER BY iDateTime ASC, ltId ASC"
            )
            settings = cur.fetchall()
            
        settings_map = {}
        for s in settings:
            key = (s["mtId"], s["lot"])
            settings_map[key] = s

        # Group by item
        stats_map = {}
        for row in results:
            key = (row["reagent_id"], row["lot_number"])
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
                    "target": settings_map.get((row["reagent_id"], row["lot_number"]), {})
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
                try:
                    tea = float(target.get("tea_percent")) if target and target.get("tea_percent") is not None else None
                except:
                    tea = None
                
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
            
        return sorted(final_stats, key=lambda x: (x["reagent_name"], str(x["level_name"]), str(x["lot_number"])))

    @staticmethod
    def get_measurement_uncertainty(from_date: date, to_date: date, instrument_id: str, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute("SELECT mhcode FROM MhMaster WHERE mhId=%s", (instrument_id,))
            row = cur.fetchone()
            if not row: return []
            mhcode = row["mhcode"]
            
            query = (
                "SELECT d.dqcId AS result_id, d.mtId AS reagent_id, d.iValue AS measured_value, "
                "re.mhitem AS reagent_name, re.mhitem AS reagent_label, "
                "b.lot_Level AS level_name, d.lot AS lot_number "
                "FROM DailyQC d "
                "JOIN MhItem re ON d.mtId = re.mtId "
                "LEFT JOIN LotTable b ON d.lot = b.lot_id "
                "WHERE d.mhId IN (%s, %s) AND re.itemtype = 'Q' "
                "AND d.iDate >= %s AND d.iDate <= %s "
                "AND d.iValue IS NOT NULL "
            )
            params = [instrument_id, mhcode, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND IFNULL(b.lot, d.lot) = %s "
                params.append(lot_number)
                
            query += " ORDER BY CAST(re.mtId AS UNSIGNED), b.lot_Level, d.iDate"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            
            cur.execute(
                "SELECT mtId, lot, tMean AS tm, tSd AS tsd, CVA AS cva_percent, TEA AS tea_percent "
                "FROM LotTest ORDER BY iDateTime ASC, ltId ASC"
            )
            settings = cur.fetchall()

        settings_map = {}
        for s in settings:
            key = (s["mtId"], s["lot"])
            settings_map[key] = s

        stats_map = {}
        for row in results:
            key = (row["reagent_id"], row["lot_number"])
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
            try:
                tea = float(target.get("tea_percent")) if target and target.get("tea_percent") is not None else None
            except:
                tea = None
            
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
            
            if bias_pct is not None:
                uc = math.sqrt((cv ** 2) + (bias_pct ** 2))
                s["u_expanded"] = 2 * uc
            else:
                s["u_expanded"] = None
                
            final_stats.append(s)

        return sorted(final_stats, key=lambda x: (x["reagent_name"], str(x["level_name"]), str(x["lot_number"])))

    @staticmethod
    def get_qc_raw_data(from_date: date, to_date: date, instrument_id: str, lot_number: str = "全部") -> list[dict]:
        with DBContext() as (_, cur):
            cur.execute("SELECT mhcode FROM MhMaster WHERE mhId=%s", (instrument_id,))
            row = cur.fetchone()
            if not row: return []
            mhcode = row["mhcode"]
            
            query = (
                "SELECT d.dqcId AS result_id, d.iDate AS result_date, d.iValue AS measured_value, d.Check_Type AS qualitative_result, "
                "CASE WHEN d.sdFlag=0 THEN 1 ELSE 0 END AS is_accepted, '' AS westgard_flag, re.mhitem AS reagent_name, re.mhitem AS reagent_label, "
                "CASE WHEN re.mhitem='pH' THEN 3 WHEN re.itemtype='Q' THEN 1 ELSE 2 END AS param_type, "
                "b.lot_Level AS level_name, d.lot AS lot_number, d.lot AS qc_batch_id "
                "FROM DailyQC d "
                "JOIN MhItem re ON d.mtId = re.mtId "
                "LEFT JOIN LotTable b ON d.lot = b.lot_id "
                "WHERE d.mhId IN (%s, %s) "
                "AND d.iDate >= %s AND d.iDate <= %s "
            )
            params = [instrument_id, mhcode, f"{from_date} 00:00:00", f"{to_date} 23:59:59"]
            
            if lot_number and lot_number != "全部":
                query += " AND b.lot = %s "
                params.append(lot_number)
                
            query += " ORDER BY d.iDate, b.lot_Level, CAST(re.mtId AS UNSIGNED)"
            
            cur.execute(query, tuple(params))
            results = cur.fetchall()
            return results
