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


SEMI_OPTIONS = ["Neg", "Trace", "1+", "2+", "3+"]


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

        toolbar.addWidget(btn_add)
        toolbar.addWidget(self.btn_target)
        toolbar.addWidget(self.btn_accept)
        toolbar.addWidget(self.btn_activate)
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

        # 目前使用中
        self.lbl_active = QLabel("目前使用中：Level 1 — 未設定  |  Level 2 — 未設定")
        self.lbl_active.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{COLORS['accent']}; padding:8px;"
        )
        self.content_layout.addWidget(self.lbl_active)

        self.table = self.make_table(
            ["濃度", "批號", "效期", "開封日", "狀態", "建立時間"]
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

        l1_lot = l2_lot = "未設定"
        for b in active:
            if b["level_name"] == "Level 1":
                l1_lot = b["lot_number"]
            elif b["level_name"] == "Level 2":
                l2_lot = b["lot_number"]
        self.lbl_active.setText(
            f"目前使用中：Level 1 — {l1_lot}  |  Level 2 — {l2_lot}"
        )

        seen = {}
        display_batches = []
        archived_counts = {}
        for b in batches:
            key = (b["batch_id"],)
            if key in seen:
                continue
            seen[key] = True
            
            if b.get("is_archived"):
                lvl = b["level_id"]
                if archived_counts.get(lvl, 0) < 2:
                    archived_counts[lvl] = archived_counts.get(lvl, 0) + 1
                    display_batches.append(b)
            else:
                display_batches.append(b)

        self.table.setRowCount(0)
        for r, b in enumerate(display_batches):
            self.table.insertRow(r)
            level_unique = b["level_name"]
            if b.get("is_archived"):
                status = "📦 已退役"
            elif b["is_active"]:
                status = "✅ 使用中"
            else:
                status = "⏳ 待允收"
            vals = [
                level_unique,
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
            batch_id = QCBatchService.create(
                d["level_id"], d["lot_number"], d["expiry_date"],
                d["open_date"], d["notes"], self.user["user_id"]
            )
            self._load()
            if self.confirm("設為使用中", "是否立即將此批號設為目前使用中？", default_yes=True):
                b = QCBatchService.get_all()
                level_id = d["level_id"]
                QCBatchService.set_active(batch_id, level_id)
                self._load()

    def _activate_selected(self):
        b = self._get_selected()
        if not b:
            return
        if not self.confirm("確認", f"將批號 {b['lot_number']} 設為使用中？", default_yes=True):
            return
        QCBatchService.set_active(b["batch_id"], b["level_id"])
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

        self.f_level = QComboBox()
        # Level 是依品管液中同 level_name 的第一個 level_id 代表
        self.f_level.addItem("Level 1（低值）", 1)   # level_id=1 代表 pH Level 1（所有參數共享批號）
        self.f_level.addItem("Level 2（高值）", 2)   # level_id=2 代表 pH Level 2

        self.f_lot = QLineEdit()
        self.f_lot.setPlaceholderText("輸入批號")
        self.f_exp = QDateEdit()
        self.f_exp.setCalendarPopup(True)
        self.f_exp.setDate(QDate.currentDate().addMonths(6))
        self.f_open = QDateEdit()
        self.f_open.setCalendarPopup(True)
        self.f_open.setDate(QDate.currentDate())
        self.f_notes = QTextEdit()
        self.f_notes.setFixedHeight(60)

        form.addRow("品管液濃度 *", self.f_level)
        form.addRow("批號 *",       self.f_lot)
        form.addRow("效期",         self.f_exp)
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

    def _validate(self):
        if not self.f_lot.text().strip():
            QMessageBox.warning(self, "驗證", "批號為必填")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "level_id":   self.f_level.currentData(),
            "lot_number": self.f_lot.text().strip(),
            "expiry_date":self.f_exp.date().toPyDate(),
            "open_date":  self.f_open.date().toPyDate(),
            "notes":      self.f_notes.toPlainText().strip(),
        }


class QCAcceptanceDialog(QDialog):
    """品管液允收。"""
    def __init__(self, parent, batch: dict, user: dict, read_only=False, fixed_end_date=None):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.read_only = read_only
        self.fixed_end_date = fixed_end_date
        
        title = "歷史允收記錄" if read_only else "執行品管批次允收"
        self.setWindowTitle(f"{title} — {batch.get('level_name','')} 批號 {batch['lot_number']}")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Date range for fetching overlap data
        self.date_layout = QHBoxLayout()
        self.date_layout.addWidget(QLabel("評估資料期間："))
        
        self.d_start = QDateEdit()
        self.d_start.setCalendarPopup(True)
        if batch.get("open_date"):
            self.d_start.setDate(batch["open_date"])
        else:
            self.d_start.setDate(QDate.currentDate().addMonths(-1))
            
        self.d_end = QDateEdit()
        self.d_end.setCalendarPopup(True)
        self.d_end.setDate(QDate.currentDate())
        
        self.d_start.dateChanged.connect(self._refresh_stats)
        self.d_end.dateChanged.connect(self._refresh_stats)
        
        self.date_layout.addWidget(self.d_start)
        self.date_layout.addWidget(QLabel(" ~ "))
        self.date_layout.addWidget(self.d_end)
        self.date_layout.addStretch()
        
        if not self.read_only:
            layout.addLayout(self.date_layout)
        else:
            acc_by = self.batch.get("accepted_by_name", "Unknown")
            acc_at = self.batch.get("accepted_at", self.fixed_end_date)
            lbl_info = QLabel(f"歷史允收紀錄  |  執行人員：{acc_by}  |  時間：{acc_at}")
            lbl_info.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
            layout.addWidget(lbl_info)
        
        # Tab Widget for tables
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Bottom Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        if self.read_only:
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setStyleSheet("background-color: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; border-radius: 4px; padding: 8px 24px; font-weight: bold;")
            btn_export.clicked.connect(self._export_pdf)
            btn_row.addWidget(btn_export)

            btn_close = QPushButton("關閉")
            btn_close.setStyleSheet("background-color: #E6F7FF; color: #0056B3; border: 1px solid #91D5FF; border-radius: 4px; padding: 8px 24px; font-weight: bold;")
            btn_close.clicked.connect(self.accept)
            btn_row.addWidget(btn_close)
        else:
            btn_accept = QPushButton("允收")
            btn_accept.setObjectName("btn_primary")
            btn_accept.clicked.connect(lambda: self._save(1))
            
            btn_cancel = QPushButton("取消")
            btn_cancel.clicked.connect(self.reject)
            
            btn_reject = QPushButton("拒絕")
            btn_reject.setObjectName("btn_danger")
            btn_reject.clicked.connect(lambda: self._save(2))
            
            btn_row.addWidget(btn_reject)
            btn_row.addWidget(btn_cancel)
            btn_row.addWidget(btn_accept)
            
        layout.addLayout(btn_row)
        
        self._input_widgets = {} # reagent_id -> (tm_input, tsd_input)
        self._refresh_stats()

    def _refresh_stats(self):
        # clear previous tabs
        self.tabs.clear()
                
        if self.read_only and self.fixed_end_date:
            d1 = self.d_start.date().toPyDate() # Just use open date or 1 month prior
            d2 = self.fixed_end_date
        else:
            d1 = self.d_start.date().toPyDate()
            d2 = self.d_end.date().toPyDate()
        
        stats = QCBatchService.get_qc_batch_stats(self.batch["batch_id"], d1, d2)
        self._stats = stats
        
        # Build Qualitative Table
        grp_qual = QGroupBox("定性/半定量項目統計")
        grp_qual.setStyleSheet("font-weight: bold; color: #333;")
        l_qual = QVBoxLayout(grp_qual)
        
        t_qual = QTableWidget(0, 7)
        t_qual.setHorizontalHeaderLabels(["項目", "N", "目前範圍", "合格筆數", "不合格筆數", "設定下限", "設定上限"])
        t_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t_qual.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        t_qual.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        t_qual.setAlternatingRowColors(True)
        t_qual.verticalHeader().setVisible(False)
        
        from PyQt6.QtWidgets import QStyledItemDelegate
        from PyQt6.QtGui import QPen
        class QualBorderDelegate(QStyledItemDelegate):
            def createEditor(self, parent, option, index):
                if index.column() in (5, 6):
                    cb = QComboBox(parent)
                    cb.setEditable(True)
                    cb.addItems(SEMI_OPTIONS)
                    return cb
                return super().createEditor(parent, option, index)
                
            def setModelData(self, editor, model, index):
                if isinstance(editor, QComboBox):
                    model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
                else:
                    super().setModelData(editor, model, index)

            def paint(self, painter, option, index):
                super().paint(painter, option, index)
                row, col, rows = index.row(), index.column(), index.model().rowCount()
                if col in (5, 6):
                    painter.save()
                    painter.setPen(QPen(Qt.GlobalColor.black, 3))
                    r = option.rect
                    if row == 0:
                        painter.drawLine(r.topLeft(), r.topRight())
                    if row == rows - 1:
                        painter.drawLine(r.bottomLeft(), r.bottomRight())
                    if col == 5:
                        painter.drawLine(r.topLeft(), r.bottomLeft())
                    if col == 6:
                        painter.drawLine(r.topRight(), r.bottomRight())
                    painter.restore()
        t_qual.setItemDelegate(QualBorderDelegate(t_qual))
        
        self._sq_inputs = {}
        from services.qc_service import MasterService, TargetSettingService
        reagents = MasterService.get_reagents()
        r_map = {r["reagent_name"]: r["reagent_id"] for r in reagents}
        
        # Pre-fetch historical target settings if read-only
        self._target_settings = {}
        if self.read_only:
            saved_targets = TargetSettingService.get_by_batch(self.batch["batch_id"])
            all_iqi_by_reagent = {}
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == self.batch["level_name"]:
                        rid = iqi["reagent_id"]
                        if rid not in all_iqi_by_reagent:
                            all_iqi_by_reagent[rid] = []
                        all_iqi_by_reagent[rid].append(iqi["iqi_id"])
            for rid, iqis in all_iqi_by_reagent.items():
                if iqis and iqis[0] in saved_targets:
                    self._target_settings[rid] = saved_targets[iqis[0]]
            print(f"DEBUG read_only target_settings: {self._target_settings}")
        
        for rname, data in stats["qual"].items():
            r = t_qual.rowCount()
            t_qual.insertRow(r)
            
            vals = [rname, data["n"], data["range"], data["passed"], data["failed"]]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c in (0, 1):
                    it.setBackground(QBrush(QColor("#FFFFFF")))
                elif c in (2, 3, 4):
                    it.setBackground(QBrush(QColor("#FFF3E0")))
                t_qual.setItem(r, c, it)
                
            it_min = QTableWidgetItem()
            s_min = data.get("s_min")
            if self.read_only:
                rid = r_map.get(rname)
                ts = self._target_settings.get(rid, {})
                s_min = ts.get("semi_target_min")
                print(f"DEBUG {rname} s_min: {s_min}")
            if s_min is not None:
                it_min.setText(str(s_min))
            it_min.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.read_only:
                it_min.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                it_min.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                it_min.setBackground(QBrush(QColor("#E3F2FD")))
            t_qual.setItem(r, 5, it_min)
            
            it_max = QTableWidgetItem()
            s_max = data.get("s_max")
            if self.read_only:
                rid = r_map.get(rname)
                ts = self._target_settings.get(rid, {})
                s_max = ts.get("semi_target_max")
            if s_max is not None:
                it_max.setText(str(s_max))
            it_max.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.read_only:
                it_max.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                it_max.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                it_max.setBackground(QBrush(QColor("#E3F2FD")))
            t_qual.setItem(r, 6, it_max)
            
            self._sq_inputs[r_map.get(rname)] = (it_min, it_max)
                
        l_qual.addWidget(t_qual)
        
        qual_tab = QWidget()
        qual_layout = QVBoxLayout(qual_tab)
        qual_layout.setContentsMargins(12, 12, 12, 12)
        qual_layout.addWidget(grp_qual)
        self.tabs.addTab(qual_tab, "定性 / 半定量")
        
        # Build Quantitative Table
        grp_quant = QGroupBox("定量項目統計與目標設定")
        grp_quant.setStyleSheet("font-weight: bold; color: #333;")
        l_quant = QVBoxLayout(grp_quant)
        
        t_quant = QTableWidget(0, 8)
        t_quant.setHorizontalHeaderLabels(["項目", "N", "Target Mean", "Actual Mean", "Target SD", "Actual SD", "設定Mean", "設定SD"])
        t_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t_quant.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        t_quant.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        t_quant.setAlternatingRowColors(True)
        t_quant.verticalHeader().setVisible(False)
        
        # Delegate to draw thick borders for column grouping
        from PyQt6.QtWidgets import QStyledItemDelegate
        from PyQt6.QtGui import QPen
        class GroupBorderDelegate(QStyledItemDelegate):
            def paint(self, painter, option, index):
                super().paint(painter, option, index)
                row = index.row()
                col = index.column()
                rows = index.model().rowCount()
                if col in (2, 3, 4, 5, 6, 7):
                    painter.save()
                    pen = QPen(Qt.GlobalColor.black, 3)
                    painter.setPen(pen)
                    rect = option.rect
                    
                    # Top border
                    if row == 0:
                        painter.drawLine(rect.topLeft(), rect.topRight())
                    # Bottom border
                    if row == rows - 1:
                        painter.drawLine(rect.bottomLeft(), rect.bottomRight())
                    # Left borders of groups
                    if col in (2, 4, 6):
                        painter.drawLine(rect.topLeft(), rect.bottomLeft())
                    # Right borders of groups
                    if col in (3, 5, 7):
                        painter.drawLine(rect.topRight(), rect.bottomRight())
                        
                    painter.restore()
        
        t_quant.setItemDelegate(GroupBorderDelegate(t_quant))
        
        self._input_widgets = {}
        
        # Map reagent_name back to reagent_id for saving
        from services.qc_service import MasterService
        reagents = MasterService.get_reagents()
        r_map = {r["reagent_name"]: r["reagent_id"] for r in reagents}
        
        for rname, data in stats["quant"].items():
            r = t_quant.rowCount()
            t_quant.insertRow(r)
            
            dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC") else 2)
            
            # AM, ASD formatting
            am = f"{data['am']:.{dec}f}" if data['am'] is not None else "—"
            asd = f"{data['asd']:.{dec}f}" if data['asd'] is not None else "—"
            tm = f"{data['tm']:.{dec}f}" if data['tm'] is not None else "—"
            tsd = f"{data['tsd']:.{dec}f}" if data['tsd'] is not None else "—"
            
            vals = [rname, data["n"], tm, am, tsd, asd]
            for c, v in enumerate(vals):
                it = QTableWidgetItem(str(v))
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it.setFlags(it.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if c in (0, 1):
                    it.setBackground(QBrush(QColor("#FFFFFF")))
                elif c in (2, 3):
                    it.setBackground(QBrush(QColor("#FFF3E0"))) # Light Orange
                elif c in (4, 5):
                    it.setBackground(QBrush(QColor("#E8F5E9"))) # Light Green
                t_quant.setItem(r, c, it)
                
            # Editable Item Mean
            inp_mean = QTableWidgetItem()
            m_val = data['am']
            if self.read_only:
                rid = r_map.get(rname)
                ts = self._target_settings.get(rid, {})
                m_val = ts.get("tm")
                print(f"DEBUG {rname} m_val: {m_val}")
            if m_val is not None:
                inp_mean.setText(f"{m_val:.{dec}f}")
            inp_mean.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.read_only:
                inp_mean.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                inp_mean.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                inp_mean.setBackground(QBrush(QColor("#E3F2FD"))) # Light Blue
            t_quant.setItem(r, 6, inp_mean)
            
            # Editable Item SD
            inp_sd = QTableWidgetItem()
            sd_val = data['tsd']
            if self.read_only:
                rid = r_map.get(rname)
                ts = self._target_settings.get(rid, {})
                sd_val = ts.get("tsd")
            if sd_val is not None:
                inp_sd.setText(f"{sd_val:.{dec}f}")
            inp_sd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if self.read_only:
                inp_sd.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
            else:
                inp_sd.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                inp_sd.setBackground(QBrush(QColor("#E3F2FD"))) # Light Blue
            t_quant.setItem(r, 7, inp_sd)
            
            self._input_widgets[r_map.get(rname)] = (inp_mean, inp_sd)
            
        l_quant.addWidget(t_quant)
        
        quant_tab = QWidget()
        quant_layout = QVBoxLayout(quant_tab)
        quant_layout.setContentsMargins(12, 12, 12, 12)
        quant_layout.addWidget(grp_quant)
        self.tabs.addTab(quant_tab, "定量")

    def _save(self, status: int):
        status_map = {1: "允收", 2: "拒絕"}
        st = status_map[status]
        
        if not self.confirm("確認決策", f"確定要將批號 {self.batch['lot_number']} 標記為「{st}」嗎？", default_yes=True):
            return
            
        # 1. Update qc_batches acceptance_status
        QCBatchService.save_qc_batch_acceptance(self.batch["batch_id"], status)
        
        # 1.5 Save to qc_batch_acceptance table so Inquiry can find it
        if hasattr(self, '_stats'):
            from services.qc_service import MasterService
            reagents = MasterService.get_reagents()
            r_map_rev = {r["reagent_id"]: r["reagent_name"] for r in reagents}
            
            all_reagents_for_batch = set()
            for inst in MasterService.get_instruments():
                for iqi in MasterService.get_iqi(inst["instrument_id"]):
                    if iqi["level_name"] == self.batch["level_name"]:
                        all_reagents_for_batch.add(iqi["reagent_id"])
                        
            for rid in all_reagents_for_batch:
                rname = r_map_rev.get(rid)
                qual_data = self._stats.get("qual", {}).get(rname)
                quant_data = self._stats.get("quant", {}).get(rname)
                
                if qual_data:
                    s_res = f"Pass:{qual_data['passed']} Fail:{qual_data['failed']}"
                    QCBatchService.save_acceptance(
                        self.batch["batch_id"], rid, 2, s_res, qual_data["range"],
                        qual_data['failed'] == 0, None, None, None, status == 1, "", self.user["user_id"]
                    )
                elif quant_data:
                    QCBatchService.save_acceptance(
                        self.batch["batch_id"], rid, 1, None, None, True, None, 
                        quant_data["am"], quant_data["asd"], status == 1, "", self.user["user_id"]
                    )
                else:
                    reagent = next((r for r in reagents if r["reagent_id"] == rid), None)
                    if reagent:
                        accept_type = 1 if reagent["param_type"] == 1 else 2
                        QCBatchService.save_acceptance(
                            self.batch["batch_id"], rid, accept_type, None, None, True, None, 
                            None, None, status == 1, "無測量數據", self.user["user_id"]
                        )
        
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
                        
            # Save Semi Targets
            if hasattr(self, '_sq_inputs'):
                for reagent_id, (it_min, it_max) in self._sq_inputs.items():
                    if not reagent_id: continue
                    s_min = it_min.text().strip()
                    s_max = it_max.text().strip()
                    iqis = all_iqi_by_reagent.get(reagent_id, [])
                    for iqi_id in iqis:
                        TargetSettingService.save_semi_target(
                            iqi_id, self.batch["batch_id"], s_min, s_max,
                            mode=2, effective_from=today, set_by=self.user["user_id"]
                        )
                        saved += 1
                        
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
            msg += f"\n並寫入 {saved} 項定量項目的設定值。"
            
        QMessageBox.information(self, "完成", msg)
        
        # 如果是允收，自動設為使用中
        if status == 1:
            QCBatchService.set_active(self.batch["batch_id"], self.batch["level_id"])
            
        self.accept()
        
    def confirm(self, title, msg, default_yes=False):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes

    def _export_pdf(self):
        try:
            from PyQt6.QtPrintSupport import QPrinter
        except ImportError:
            QMessageBox.critical(self, "錯誤", "缺少列印支援套件。")
            return
            
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtWidgets import QFileDialog
        
        default_name = f"品管液允收紀錄單_{self.batch['lot_number']}.pdf"
        filepath, _ = QFileDialog.getSaveFileName(self, "儲存 PDF", default_name, "PDF Files (*.pdf)")
        
        if not filepath:
            return
            
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(filepath)
        
        doc = QTextDocument()
        doc.setHtml(self._get_print_html())
        doc.print(printer)
        
        QMessageBox.information(self, "成功", f"PDF 已成功儲存至：\\n{filepath}")

    def _get_print_html(self):
        acc_by = self.batch.get('accepted_by_name', 'Unknown')
        acc_at = self.batch.get('accepted_at', self.fixed_end_date)
        
        # Get expiry date
        expiry_date = ""
        try:
            from database.connection import DBContext
            with DBContext() as (_, cur):
                cur.execute("SELECT expiry_date FROM qc_batches WHERE batch_id = %s", (self.batch['batch_id'],))
                r = cur.fetchone()
                if r and r['expiry_date']:
                    expiry_date = r['expiry_date'].strftime('%Y/%m/%d')
        except:
            pass
        
        html = f"""
        <div style="font-family: sans-serif; color: #000;">
            <h1 style="font-size: 16pt; text-align: center; margin-top: 0; margin-bottom: 20px; font-weight: bold;">品管液允收紀錄單</h1>
            
            <table width="100%" cellpadding="0" cellspacing="0" style="border: 2px solid #000; margin-bottom: 15px;">
                <tr><td>
                    <table width="100%" border="0" cellpadding="8" cellspacing="0" style="font-size: 12pt;">
                        <tr>
                            <td width="50%" style="border-bottom: 1px dotted #ccc;"><b>批號：</b> {self.batch['lot_number']} ({self.batch.get('level_name','')})</td>
                            <td width="50%" style="border-bottom: 1px dotted #ccc;"><b>執行人員：</b> {acc_by}</td>
                        </tr>
                        <tr>
                            <td colspan="2" style="border-bottom: 1px dotted #ccc;"><b>穩定效期：</b> {expiry_date}</td>
                        </tr>
                        <tr>
                            <td colspan="2"><b>允收時間：</b> {acc_at}</td>
                        </tr>
                    </table>
                </td></tr>
            </table>
            
            <h3 style="font-size: 12pt; margin: 10px 0;">定性 / 半定量項目</h3>
            <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 12pt; border: 1px solid #000; border-collapse: collapse; margin-bottom: 20px;">
                <tr style="background-color: #f0f0f0;">
                    <th style="border: 1px solid #000;">項目</th>
                    <th style="border: 1px solid #000;">N</th>
                    <th style="border: 1px solid #000;">目前範圍</th>
                    <th style="border: 1px solid #000;">合格</th>
                    <th style="border: 1px solid #000;">不合格</th>
                    <th style="border: 1px solid #000;">設定下限</th>
                    <th style="border: 1px solid #000;">設定上限</th>
                </tr>
        """
        t_qual = self.tabs.widget(0).findChild(QTableWidget)
        if t_qual:
            for r in range(t_qual.rowCount()):
                html += "<tr>"
                for c in range(7):
                    item = t_qual.item(r, c)
                    text = item.text() if item else ""
                    html += f"<td style='border: 1px solid #000; text-align: center;'>{text}</td>"
                html += "</tr>"
        html += "</table>"
        
        html += f"""
            <h3 style="font-size: 12pt; margin: 10px 0;">定量項目</h3>
            <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 12pt; border: 1px solid #000; border-collapse: collapse; margin-bottom: 10px;">
                <tr style="background-color: #f0f0f0;">
                    <th style="border: 1px solid #000;">項目</th>
                    <th style="border: 1px solid #000;">N</th>
                    <th style="border: 1px solid #000;">Target Mean</th>
                    <th style="border: 1px solid #000;">Actual Mean</th>
                    <th style="border: 1px solid #000;">Target SD</th>
                    <th style="border: 1px solid #000;">Actual SD</th>
                    <th style="border: 1px solid #000;">設定 Mean</th>
                    <th style="border: 1px solid #000;">設定 SD</th>
                </tr>
        """
        t_quant = self.tabs.widget(1).findChild(QTableWidget)
        if t_quant:
            for r in range(t_quant.rowCount()):
                html += "<tr>"
                for c in range(8):
                    item = t_quant.item(r, c)
                    text = item.text() if item else ""
                    html += f"<td style='border: 1px solid #000; text-align: center;'>{text}</td>"
                html += "</tr>"
        html += "</table>"
        
        html += f"""
            <table width="100%" border="0" cellpadding="0" cellspacing="0" style="font-size: 12pt; margin-top: 15px;">
                <tr>
                    <td width="50%"></td>
                    <td width="50%" style="text-align: right;">組長簽章：______________________</td>
                </tr>
            </table>
        </div>
        """
        return html

class QCHistoryDialog(QDialog):
    def __init__(self, parent, iqi_id: int, reagent_name: str, level_name: str, lot_number: str):
        super().__init__(parent)
        self.iqi_id = iqi_id
        self.setWindowTitle(f"設定歷史紀錄 — {reagent_name} ({level_name} 批號 {lot_number})")
        self.setMinimumSize(800, 500)
        self.setStyleSheet(PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        top = QHBoxLayout()
        title = QLabel("🕒 品管範圍異動紀錄")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['primary']};")
        top.addWidget(title)
        top.addStretch()
        
        self.btn_export = QPushButton("💾 匯出 PDF")
        self.btn_export.clicked.connect(self._export_pdf)
        top.addWidget(self.btn_export)
        layout.addLayout(top)
        
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["有效日期", "設定時間", "設定人員", "變更數值", "TEa%", "變更原因"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)
        
        self._load_data()
        
    def _load_data(self):
        from services.qc_service import TargetSettingService
        records = TargetSettingService.get_history(self.iqi_id)
        self.records = records
        self.table.setRowCount(len(records))
        for r, rec in enumerate(records):
            eff_date = rec['effective_from'].strftime('%Y-%m-%d') if rec['effective_from'] else ""
            set_at = rec['set_at'].strftime('%Y-%m-%d %H:%M') if rec['set_at'] else ""
            
            if rec['tm'] is not None and rec['tsd'] is not None:
                val_str = f"TM: {rec['tm']}, TSD: {rec['tsd']}"
            elif rec['semi_target_min'] or rec['semi_target_max']:
                val_str = f"{rec['semi_target_min']} ~ {rec['semi_target_max']}"
            else:
                val_str = "未設定"
                
            tea_str = str(rec['tea_percent']) if rec['tea_percent'] is not None else ""
            reason = rec.get('change_reason') or ""
            
            self.table.setItem(r, 0, QTableWidgetItem(eff_date))
            self.table.setItem(r, 1, QTableWidgetItem(set_at))
            self.table.setItem(r, 2, QTableWidgetItem(rec['set_by_name']))
            self.table.setItem(r, 3, QTableWidgetItem(val_str))
            self.table.setItem(r, 4, QTableWidgetItem(tea_str))
            self.table.setItem(r, 5, QTableWidgetItem(reason))
            
        self.table.resizeColumnsToContents()

    def _export_pdf(self):
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtGui import QTextDocument
        from PyQt6.QtPrintSupport import QPrinter
        path, _ = QFileDialog.getSaveFileName(self, "匯出歷史紀錄", "qc_history.pdf", "PDF Files (*.pdf)")
        if not path:
            return
            
        html = self._get_print_html()
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        doc.print(printer)
        QMessageBox.information(self, "完成", "歷史紀錄已匯出至 PDF")

    def _get_print_html(self):
        html = f"""
        <div style="font-family: sans-serif; color: #000;">
            <h1 style="font-size: 16pt; text-align: center;">品管範圍異動紀錄</h1>
            <table width="100%" cellpadding="6" cellspacing="0" style="font-size: 12pt; border: 1px solid #000; border-collapse: collapse;">
                <tr>
                    <th style="border: 1px solid #000;">有效日期</th>
                    <th style="border: 1px solid #000;">設定時間</th>
                    <th style="border: 1px solid #000;">設定人員</th>
                    <th style="border: 1px solid #000;">變更數值</th>
                    <th style="border: 1px solid #000;">變更原因</th>
                </tr>
        """
        for r in range(self.table.rowCount()):
            html += "<tr>"
            for c in [0, 1, 2, 3, 5]:
                item = self.table.item(r, c)
                text = item.text() if item else ""
                html += f"<td style='border: 1px solid #000; text-align: center;'>{text}</td>"
            html += "</tr>"
        html += "</table></div>"
        return html


class TargetSettingDialog(QDialog):
    """設定品管範圍"""
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
                    ts = TargetSettingService.get_for_batch(iqi["iqi_id"], self.batch["batch_id"])
                    if ts:
                        self._existing[iqi["reagent_id"]] = ts
        
        row = 1
        for r in reagents:
            disp_name = r['reagent_name']
            g.addWidget(QLabel(disp_name), row, 0)
            
            widgets = {}
            if r["param_type"] in (2, 3): # Semi or Numeric Semi
                c_min = QComboBox()
                c_max = QComboBox()
                if r["param_type"] == 2:
                    c_min.addItems(SEMI_OPTIONS)
                    c_max.addItems(SEMI_OPTIONS)
                else:
                    opts = [str(x/2) for x in range(9, 18)]
                    c_min.addItems(opts)
                    c_max.addItems(opts)
                
                if r["reagent_id"] in self._existing:
                    ts = self._existing[r["reagent_id"]]
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
                
                def update_range(*args, tm_w=inp_tm, tsd_w=inp_tsd, lbl=lbl_range, dec=dec):
                    try:
                        tm = float(tm_w.text())
                        tsd = float(tsd_w.text())
                        lbl.setText(f"{tm - 2*tsd:.{dec}f} ~ {tm + 2*tsd:.{dec}f}")
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

    def _show_history(self, iqi_id, reagent_name):
        dlg = QCHistoryDialog(self, iqi_id, reagent_name, self.batch["level_name"], self.batch["lot_number"])
        dlg.exec()

    def _save(self):
        saved = 0
        today = date.today()
        
        # Combine reason
        combo_text = self.reason_combo.currentText()
        input_text = self.reason_input.text().strip()
        
        if combo_text and input_text:
            final_reason = f"{combo_text} - {input_text}"
        elif combo_text:
            final_reason = combo_text
        else:
            final_reason = input_text
            
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
                
                # Check for changes
                is_changed = False
                if reagent_id in self._existing:
                    old_ts = self._existing[reagent_id]
                    if old_ts.get("semi_target_min") != s_min or old_ts.get("semi_target_max") != s_max:
                        is_changed = True
                
                if is_changed and not final_reason:
                    QMessageBox.warning(self, "錯誤", f"偵測到設定值被修改，請填寫變更原因！")
                    return
                
                for iqi_id in iqis:
                    TargetSettingService.save_semi_target(
                        iqi_id, self.batch["batch_id"], s_min, s_max,
                        mode=2, effective_from=today, set_by=self.user["user_id"], change_reason=final_reason
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
                    
                    is_changed = False
                    if reagent_id in self._existing:
                        old_ts = self._existing[reagent_id]
                        if str(old_ts.get("tm")) != tm_txt or str(old_ts.get("tsd")) != tsd_txt or str(old_ts.get("tea_percent") or "") != tea_txt:
                            is_changed = True
                            
                    if is_changed and not final_reason:
                        QMessageBox.warning(self, "錯誤", f"偵測到設定值被修改，請填寫變更原因！")
                        return
                    
                    for iqi_id in iqis:
                        TargetSettingService.save(
                            iqi_id, self.batch["batch_id"], tm, tsd, None, tea,
                            mode=2, effective_from=today, set_by=self.user["user_id"], change_reason=final_reason
                        )
                    saved += 1
                except ValueError:
                    pass
                    
        QMessageBox.information(self, "完成", f"已儲存 {saved} 項範圍設定。")
        self.accept()

