# ui/qc/qc_batch.py — 品管液批號管理（Quantimetrix）+ 允收 + TM/TSD 設定

from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialog, QFormLayout, QComboBox,
    QDateEdit, QTextEdit, QTableWidgetItem, QFrame,
    QTabWidget, QWidget, QMessageBox, QScrollArea,
    QGroupBox, QDoubleSpinBox, QRadioButton, QButtonGroup,
    QHeaderView, QTableWidget, QGridLayout,
)
from PyQt6.QtGui import QColor, QBrush
from PyQt6.QtCore import Qt, QDate
from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import (
    QCBatchService, MasterService, TargetSettingService, calc_stats
)
from datetime import date


SEMI_OPTIONS = ["Neg", "1+", "2+", "3+", "4+"]


class QCBatchPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("品管液批號管理", "Quantimetrix 批號管理、允收與 TM/TSD 設定", user)
        self._build()

    def _build(self):
        toolbar = QHBoxLayout()
        btn_add = QPushButton("＋ 新增批號")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_batch)

        self.btn_target = QPushButton("⚙️ 設定品管範圍")
        self.btn_target.setEnabled(False)
        self.btn_target.clicked.connect(self._open_target_setting)

        self.btn_accept = QPushButton("📋 執行允收")
        self.btn_accept.setEnabled(False)
        self.btn_accept.clicked.connect(self._run_acceptance)

        self.btn_activate = QPushButton("✅ 設為使用中")
        self.btn_activate.setEnabled(False)
        self.btn_activate.clicked.connect(self._activate_selected)
        
        self.btn_delete = QPushButton("🗑️ 刪除批號")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("color: #E74C3C;")
        self.btn_delete.clicked.connect(self._delete_batch)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(self.btn_target)
        toolbar.addWidget(self.btn_accept)
        toolbar.addWidget(self.btn_activate)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

        # 目前使用中
        self.lbl_active = QLabel("目前使用中批號：未設定")
        self.lbl_active.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{COLORS['accent']}; padding:8px;"
        )
        self.content_layout.addWidget(self.lbl_active)

        self.table = self.make_table(
            ["商品套組", "母批號", "穩定效期", "開封日", "狀態", "建立時間"]
        )
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.cellDoubleClicked.connect(lambda r, c: self._view_acceptance(r))
        self.content_layout.addWidget(self.table)

        hint = QLabel("💡 雙擊可查看允收記錄 | 需先選擇批號才能執行允收")
        hint.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px;")
        self.content_layout.addWidget(hint)

        self._load()

    def _load(self):
        batches = QCBatchService.get_all()
        active  = QCBatchService.get_active_batches()

        # Group active batches by lot_number
        active_groups = {}
        for b in active:
            lot = b["lot_number"]
            lvl = b["level_name"]
            if lot not in active_groups:
                active_groups[lot] = []
            active_groups[lot].append(lvl.replace("Level ", "L"))
            
        if active_groups:
            parts = sorted(active_groups.keys())
            self.lbl_active.setText("目前使用中：" + "、".join(parts))
        else:
            self.lbl_active.setText("目前使用中批號：未設定")

        archived_counts = {}
        display_batches = []
        for b in batches:
            if b.get("is_archived"):
                if archived_counts.get("total", 0) < 4:
                    archived_counts["total"] = archived_counts.get("total", 0) + 1
                    display_batches.append(b)
            else:
                display_batches.append(b)

        self.table.setRowCount(0)
        for r, b in enumerate(display_batches):
            self.table.insertRow(r)
            if b.get("is_archived"):
                status = "📦 已退役"
            elif b["is_active"]:
                status = "✅ 使用中"
            else:
                status = "⏳ 待允收"
                
            sub_count = len(b.get("sub_lots", []))
            level_str = "雙濃度 (L1/L2)" if sub_count == 2 else f"{sub_count} 種濃度"
            
            vals = [
                level_str,
                b["lot_number"],
                str(b["expiry_date"] or ""),
                str(b["open_date"] or ""),
                status,
                str(b["created_at"])[:16],
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, b)
                self.table.setItem(r, c, item)

        self._on_selection()

    def _on_selection(self):
        has = self.table.currentRow() >= 0
        self.btn_activate.setEnabled(has)
        self.btn_accept.setEnabled(has)
        self.btn_target.setEnabled(has)
        self.btn_delete.setEnabled(has)

    def _get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _add_batch(self):
        dlg = QCBatchDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            mother_lot = QCBatchService.create_mother_batch(
                d["lot_number"], d["l1_lot_id"], d["l2_lot_id"], d["expiry_date"],
                d["open_date"], d["notes"], self.user["user_id"]
            )
            self._load()

    def _activate_selected(self):
        b = self._get_selected()
        if not b:
            return
        is_currently_active = b.get("is_active")
        action_name = "取消使用並退役" if is_currently_active else "設為使用中"
        if not self.confirm("確認", f"確定要將母批號 {b['lot_number']} (及所有關聯濃度) {action_name}？", default_yes=not is_currently_active):
            return
        QCBatchService.toggle_active(b["lot_number"], not is_currently_active)
        self._load()

    def _delete_batch(self):
        b = self._get_selected()
        if not b:
            return
        if b.get("is_active"):
            QMessageBox.warning(self, "警告", "無法刪除目前使用中的批號！請先設定其他批號為使用中。")
            return
            
        if b.get("is_archived"):
            QMessageBox.warning(self, "警告", "無法刪除已退役的批號！這屬於歷史紀錄的一部分。")
            return
            
        if not self.confirm("刪除確認", f"確定要刪除母批號 {b['lot_number']} 及所有關聯設定嗎？\n此操作無法復原。"):
            return
        QCBatchService.delete(b["lot_number"])
        self._load()

    def _run_acceptance(self):
        b = self._get_selected()
        if not b:
            return
        dlg = QCAcceptanceDialog(self, b, self.user)
        dlg.exec()
        self._load()

    def _open_target_setting(self):
        b = self._get_selected()
        if not b:
            return
        dlg = TargetSettingDialog(self, b, self.user)
        dlg.exec()

    def _view_acceptance(self, row: int):
        item = self.table.item(row, 0)
        if not item:
            return
        b = item.data(Qt.ItemDataRole.UserRole)
        if not b:
            return
        # Find the acceptance date for this batch from the records
        records = QCBatchService.get_acceptance_records(b["batch_id"])
        if not records:
            QMessageBox.information(self, "提示", "查無此批號的歷史允收紀錄。")
            return
            
        accepted_at = records[0]["accepted_at"].date()
        dlg = QCAcceptanceDialog(self, b, self.user, read_only=True, fixed_end_date=accepted_at)
        dlg.exec()

    def on_page_show(self):
        self._load()


class QCBatchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("新增品管液批號")
        self.setFixedWidth(420)
        self.setStyleSheet(PAGE_STYLE)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(24, 24, 24, 24)

        self.f_lot = QLineEdit()
        self.f_lot.setPlaceholderText("輸入母批號 (如: C252880)")
        self.f_lot.textChanged.connect(self._on_lot_changed)
        
        self.f_l1_lot = QLineEdit()
        self.f_l1_lot.setPlaceholderText("Level 1 儀器代碼 (如: C252881)")
        self.f_l2_lot = QLineEdit()
        self.f_l2_lot.setPlaceholderText("Level 2 儀器代碼 (如: C252882)")
        
        self.f_exp = QDateEdit()
        self.f_exp.setCalendarPopup(True)
        self.f_exp.setDate(QDate.currentDate().addMonths(6))
        self.f_open = QDateEdit()
        self.f_open.setCalendarPopup(True)
        self.f_open.setDate(QDate.currentDate())
        self.f_notes = QTextEdit()
        self.f_notes.setFixedHeight(60)

        form.addRow("母批號 (群組名) *", self.f_lot)
        form.addRow("Level 1 儀器代碼", self.f_l1_lot)
        form.addRow("Level 2 儀器代碼", self.f_l2_lot)
        form.addRow("穩定效期",         self.f_exp)
        form.addRow("開封日",       self.f_open)
        form.addRow("備註",         self.f_notes)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("儲存")
        btn_ok.setObjectName("btn_primary")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self._validate)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        form.addRow(btn_row)

    def _on_lot_changed(self, text: str):
        # Auto-fill sub-lots logic if user types something like C252880
        if text.endswith("0") and len(text) > 4:
            base = text[:-1]
            if not self.f_l1_lot.text() or self.f_l1_lot.text().startswith(base):
                self.f_l1_lot.setText(base + "1")
            if not self.f_l2_lot.text() or self.f_l2_lot.text().startswith(base):
                self.f_l2_lot.setText(base + "2")

    def _validate(self):
        if not self.f_lot.text().strip():
            QMessageBox.warning(self, "驗證", "母批號為必填")
            return
        if not self.f_l1_lot.text().strip() or not self.f_l2_lot.text().strip():
            QMessageBox.warning(self, "驗證", "Level 1 與 Level 2 儀器代碼皆為必填")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "lot_number": self.f_lot.text().strip(),
            "l1_lot_id": self.f_l1_lot.text().strip(),
            "l2_lot_id": self.f_l2_lot.text().strip(),
            "expiry_date": self.f_exp.date().toString("yyyy-MM-dd"),
            "open_date": self.f_open.date().toString("yyyy-MM-dd"),
            "notes": self.f_notes.toPlainText().strip()
        }


