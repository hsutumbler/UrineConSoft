with open("ui/qc/qc_data_entry.py", "r") as f:
    content = f.read()

old_lbl = """        # 顯示目前試劑批號
        self.lbl_batches = QLabel("試劑批號：—")
        self.lbl_batches.setStyleSheet(f"font-size:12px; color:{COLORS['text_secondary']};")
        layout.addWidget(self.lbl_batches)"""

content = content.replace(old_lbl, "")

old_reload = """        # 更新批號顯示
        rb = ReagentBatchService.get_active()
        rb_lot = rb["lot_number"] if rb else "未設定"
        self.lbl_batches.setText(f"試劑批號：{rb_lot}")"""

content = content.replace(old_reload, "")

with open("ui/qc/qc_data_entry.py", "w") as f:
    f.write(content)
