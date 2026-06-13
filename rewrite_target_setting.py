import re

with open("ui/qc/qc_batch.py", "r", encoding="utf-8") as f:
    content = f.read()

# Define the start and end of TargetSettingDialog
start_idx = content.find("class TargetSettingDialog(QDialog):")
end_idx = content.find("class QCHistoryDialog(QDialog):")

if start_idx == -1 or end_idx == -1:
    print("Could not find boundaries")
    exit(1)

new_class = """class TargetSettingDialog(QDialog):
    \"\"\"設定品管範圍 (母子批號雙濃度)\"\"\"
    def __init__(self, parent, batch: dict, user: dict):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.setWindowTitle(f"設定品管範圍 — 商品套組 {batch['lot_number']}")
        self.setMinimumSize(750, 650)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        top_row = QHBoxLayout()
        info = QLabel(f"設定商品套組 {batch['lot_number']} 的品管範圍")
        info.setStyleSheet("font-size:14px; color:#A48753; font-weight:bold;")
        top_row.addWidget(info)
        layout.addLayout(top_row)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E0E0E0; background: #FFF; border-radius: 4px; }")
        layout.addWidget(self.tabs)

        self._inputs = {}
        
        from services.qc_service import MasterService, TargetSettingService
        reagents = MasterService.get_reagents()
        
        # Build a tab for each sub_lot
        for sub in batch.get("sub_lots", []):
            level_id = sub["level_id"]
            lvl_name = sub["level_name"]
            sub_batch_id = sub["batch_id"]
            
            self._inputs[level_id] = {}
            
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            w = QWidget()
            g = QGridLayout(w)
            g.setSpacing(12)
            
            headers = ["項目", "設定1 (下限 / TM)", "設定2 (上限 / TSD)", "計算範圍 (±2SD)", "TEa%"]
            for c, h in enumerate(headers):
                lbl = QLabel(h)
                lbl.setStyleSheet("font-weight:700; color:#333;")
                g.addWidget(lbl, 0, c)
                
            # Load existing for THIS sub_batch
            existing = {}
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == lvl_name:
                        ts = TargetSettingService.get_for_batch(iqi["iqi_id"], sub_batch_id)
                        if ts:
                            existing[iqi["reagent_id"]] = ts
                            
            row = 1
            for r in reagents:
                disp_name = r['reagent_name']
                g.addWidget(QLabel(disp_name), row, 0)
                
                widgets = {}
                if r["param_type"] in (2, 3): # Semi
                    c_min = QComboBox()
                    c_max = QComboBox()
                    if r["param_type"] == 2:
                        from ui.base_page import SEMI_OPTIONS
                        c_min.addItems(SEMI_OPTIONS)
                        c_max.addItems(SEMI_OPTIONS)
                    else:
                        opts = [str(x/2) for x in range(9, 18)]
                        c_min.addItems(opts)
                        c_max.addItems(opts)
                    
                    if r["reagent_id"] in existing:
                        ts = existing[r["reagent_id"]]
                        s_min, s_max = ts.get("semi_target_min"), ts.get("semi_target_max")
                        if s_min: c_min.setCurrentText(s_min)
                        if s_max: c_max.setCurrentText(s_max)
                        
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
                    
                    dec = 3 if r["reagent_name"] == "SG" else (1 if r["reagent_name"] in ("RBC", "WBC") else 2)
                    
                    # We need a closure for the signal
                    def make_update_range(tm_w, tsd_w, lbl, d):
                        def update_range():
                            try:
                                tm = float(tm_w.text())
                                tsd = float(tsd_w.text())
                                lbl.setText(f"{tm - 2*tsd:.{d}f} ~ {tm + 2*tsd:.{d}f}")
                            except ValueError:
                                lbl.setText("—")
                        return update_range
                        
                    updater = make_update_range(inp_tm, inp_tsd, lbl_range, dec)
                    inp_tm.textChanged.connect(updater)
                    inp_tsd.textChanged.connect(updater)
                    
                    if r["reagent_id"] in existing:
                        ts = existing[r["reagent_id"]]
                        if ts.get("tm") is not None: inp_tm.setText(str(ts["tm"]))
                        if ts.get("tsd") is not None: inp_tsd.setText(str(ts["tsd"]))
                        if ts.get("tea_percent") is not None: inp_tea.setText(str(ts["tea_percent"]))
                        updater()
                        
                    g.addWidget(inp_tm, row, 1)
                    g.addWidget(inp_tsd, row, 2)
                    g.addWidget(lbl_range, row, 3)
                    g.addWidget(inp_tea, row, 4)
                    
                    widgets["type"] = "quant"
                    widgets["tm"] = inp_tm
                    widgets["tsd"] = inp_tsd
                    widgets["tea"] = inp_tea
                    
                self._inputs[level_id][r["reagent_id"]] = widgets
                row += 1
                
            g.setRowStretch(row, 1)
            scroll.setWidget(w)
            tab_layout.addWidget(scroll)
            
            self.tabs.addTab(tab_widget, f"{lvl_name} ({sub_batch_id})")

        # Change Reason Area
        reason_layout = QHBoxLayout()
        reason_layout.addWidget(QLabel("變更原因："))
        self.reason_combo = QComboBox()
        self.reason_combo.addItems(["", "新批號試劑", "新批號品管液", "平行測試後修訂", "其他原因"])
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("自訂備註 (若選擇其他則必填)")
        reason_layout.addWidget(self.reason_combo)
        reason_layout.addWidget(self.reason_input, 1)
        
        reason_container = QWidget()
        reason_container.setLayout(reason_layout)
        reason_container.setStyleSheet("background: #FFF3E0; border-radius: 4px;")
        layout.addWidget(reason_container)
        
        btn_row = QHBoxLayout()
        btn_save = QPushButton("儲存雙濃度設定")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _save(self):
        saved = 0
        from datetime import date
        today = date.today()
        
        combo_text = self.reason_combo.currentText()
        input_text = self.reason_input.text().strip()
        
        if combo_text and input_text:
            final_reason = f"{combo_text} - {input_text}"
        elif combo_text:
            final_reason = combo_text
        else:
            final_reason = input_text
            
        from services.qc_service import MasterService, TargetSettingService
        
        for sub in self.batch.get("sub_lots", []):
            level_id = sub["level_id"]
            lvl_name = sub["level_name"]
            sub_batch_id = sub["batch_id"]
            
            all_iqi_by_reagent = {}
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == lvl_name:
                        key = iqi["reagent_id"]
                        if key not in all_iqi_by_reagent:
                            all_iqi_by_reagent[key] = []
                        all_iqi_by_reagent[key].append(iqi["iqi_id"])
                        
            inputs = self._inputs.get(level_id, {})
            for reagent_id, w in inputs.items():
                iqis = all_iqi_by_reagent.get(reagent_id, [])
                if w["type"] == "semi":
                    s_min = w["min"].currentText().strip()
                    s_max = w["max"].currentText().strip()
                    if s_min and s_max:
                        for iqi_id in iqis:
                            TargetSettingService.save_semi_target(
                                iqi_id, sub_batch_id, s_min, s_max,
                                0, today, self.user["user_id"], final_reason
                            )
                        saved += 1
                else:
                    tm_txt = w["tm"].text().strip()
                    tsd_txt = w["tsd"].text().strip()
                    tea_txt = w["tea"].text().strip()
                    if tm_txt and tsd_txt:
                        try:
                            tm = float(tm_txt)
                            tsd = float(tsd_txt)
                            tea = float(tea_txt) if tea_txt else 0.0
                            for iqi_id in iqis:
                                TargetSettingService.save(
                                    iqi_id, sub_batch_id, tm, tsd,
                                    0, tea, 0, today, self.user["user_id"], final_reason
                                )
                            saved += 1
                        except ValueError:
                            pass
                            
        QMessageBox.information(self, "成功", f"成功儲存品管範圍設定。")
        self.accept()

"""

new_content = content[:start_idx] + new_class + content[end_idx:]

with open("ui/qc/qc_batch.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("TargetSettingDialog updated!")