class QCAcceptanceDialog(QDialog):
    """品管液允收 (母子批號雙濃度)。"""
    def __init__(self, parent, batch: dict, user: dict, read_only=False, fixed_end_date=None):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.read_only = read_only
        self.fixed_end_date = fixed_end_date
        
        title = "歷史允收記錄" if read_only else "執行品管批次允收"
        self.setWindowTitle(f"{title} — 商品套組 {batch['lot_number']}")
        self.setMinimumSize(950, 750)
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
            t_qual.setColumnCount(7)
            t_qual.setHorizontalHeaderLabels(["項目", "正常數", "異常數", "總筆數", "Target", "允收設定", "定性結論"])
            t_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_qual.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers if not read_only else QTableWidget.EditTrigger.NoEditTriggers)
            tab_layout.addWidget(QLabel("定性 / 半定量分析"))
            tab_layout.addWidget(t_qual, 4)
            
            t_quant = QTableWidget()
            t_quant.setColumnCount(8)
            t_quant.setHorizontalHeaderLabels(["項目", "TM", "TSD", "AM", "ASD", "CV%", "TEa%", "定量結論"])
            t_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_quant.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            t_quant.setMaximumHeight(100)
            
            lbl_quant = QLabel("定量項目：")
            lbl_quant.setStyleSheet("font-weight: bold; margin-top: 10px;")
            tab_layout.addWidget(lbl_quant)
            tab_layout.addWidget(t_quant)
            
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
            
            btn_row.addStretch()
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
                t_qual.setItem(r, 1, QTableWidgetItem(str(data["passed"])))
                t_qual.setItem(r, 2, QTableWidgetItem(str(data["failed"])))
                t_qual.setItem(r, 3, QTableWidgetItem(str(data["n"])))
                
                target_str = "未設定"
                if self.read_only:
                    rid = data.get("reagent_id")
                    if rid and rid in self._target_settings.get(level_id, {}):
                        ts = self._target_settings[level_id][rid]
                        if ts.get("semi_target_min"):
                            target_str = f"{ts['semi_target_min']} ~ {ts['semi_target_max']}"
                t_qual.setItem(r, 4, QTableWidgetItem(target_str))
                
                c_set = QComboBox()
                c_set.addItems(["Pass", "Fail", "N/A"])
                if self.read_only: c_set.setEnabled(False)
                t_qual.setCellWidget(r, 5, c_set)
                
                t_qual.setItem(r, 6, QTableWidgetItem("待確認"))
                
            t_quant.setRowCount(0)
            for rname, data in stats["quant"].items():
                r = t_quant.rowCount()
                t_quant.insertRow(r)
                
                am = data["am"]
                asd = data["asd"]
                tm = data.get("tm")
                tsd = data.get("tsd")
                cv = (asd / am * 100) if am and asd is not None else 0
                
                tm_str = f"{tm:.2f}" if tm is not None else "-"
                tsd_str = f"{tsd:.2f}" if tsd is not None else "-"
                am_str = f"{am:.2f}" if am is not None else "-"
                asd_str = f"{asd:.2f}" if asd is not None else "-"
                cv_str = f"{cv:.1f}%" if am is not None else "-"
                
                t_quant.setItem(r, 0, QTableWidgetItem(rname))
                t_quant.setItem(r, 1, QTableWidgetItem(tm_str))
                t_quant.setItem(r, 2, QTableWidgetItem(tsd_str))
                t_quant.setItem(r, 3, QTableWidgetItem(am_str))
                t_quant.setItem(r, 4, QTableWidgetItem(asd_str))
                t_quant.setItem(r, 5, QTableWidgetItem(cv_str))
                t_quant.setItem(r, 6, QTableWidgetItem("-"))
                t_quant.setItem(r, 7, QTableWidgetItem("待確認"))

    def _save(self, status: int):
        from services.qc_service import QCBatchService
        # simplified save logic since it's just a dummy demo for now
        QMessageBox.information(self, "完成", "允收紀錄已儲存。")
        self.accept()

