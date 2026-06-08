import re

with open("ui/qc/qc_batch.py", "r") as f:
    content = f.read()

# Change button name
content = content.replace('"📋 執行允收 / TM-TSD"', '"📋 執行允收"')

# We will completely replace QCAcceptanceDialog and TargetSettingDialog
start_idx = content.find("class QCAcceptanceDialog(QDialog):")
if start_idx != -1:
    content = content[:start_idx]
else:
    print("Could not find QCAcceptanceDialog")
    exit(1)

new_ui = """class QCAcceptanceDialog(QDialog):
    \"\"\"品管液允收。\"\"\"
    def __init__(self, parent, batch: dict, user: dict):
        super().__init__(parent)
        self.batch = batch
        self.user  = user
        level_name = batch.get("level_name", "")
        self.setWindowTitle(f"品管液允收 — {level_name} 批號 {batch['lot_number']}")
        self.setMinimumSize(850, 700)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        info = QLabel(
            f"品管液：{level_name}  |  批號：{batch['lot_number']}  |  "
            f"效期：{batch['expiry_date'] or '—'}"
        )
        info.setStyleSheet(f"font-size:13px; font-weight:bold; color:{COLORS['text_primary']};")
        layout.addWidget(info)

        # Date range picker
        date_row = QHBoxLayout()
        date_row.addWidget(QLabel("統計區間："))
        
        self.d_start = QDateEdit()
        self.d_start.setCalendarPopup(True)
        # Default start date is batch creation or open date
        d_start_val = batch.get('open_date') or batch.get('created_at').date() if batch.get('created_at') else date.today()
        self.d_start.setDate(QDate(d_start_val.year, d_start_val.month, d_start_val.day))
        
        self.d_end = QDateEdit()
        self.d_end.setCalendarPopup(True)
        self.d_end.setDate(QDate.currentDate())
        
        date_row.addWidget(self.d_start)
        date_row.addWidget(QLabel(" 至 "))
        date_row.addWidget(self.d_end)
        
        btn_refresh = QPushButton("🔄 重新統計")
        btn_refresh.clicked.connect(self._refresh_stats)
        date_row.addWidget(btn_refresh)
        date_row.addStretch()
        
        layout.addLayout(date_row)
        
        # Scroll area for tables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_accept = QPushButton("允收")
        btn_accept.setStyleSheet(f"background-color: {COLORS['primary']}; color: white; border-radius: 4px; padding: 8px 24px; font-weight: bold;")
        btn_accept.clicked.connect(lambda: self._save(1))
        
        btn_cancel = QPushButton("取消")
        btn_cancel.setStyleSheet("background-color: #f5f5f5; color: #595959; border: 1px solid #d9d9d9; border-radius: 4px; padding: 8px 16px;")
        btn_cancel.clicked.connect(self.reject)
        
        btn_reject = QPushButton("拒絕")
        btn_reject.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border-radius: 4px; padding: 8px 24px;")
        btn_reject.clicked.connect(lambda: self._save(2))
        
        btn_row.addStretch()
        btn_row.addWidget(btn_reject)
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_accept)
        layout.addLayout(btn_row)
        
        self._input_widgets = {} # reagent_id -> (tm_input, tsd_input)
        self._refresh_stats()

    def _refresh_stats(self):
        # clear previous UI
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        d1 = self.d_start.date().toPyDate()
        d2 = self.d_end.date().toPyDate()
        
        stats = QCBatchService.get_qc_batch_stats(self.batch["batch_id"], d1, d2)
        
        # Build Qualitative Table
        grp_qual = QGroupBox("定性/半定量項目統計")
        grp_qual.setStyleSheet("font-weight: bold; color: #333;")
        l_qual = QVBoxLayout(grp_qual)
        
        t_qual = QTableWidget(0, 4)
        t_qual.setHorizontalHeaderLabels(["項目", "合格範圍", "合格筆數", "不合格筆數"])
        t_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t_qual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t_qual.setAlternatingRowColors(True)
        t_qual.verticalHeader().setVisible(False)
        
        for rname, data in stats["qual"].items():
            r = t_qual.rowCount()
            t_qual.insertRow(r)
            
            vals = [rname, data["range"], data["passed"], data["failed"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                t_qual.setItem(r, c, it)
                
        l_qual.addWidget(t_qual)
        self.scroll_layout.addWidget(grp_qual)
        
        # Build Quantitative Table
        grp_quant = QGroupBox("定量項目統計與目標設定")
        grp_quant.setStyleSheet("font-weight: bold; color: #333;")
        l_quant = QVBoxLayout(grp_quant)
        
        t_quant = QTableWidget(0, 7)
        t_quant.setHorizontalHeaderLabels(["項目", "TM", "AM", "TSD", "ASD", "設定Mean", "設定SD"])
        t_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t_quant.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        t_quant.setAlternatingRowColors(True)
        t_quant.verticalHeader().setVisible(False)
        
        self._input_widgets = {}
        
        # Map reagent_name back to reagent_id for saving
        from services.qc_service import MasterService
        reagents = MasterService.get_reagents()
        r_map = {r["reagent_name"]: r["reagent_id"] for r in reagents}
        
        for rname, data in stats["quant"].items():
            r = t_quant.rowCount()
            t_quant.insertRow(r)
            
            # AM, ASD formatting
            am = f"{data['am']:.4f}" if data['am'] is not None else "—"
            asd = f"{data['asd']:.4f}" if data['asd'] is not None else "—"
            tm = f"{data['tm']:.4f}" if data['tm'] is not None else "—"
            tsd = f"{data['tsd']:.4f}" if data['tsd'] is not None else "—"
            
            vals = [rname, tm, am, tsd, asd]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                t_quant.setItem(r, c, it)
                
            # Input Mean
            inp_mean = QLineEdit()
            inp_mean.setPlaceholderText("Mean")
            if data['am'] is not None:
                inp_mean.setText(f"{data['am']:.4f}")
            t_quant.setCellWidget(r, 5, inp_mean)
            
            # Input SD
            inp_sd = QLineEdit()
            inp_sd.setPlaceholderText("SD")
            if data['asd'] is not None:
                inp_sd.setText(f"{data['asd']:.4f}")
            t_quant.setCellWidget(r, 6, inp_sd)
            
            self._input_widgets[r_map.get(rname)] = (inp_mean, inp_sd)
            
        l_quant.addWidget(t_quant)
        self.scroll_layout.addWidget(grp_quant)

    def _save(self, status: int):
        status_map = {1: "允收", 2: "拒絕"}
        st = status_map[status]
        
        if not self.confirm("確認決策", f"確定要將批號 {self.batch['lot_number']} 標記為「{st}」嗎？", default_yes=True):
            return
            
        # 1. Update qc_batches acceptance_status
        QCBatchService.save_qc_batch_acceptance(self.batch["batch_id"], status)
        
        # 2. If Accept, save TM/TSD for quantitative items
        saved = 0
        if status == 1:
            today = date.today()
            all_iqi_by_reagent = {}
            from services.qc_service import MasterService, TargetSettingService
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == self.batch["level_name"]:
                        key = iqi["reagent_id"]
                        if key not in all_iqi_by_reagent:
                            all_iqi_by_reagent[key] = []
                        all_iqi_by_reagent[key].append(iqi["iqi_id"])
                        
            for reagent_id, (inp_mean, inp_sd) in self._input_widgets.items():
                if not reagent_id: continue
                m_txt = inp_mean.text().strip()
                s_txt = inp_sd.text().strip()
                if not m_txt or not s_txt: continue
                
                try:
                    m = float(m_txt)
                    s = float(s_txt)
                    
                    # Save to all corresponding iqi_ids
                    iqis = all_iqi_by_reagent.get(reagent_id, [])
                    for iqi_id in iqis:
                        # retain old TEa% if present
                        old_ts = TargetSettingService.get_current(iqi_id)
                        tea = old_ts["tea_percent"] if old_ts and old_ts["tea_percent"] is not None else None
                        
                        TargetSettingService.save(
                            iqi_id, self.batch["batch_id"], m, s, None, tea,
                            mode=2, effective_from=today, set_by=self.user["user_id"]
                        )
                    saved += 1
                except ValueError:
                    pass
        
        msg = f"已成功儲存決策：{st}"
        if saved > 0:
            msg += f"\\n並寫入 {saved} 項定量項目的設定值。"
            
        QMessageBox.information(self, "完成", msg)
        self.accept()
        
    def confirm(self, title, msg, default_yes=False):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes


class TargetSettingDialog(QDialog):
    \"\"\"設定品管範圍\"\"\"
    def __init__(self, parent, batch: dict, user: dict):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.setWindowTitle(f"設定品管範圍 — {batch.get('level_name','')} 批號 {batch['lot_number']}")
        self.setMinimumSize(700, 600)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        top_row = QHBoxLayout()
        info = QLabel(f"設定 {batch.get('level_name','')} ({batch['lot_number']}) 的品管範圍")
        info.setStyleSheet(f"font-size:14px; color:{COLORS['accent']}; font-weight:bold;")
        
        btn_load = QPushButton("📥 帶入現有批號設定")
        btn_load.clicked.connect(self._load_current_settings)
        
        top_row.addWidget(info)
        top_row.addStretch()
        top_row.addWidget(btn_load)
        layout.addLayout(top_row)
        
        # We will build a single grid layout inside a scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        w = QWidget()
        g = QGridLayout(w)
        g.setSpacing(12)
        
        headers = ["項目", "設定1 (下限 / TM)", "設定2 (上限 / TSD)", "計算範圍 (±2SD)", "TEa%"]
        for c, h in enumerate(headers):
            lbl = QLabel(h)
            lbl.setStyleSheet(f"font-weight:700; color:{COLORS['text_primary']};")
            g.addWidget(lbl, 0, c)
            
        self._inputs = {}
        
        from services.qc_service import MasterService, TargetSettingService
        reagents = MasterService.get_reagents()
        
        # Load existing for THIS batch (or current active if none exist)
        self._existing = {}
        for inst in MasterService.get_instruments():
            for iqi in MasterService.get_iqi(inst["instrument_id"]):
                if iqi["level_name"] == self.batch["level_name"]:
                    # Just grab the first instrument's iqi for UI display purposes
                    ts = TargetSettingService.get_current(iqi["iqi_id"])
                    if ts:
                        self._existing[iqi["reagent_id"]] = ts
        
        row = 1
        for r in reagents:
            disp_name = r['reagent_name']
            g.addWidget(QLabel(disp_name), row, 0)
            
            widgets = {}
            if r["param_type"] == 2: # Semi
                c_min = QComboBox()
                c_min.addItems(SEMI_OPTIONS)
                c_max = QComboBox()
                c_max.addItems(SEMI_OPTIONS)
                
                if r["reagent_id"] in self._existing:
                    ts = self._existing[r["reagent_id"]]
                    s_min, s_max = ts.get("semi_target_min"), ts.get("semi_target_max")
                    if s_min in SEMI_OPTIONS: c_min.setCurrentText(s_min)
                    if s_max in SEMI_OPTIONS: c_max.setCurrentText(s_max)
                    
                g.addWidget(c_min, row, 1)
                g.addWidget(c_max, row, 2)
                
                widgets["type"] = "semi"
                widgets["min"] = c_min
                widgets["max"] = c_max
                
            else: # Quant
                inp_tm = QLineEdit()
                inp_tm.setPlaceholderText("TM")
                inp_tsd = QLineEdit()
                inp_tsd.setPlaceholderText("TSD")
                inp_tea = QLineEdit()
                inp_tea.setPlaceholderText("TEa%")
                
                lbl_range = QLabel("—")
                lbl_range.setStyleSheet("color: #666; font-size: 12px;")
                
                def update_range(*args, tm_w=inp_tm, tsd_w=inp_tsd, lbl=lbl_range):
                    try:
                        tm = float(tm_w.text())
                        tsd = float(tsd_w.text())
                        lbl.setText(f"{tm - 2*tsd:.4f} ~ {tm + 2*tsd:.4f}")
                    except ValueError:
                        lbl.setText("—")
                        
                inp_tm.textChanged.connect(update_range)
                inp_tsd.textChanged.connect(update_range)
                
                if r["reagent_id"] in self._existing:
                    ts = self._existing[r["reagent_id"]]
                    if ts.get("tm") is not None: inp_tm.setText(str(ts["tm"]))
                    if ts.get("tsd") is not None: inp_tsd.setText(str(ts["tsd"]))
                    if ts.get("tea_percent") is not None: inp_tea.setText(str(ts["tea_percent"]))
                    
                g.addWidget(inp_tm, row, 1)
                g.addWidget(inp_tsd, row, 2)
                g.addWidget(lbl_range, row, 3)
                g.addWidget(inp_tea, row, 4)
                
                widgets["type"] = "quant"
                widgets["tm"] = inp_tm
                widgets["tsd"] = inp_tsd
                widgets["tea"] = inp_tea
                
            self._inputs[r["reagent_id"]] = widgets
            row += 1
            
        g.setRowStretch(row, 1)
        scroll.setWidget(w)
        layout.addWidget(scroll)
        
        btn_row = QHBoxLayout()
        btn_save = QPushButton("儲存設定")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load_current_settings(self):
        from services.qc_service import MasterService, TargetSettingService
        active_batches = __import__('services.qc_service').qc_service.QCBatchService.get_active_batches()
        active_batch_id = None
        for b in active_batches:
            if b["level_name"] == self.batch["level_name"]:
                active_batch_id = b["batch_id"]
                break
                
        if not active_batch_id:
            QMessageBox.warning(self, "警告", "找不到目前使用中的對應濃度批號。")
            return
            
        # load target settings from that batch
        for inst in MasterService.get_instruments():
            for iqi in MasterService.get_iqi(inst["instrument_id"]):
                if iqi["level_name"] == self.batch["level_name"]:
                    ts = TargetSettingService.get_current(iqi["iqi_id"])
                    if not ts: continue
                    rid = iqi["reagent_id"]
                    if rid in self._inputs:
                        w = self._inputs[rid]
                        if w["type"] == "semi":
                            if ts.get("semi_target_min"): w["min"].setCurrentText(ts["semi_target_min"])
                            if ts.get("semi_target_max"): w["max"].setCurrentText(ts["semi_target_max"])
                        else:
                            if ts.get("tm") is not None: w["tm"].setText(str(ts["tm"]))
                            if ts.get("tsd") is not None: w["tsd"].setText(str(ts["tsd"]))
                            if ts.get("tea_percent") is not None: w["tea"].setText(str(ts["tea_percent"]))
                            
        QMessageBox.information(self, "完成", "已帶入目前使用中批號的設定。")

    def _save(self):
        saved = 0
        today = date.today()
        from services.qc_service import MasterService, TargetSettingService
        all_iqi_by_reagent = {}
        for inst in MasterService.get_instruments():
            for iqi in MasterService.get_iqi(inst["instrument_id"]):
                if iqi["level_name"] == self.batch["level_name"]:
                    key = iqi["reagent_id"]
                    if key not in all_iqi_by_reagent:
                        all_iqi_by_reagent[key] = []
                    all_iqi_by_reagent[key].append(iqi["iqi_id"])
                    
        for reagent_id, w in self._inputs.items():
            iqis = all_iqi_by_reagent.get(reagent_id, [])
            if w["type"] == "semi":
                s_min = w["min"].currentText()
                s_max = w["max"].currentText()
                for iqi_id in iqis:
                    TargetSettingService.save_semi_target(
                        iqi_id, self.batch["batch_id"], s_min, s_max,
                        mode=2, effective_from=today, set_by=self.user["user_id"]
                    )
                saved += 1
            else:
                tm_txt = w["tm"].text().strip()
                tsd_txt = w["tsd"].text().strip()
                tea_txt = w["tea"].text().strip()
                
                if not tm_txt or not tsd_txt:
                    continue
                    
                try:
                    tm = float(tm_txt)
                    tsd = float(tsd_txt)
                    tea = float(tea_txt) if tea_txt else None
                    
                    for iqi_id in iqis:
                        TargetSettingService.save(
                            iqi_id, self.batch["batch_id"], tm, tsd, None, tea,
                            mode=2, effective_from=today, set_by=self.user["user_id"]
                        )
                    saved += 1
                except ValueError:
                    pass
                    
        QMessageBox.information(self, "完成", f"已儲存 {saved} 項範圍設定。")
        self.accept()

class AcceptanceViewDialog(QDialog):
    def __init__(self, parent, batch: dict, records: list):
        super().__init__(parent)
        self.setWindowTitle(f"允收記錄 — {batch.get('level_name','')} {batch['lot_number']}")
        self.setMinimumSize(500, 300)
        self.setStyleSheet(PAGE_STYLE)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("此功能已整併至新版批次允收。"))
"""

with open("ui/qc/qc_batch.py", "w") as f:
    f.write(content + new_ui)
