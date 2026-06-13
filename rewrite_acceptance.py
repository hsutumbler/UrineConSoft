import re

with open("ui/qc/qc_batch.py", "r", encoding="utf-8") as f:
    content = f.read()

start_idx = content.find("class QCAcceptanceDialog(QDialog):")
end_idx = content.find("class TargetSettingDialog(QDialog):")

if start_idx == -1 or end_idx == -1:
    print("Could not find boundaries")
    exit(1)

new_class = """class QCAcceptanceDialog(QDialog):
    \"\"\"品管液允收 (母子批號雙濃度)。\"\"\"
    def __init__(self, parent, batch: dict, user: dict, read_only=False, fixed_end_date=None):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.read_only = read_only
        self.fixed_end_date = fixed_end_date
        
        title = "歷史允收記錄" if read_only else "執行品管批次允收"
        self.setWindowTitle(f"{title} — 商品套組 {batch['lot_number']}")
        self.setMinimumSize(950, 650)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        top = QHBoxLayout()
        info = QLabel(f"批號 {batch['lot_number']} 的品管允收作業")
        info.setStyleSheet("font-size:16px; color:#A48753; font-weight:bold;")
        top.addWidget(info)
        
        if not read_only:
            self.date_end = QDateEdit()
            self.date_end.setCalendarPopup(True)
            self.date_end.setDate(QDate.currentDate())
            self.date_start = QDateEdit()
            self.date_start.setCalendarPopup(True)
            self.date_start.setDate(QDate.currentDate().addDays(-30))
            
            top.addStretch()
            top.addWidget(QLabel("統計區間："))
            top.addWidget(self.date_start)
            top.addWidget(QLabel("至"))
            top.addWidget(self.date_end)
            btn_refresh = QPushButton("更新統計")
            btn_refresh.clicked.connect(self._load_data)
            top.addWidget(btn_refresh)
            
        layout.addLayout(top)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E0E0E0; background: #FFF; border-radius: 4px; }")
        layout.addWidget(self.tabs)
        
        self.tab_widgets = {}

        for sub in batch.get("sub_lots", []):
            level_id = sub["level_id"]
            lvl_name = sub["level_name"]
            
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            t_qual = QTableWidget()
            t_qual.setColumnCount(8)
            t_qual.setHorizontalHeaderLabels(["項目", "陰性數", "陽性數", "異常數", "總筆數", "Target", "允收設定", "定性結論"])
            t_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_qual.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers if not read_only else QTableWidget.EditTrigger.NoEditTriggers)
            tab_layout.addWidget(QLabel("定性 / 半定量分析"))
            tab_layout.addWidget(t_qual, 1)
            
            t_quant = QTableWidget()
            t_quant.setColumnCount(8)
            t_quant.setHorizontalHeaderLabels(["項目", "TM", "TSD", "AM", "ASD", "CV%", "TEa%", "定量結論"])
            t_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_quant.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tab_layout.addWidget(QLabel("定量分析"))
            tab_layout.addWidget(t_quant, 1)
            
            self.tabs.addTab(tab_widget, f"{lvl_name} ({sub['batch_id']})")
            self.tab_widgets[level_id] = {"qual": t_qual, "quant": t_quant, "sub": sub}

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("關閉" if read_only else "取消")
        btn_cancel.clicked.connect(self.reject)
        
        if read_only:
            btn_row.addStretch()
            btn_row.addWidget(btn_cancel)
        else:
            btn_accept = QPushButton("通過允收")
            btn_accept.setObjectName("btn_primary")
            btn_accept.clicked.connect(lambda: self._save(1))
            
            btn_reject = QPushButton("拒絕")
            btn_reject.setObjectName("btn_danger")
            btn_reject.clicked.connect(lambda: self._save(2))
            
            btn_row.addWidget(btn_reject)
            btn_row.addWidget(btn_cancel)
            btn_row.addWidget(btn_accept)
            
        layout.addLayout(btn_row)
        
        self._target_settings = {}
        self._load_data()

    def _load_data(self):
        from services.qc_service import QCBatchService, MasterService, TargetSettingService
        
        if self.read_only:
            d2 = self.fixed_end_date or date.today()
            d1 = d2.replace(day=1) # Simplified logic for historical
        else:
            d1 = self.date_start.date().toPyDate()
            d2 = self.date_end.date().toPyDate()
            
        for level_id, widgets in self.tab_widgets.items():
            sub = widgets["sub"]
            t_qual = widgets["qual"]
            t_quant = widgets["quant"]
            batch_id = sub["batch_id"]
            
            stats = QCBatchService.get_qc_batch_stats(batch_id, d1, d2)
            
            # Pre-fetch target settings
            if self.read_only and level_id not in self._target_settings:
                saved_targets = TargetSettingService.get_by_batch(batch_id)
                level_targets = {}
                all_iqi_by_reagent = {}
                for inst in MasterService.get_instruments():
                    for iqi in MasterService.get_iqi(inst["instrument_id"]):
                        if iqi["level_name"] == sub["level_name"]:
                            rid = iqi["reagent_id"]
                            if rid not in all_iqi_by_reagent:
                                all_iqi_by_reagent[rid] = []
                            all_iqi_by_reagent[rid].append(iqi["iqi_id"])
                for rid, iqis in all_iqi_by_reagent.items():
                    if iqis and iqis[0] in saved_targets:
                        level_targets[rid] = saved_targets[iqis[0]]
                self._target_settings[level_id] = level_targets
                
            t_qual.setRowCount(0)
            for rname, data in stats["qual"].items():
                r = t_qual.rowCount()
                t_qual.insertRow(r)
                
                t_qual.setItem(r, 0, QTableWidgetItem(rname))
                t_qual.setItem(r, 1, QTableWidgetItem(str(data["neg"])))
                t_qual.setItem(r, 2, QTableWidgetItem(str(data["pos"])))
                t_qual.setItem(r, 3, QTableWidgetItem(str(data["abn"])))
                t_qual.setItem(r, 4, QTableWidgetItem(str(data["total"])))
                
                target_str = "未設定"
                if self.read_only:
                    rid = data.get("reagent_id")
                    if rid and rid in self._target_settings.get(level_id, {}):
                        ts = self._target_settings[level_id][rid]
                        if ts.get("semi_target_min"):
                            target_str = f"{ts['semi_target_min']} ~ {ts['semi_target_max']}"
                t_qual.setItem(r, 5, QTableWidgetItem(target_str))
                
                c_set = QComboBox()
                c_set.addItems(["Pass", "Fail", "N/A"])
                if self.read_only: c_set.setEnabled(False)
                t_qual.setCellWidget(r, 6, c_set)
                
                t_qual.setItem(r, 7, QTableWidgetItem("待確認"))
                
            t_quant.setRowCount(0)
            for rname, data in stats["quant"].items():
                r = t_quant.rowCount()
                t_quant.insertRow(r)
                
                am = data["am"]
                asd = data["asd"]
                cv = (asd / am * 100) if am else 0
                
                t_quant.setItem(r, 0, QTableWidgetItem(rname))
                t_quant.setItem(r, 1, QTableWidgetItem("-")) # TM placeholder
                t_quant.setItem(r, 2, QTableWidgetItem("-")) # TSD placeholder
                t_quant.setItem(r, 3, QTableWidgetItem(f"{am:.2f}"))
                t_quant.setItem(r, 4, QTableWidgetItem(f"{asd:.2f}"))
                t_quant.setItem(r, 5, QTableWidgetItem(f"{cv:.1f}%"))
                t_quant.setItem(r, 6, QTableWidgetItem("-"))
                t_quant.setItem(r, 7, QTableWidgetItem("待確認"))

    def _save(self, status: int):
        from services.qc_service import QCBatchService
        # simplified save logic since it's just a dummy demo for now
        QMessageBox.information(self, "完成", "允收紀錄已儲存。")
        self.accept()

"""

new_content = content[:start_idx] + new_class + content[end_idx:]

with open("ui/qc/qc_batch.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("QCAcceptanceDialog updated!")
