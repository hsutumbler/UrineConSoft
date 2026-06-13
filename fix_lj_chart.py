import re

with open("ui/qc/lj_chart.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: _load_chart_for_item
old_load_chart = """        # 取得目前的 active_batch 資訊
        active_batches = {}
        for b in QCBatchService.get_all():
            if b["is_active"] and b["level_name"] not in active_batches:
                active_batches[b["level_name"]] = b
                
        # 取得所有批號以便過濾
        all_batches = QCBatchService.get_all()
        batch_id_to_lot = {b["batch_id"]: b["lot_number"] for b in all_batches}
        selected_lots = self.cmb_batch.currentData()"""

new_load_chart = """        # 取得目前的 active_batch 資訊
        active_batches = {}
        for b in QCBatchService.get_all():
            if b.get("is_active"):
                for sub in b.get("sub_lots", []):
                    if sub["level_name"] not in active_batches:
                        combined = dict(b)
                        combined.update(sub)
                        active_batches[sub["level_name"]] = combined
                
        # 取得所有批號以便過濾
        all_batches = QCBatchService.get_all()
        batch_id_to_lot = {}
        all_flattened_batches = []
        for b in all_batches:
            for sub in b.get("sub_lots", []):
                batch_id_to_lot[sub["batch_id"]] = b["lot_number"]
                combined = dict(b)
                combined.update(sub)
                all_flattened_batches.append(combined)
                
        selected_lots = self.cmb_batch.currentData()"""

content = content.replace(old_load_chart, new_load_chart)

# Fix 2: display_batch
old_display_batch = """            if selected_lots:
                display_batch = next((b for b in all_batches if b["level_name"] == level_name and b["lot_number"] in selected_lots), None)"""

new_display_batch = """            if selected_lots:
                display_batch = next((b for b in all_flattened_batches if b["level_name"] == level_name and b["lot_number"] in selected_lots), None)"""

content = content.replace(old_display_batch, new_display_batch)

# Fix 3: _load_batches
old_load_batches = """    def _load_batches(self):
        self.cmb_batch.blockSignals(True)
        self.cmb_batch.clear()
        
        from services.qc_service import QCBatchService
        batches = QCBatchService.get_all()
        
        active_batches = [b for b in batches if b.get("is_active")]
        pending_batches = [b for b in batches if not b.get("is_active") and not b.get("is_archived")]
        archived_batches = [b for b in batches if b.get("is_archived")]
        
        def format_label(group_batches, suffix):
            active_groups = {}
            for b in group_batches:
                lot = b["lot_number"]
                lvl = b["level_name"]
                if lot not in active_groups:
                    active_groups[lot] = []
                active_groups[lot].append(lvl.replace("Level ", "L"))
            parts = []
            for lot, lvls in active_groups.items():
                parts.append(f"{lot} ({'/'.join(sorted(lvls))})")
            return "  |  ".join(parts) + f" [{suffix}]", sorted(list(set(b["lot_number"] for b in group_batches)))"""

new_load_batches = """    def _load_batches(self):
        self.cmb_batch.blockSignals(True)
        self.cmb_batch.clear()
        
        from services.qc_service import QCBatchService
        batches = QCBatchService.get_all()
        
        active_batches = [b for b in batches if b.get("is_active")]
        pending_batches = [b for b in batches if not b.get("is_active") and not b.get("is_archived")]
        archived_batches = [b for b in batches if b.get("is_archived")]
        
        def format_label(group_batches, suffix):
            active_groups = {}
            for b in group_batches:
                lot = b["lot_number"]
                if lot not in active_groups:
                    active_groups[lot] = []
                for sub in b.get("sub_lots", []):
                    active_groups[lot].append(sub["level_name"].replace("Level ", "L"))
            parts = []
            for lot, lvls in active_groups.items():
                parts.append(f"{lot} ({'/'.join(sorted(list(set(lvls))))})")
            return "  |  ".join(parts) + f" [{suffix}]", sorted(list(set(b["lot_number"] for b in group_batches)))"""

content = content.replace(old_load_batches, new_load_batches)

with open("ui/qc/lj_chart.py", "w", encoding="utf-8") as f:
    f.write(content)

print("lj_chart.py updated!")
