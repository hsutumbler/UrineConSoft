with open("services/qc_service.py", "r") as f:
    sql = f.read()

new_methods = """
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
                "SELECT res.iqi_id, r.reagent_name, r.reagent_label, res.qualitative_result, "
                "ts.semi_target_min, ts.semi_target_max "
                "FROM qc_results res "
                "JOIN instrument_qc_items iqi ON res.iqi_id = iqi.iqi_id "
                "JOIN reagents r ON iqi.reagent_id = r.reagent_id "
                "LEFT JOIN qc_target_settings ts ON ts.setting_id = ("
                "  SELECT setting_id FROM qc_target_settings ts2 "
                "  WHERE ts2.iqi_id = res.iqi_id AND ts2.effective_from <= res.result_date "
                "  ORDER BY effective_from DESC, set_at DESC LIMIT 1"
                ") "
                "WHERE res.qc_batch_id=%s AND r.param_type=2 "
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
                "  WHERE ts2.iqi_id = res.iqi_id AND ts2.effective_from <= res.result_date "
                "  ORDER BY effective_from DESC, set_at DESC LIMIT 1"
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
                    "asd": asd
                }
                
        return stats
"""

# Insert into QCBatchService class
pos = sql.find("class QCBatchService:")
if pos != -1:
    pos2 = sql.find("@staticmethod", pos)
    sql = sql[:pos2] + new_methods + "\n" + sql[pos2:]

with open("services/qc_service.py", "w") as f:
    f.write(sql)