class TargetSettingDialog(QDialog):
    """設定品管範圍 (母子批號雙濃度)"""
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
        
        btn_load_active = QPushButton("📥 載入品管範圍")
        btn_load_active.setToolTip("將目前使用中批號的範圍載入至下方")
        btn_load_active.clicked.connect(self._load_active_targets)
        top_row.addStretch()
        top_row.addWidget(btn_load_active)
        
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
                            
            is_chem_lot = batch["lot_number"].upper().startswith("C")
            is_sed_lot = batch["lot_number"].upper().startswith("D")
            
            row = 1
            for r in reagents:
                is_sed_reagent = r['reagent_name'] in ("RBC", "WBC")
                if is_chem_lot and is_sed_reagent:
                    continue
                if is_sed_lot and not is_sed_reagent:
                    continue
                    
                disp_name = r['reagent_name']
                g.addWidget(QLabel(disp_name), row, 0)
                
                widgets = {}
                if r["param_type"] in (2, 3): # Semi
                    c_min = QComboBox()
                    c_max = QComboBox()
                    if r["param_type"] == 2:
                        if disp_name == "NIT":
                            c_min.addItems(["Neg", "Pos"])
                            c_max.addItems(["Neg", "Pos"])
                        else:
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
        btn_save = QPushButton("儲存")
        btn_save.setObjectName("btn_primary")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

    def _load_active_targets(self):
        from services.qc_service import MasterService, TargetSettingService
        
        ans = QMessageBox.question(self, "確認", "確定要載入目前使用中批號的品管範圍嗎？這將覆蓋您目前輸入的內容。",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                   QMessageBox.StandardButton.Yes)
        if ans != QMessageBox.StandardButton.Yes:
            return
            
        loaded_count = 0
        prefix = self.batch["lot_number"][0].upper()
        from services.qc_service import QCBatchService
        
        for sub in self.batch.get("sub_lots", []):
            level_id = sub["level_id"]
            lvl_name = sub["level_name"]
            
            # Find the active batch id with the same prefix for this level
            target_sub_batch_id = QCBatchService.get_active_sub_batch_id(str(level_id), prefix)
            if not target_sub_batch_id:
                continue
            
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == lvl_name:
                        ts = TargetSettingService.get_for_batch(iqi["iqi_id"], target_sub_batch_id)
                        if ts:
                            reagent_id = iqi["reagent_id"]
                            if level_id in self._inputs and reagent_id in self._inputs[level_id]:
                                w = self._inputs[level_id][reagent_id]
                                if w["type"] == "semi":
                                    s_min = ts.get("semi_target_min")
                                    s_max = ts.get("semi_target_max")
                                    if s_min: w["min"].setCurrentText(s_min)
                                    if s_max: w["max"].setCurrentText(s_max)
                                else:
                                    if ts.get("tm") is not None: w["tm"].setText(str(ts["tm"]))
                                    if ts.get("tsd") is not None: w["tsd"].setText(str(ts["tsd"]))
                                    if ts.get("tea_percent") is not None: w["tea"].setText(str(ts["tea_percent"]))
                                loaded_count += 1
                                
        if loaded_count > 0:
            QMessageBox.information(self, "成功", "已載入目前使用中批號的品管範圍。")
        else:
            QMessageBox.information(self, "提示", "目前沒有使用中的批號或查無設定。")

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

