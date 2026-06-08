with open("ui/qc/qc_data_entry.py", "r") as f:
    content = f.read()

# Fix in qc_data_entry.py
old_label = """            is_active = any(b.get("is_active") for b in group_batches)
            if is_active:
                label += " (目前使用中)"
            else:
                label += " (待允收/測試)"
            self.cmb_qc_batch.addItem(label, group_batches)"""

new_label = """            is_active = any(b.get("is_active") for b in group_batches)
            if is_active:
                label += " [使用中]"
            else:
                label += " [待允收]"
            self.cmb_qc_batch.addItem(label, group_batches)
            
        self.cmb_qc_batch.setMinimumWidth(220)
        if self.cmb_qc_batch.view():
            self.cmb_qc_batch.view().setMinimumWidth(280)"""

content = content.replace(old_label, new_label)

with open("ui/qc/qc_data_entry.py", "w") as f:
    f.write(content)

# Fix in lj_chart.py
with open("ui/qc/lj_chart.py", "r") as f:
    content2 = f.read()

old_label2 = """            lots = sorted(list(set(b["lot_number"] for b in group_batches)))
            label = f"組合 ({'/'.join(lots)})"
            self.cmb_batch.addItem(label, lots)"""

new_label2 = """            lots = sorted(list(set(b["lot_number"] for b in group_batches)))
            is_active = any(b.get("is_active") for b in group_batches)
            label = f"{'/'.join(lots)}"
            label += " [使用中]" if is_active else " [待允收]"
            self.cmb_batch.addItem(label, lots)
            
        self.cmb_batch.setMinimumWidth(220)
        if self.cmb_batch.view():
            self.cmb_batch.view().setMinimumWidth(280)"""

content2 = content2.replace(old_label2, new_label2)

with open("ui/qc/lj_chart.py", "w") as f:
    f.write(content2)
