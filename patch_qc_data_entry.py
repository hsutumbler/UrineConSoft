with open("ui/qc/qc_data_entry.py", "r") as f:
    content = f.read()

# Add combo box to top layout
old_top = """        top.addWidget(QLabel("品管日期："))
        self.qc_date = QDateTimeEdit()
        self.qc_date.setCalendarPopup(True)
        self.qc_date.setDateTime(QDateTime.currentDateTime())
        self.qc_date.setDisplayFormat("yyyy/MM/dd HH:mm")
        top.addWidget(self.qc_date)
        top.addStretch()
        layout.addLayout(top)

        # 顯示目前批號
        self.lbl_batches = QLabel("試劑批號：—  |  品管液 L1：—  |  品管液 L2：—")
        self.lbl_batches.setStyleSheet(f"font-size:12px; color:{COLORS['text_secondary']};")
        layout.addWidget(self.lbl_batches)"""

new_top = """        top.addWidget(QLabel("品管日期："))
        self.qc_date = QDateTimeEdit()
        self.qc_date.setCalendarPopup(True)
        self.qc_date.setDateTime(QDateTime.currentDateTime())
        self.qc_date.setDisplayFormat("yyyy/MM/dd HH:mm")
        top.addWidget(self.qc_date)
        top.addSpacing(20)
        
        top.addWidget(QLabel("品管液："))
        self.cmb_qc_batch = QComboBox()
        self.cmb_qc_batch.currentIndexChanged.connect(self._reload_manual_form)
        top.addWidget(self.cmb_qc_batch)
        
        top.addStretch()
        layout.addLayout(top)

        # 顯示目前試劑批號
        self.lbl_batches = QLabel("試劑批號：—")
        self.lbl_batches.setStyleSheet(f"font-size:12px; color:{COLORS['text_secondary']};")
        layout.addWidget(self.lbl_batches)
        
        self._load_qc_batches()"""

content = content.replace(old_top, new_top)

# Add _load_qc_batches method and fix _reload_manual_form
old_reload = """    def _reload_manual_form(self):
        # 清除舊的
        for i in reversed(range(self.form_layout.count())):
            w = self.form_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._manual_widgets.clear()

        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            return

        # 更新批號顯示
        rb = ReagentBatchService.get_active()
        rb_lot = rb["lot_number"] if rb else "未設定"
        active_qc = QCBatchService.get_active_batches()
        l1_lot = l2_lot = "未設定"
        for b in active_qc:
            if b["level_name"] == "Level 1":
                l1_lot = b["lot_number"]
            elif b["level_name"] == "Level 2":
                l2_lot = b["lot_number"]
        self.lbl_batches.setText(
            f"試劑批號：{rb_lot}  |  品管液 L1：{l1_lot}  |  品管液 L2：{l2_lot}"
        )"""

new_reload = """    def _load_qc_batches(self):
        self.cmb_qc_batch.blockSignals(True)
        self.cmb_qc_batch.clear()
        
        batches = QCBatchService.get_all()
        groups = {}
        for b in batches:
            # Group by open_date, expiry_date, created_at date to keep L1/L2 together
            key = (b["open_date"], b["expiry_date"], b["created_at"].date() if b["created_at"] else None)
            if key not in groups:
                groups[key] = []
            groups[key].append(b)
            
        for key, group_batches in groups.items():
            lots = sorted(list(set(b["lot_number"] for b in group_batches)))
            label = f"{'/'.join(lots)}"
            # Find if this group contains the active batches
            is_active = any(b.get("is_active") for b in group_batches)
            if is_active:
                label += " (目前使用中)"
            else:
                label += " (待允收/測試)"
            self.cmb_qc_batch.addItem(label, group_batches)
            
        self.cmb_qc_batch.blockSignals(False)

    def _reload_manual_form(self):
        # 清除舊的
        for i in reversed(range(self.form_layout.count())):
            w = self.form_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        self._manual_widgets.clear()

        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            return

        # 更新批號顯示
        rb = ReagentBatchService.get_active()
        rb_lot = rb["lot_number"] if rb else "未設定"
        self.lbl_batches.setText(f"試劑批號：{rb_lot}")"""

content = content.replace(old_reload, new_reload)

# Fix _save_manual to use the selected batch
old_save = """    def _save_manual(self):
        if not self._manual_widgets:
            return

        rb = ReagentBatchService.get_active()
        active_qc = QCBatchService.get_active_batches()
        l1_batch = l2_batch = None
        for b in active_qc:
            if b["level_name"] == "Level 1": l1_batch = b["batch_id"]
            if b["level_name"] == "Level 2": l2_batch = b["batch_id"]"""

new_save = """    def _save_manual(self):
        if not self._manual_widgets:
            return

        rb = ReagentBatchService.get_active()
        selected_qc_group = self.cmb_qc_batch.currentData()
        l1_batch = l2_batch = None
        
        if selected_qc_group:
            for b in selected_qc_group:
                if b["level_name"] == "Level 1": l1_batch = b["batch_id"]
                if b["level_name"] == "Level 2": l2_batch = b["batch_id"]"""

content = content.replace(old_save, new_save)

with open("ui/qc/qc_data_entry.py", "w") as f:
    f.write(content)
