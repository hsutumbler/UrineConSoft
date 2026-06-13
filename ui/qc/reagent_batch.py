# ui/qc/reagent_batch.py — 試劑批號管理（LabStrip）+ 允收

from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialog, QFormLayout, QComboBox,
    QDateEdit, QTextEdit, QTableWidgetItem, QFrame,
    QTabWidget, QWidget, QMessageBox, QScrollArea,
    QGroupBox, QGridLayout, QDoubleSpinBox,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QFont
from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import (
    ReagentBatchService, MasterService, calc_stats
)
import json


SEMI_OPTIONS = ["Neg", "Trace", "1+", "2+", "3+"]


class ReagentBatchPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("試劑批號管理", "LabStrip 批號管理與允收", user)
        self._build()

    def _build(self):
        # 工具列
        toolbar = QHBoxLayout()
        btn_add = QPushButton("＋ 新增批號")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_batch)

        self.btn_accept = QPushButton("📋 執行允收")
        self.btn_accept.setEnabled(False)
        self.btn_accept.clicked.connect(self._run_acceptance)

        self.btn_activate = QPushButton("✅ 設為使用中")
        self.btn_activate.setEnabled(False)
        self.btn_activate.clicked.connect(self._activate_selected)

        self.btn_delete = QPushButton("🗑️ 刪除批號")
        self.btn_delete.setStyleSheet("color: #D32F2F;")
        self.btn_delete.setEnabled(False)
        self.btn_delete.clicked.connect(self._delete_batch)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(self.btn_accept)
        toolbar.addWidget(self.btn_activate)
        toolbar.addWidget(self.btn_delete)
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

        # 目前使用中顯示
        self.lbl_active = QLabel("目前使用中批號：未設定")
        self.lbl_active.setStyleSheet(
            f"font-size:14px; font-weight:600; color:{COLORS['accent']}; padding:8px;"
        )
        self.content_layout.addWidget(self.lbl_active)

        # 批號列表
        self.table = self.make_table(
            ["批號", "穩定效期", "開封日", "狀態", "建立時間", "建立人"]
        )
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.cellDoubleClicked.connect(lambda r, c: self._view_acceptance(r))
        self.content_layout.addWidget(self.table)

        hint = QLabel("💡 雙擊批號可查看允收記錄")
        hint.setStyleSheet(f"color:{COLORS['text_muted']}; font-size:12px;")
        self.content_layout.addWidget(hint)

        self._load()

    def _load(self):
        batches = ReagentBatchService.get_all()
        active = ReagentBatchService.get_active()
        if active:
            self.lbl_active.setText(
                f"目前使用中批號：{active['lot_number']}   "
                f"（穩定效期：{active['expiry_date'] or '—'}）"
            )
        else:
            self.lbl_active.setText("目前使用中批號：未設定")

        self.table.setRowCount(0)
        archived_count = 0
        display_batches = []
        for b in batches:
            if b.get("is_archived"):
                if archived_count < 2:
                    display_batches.append(b)
                    archived_count += 1
            else:
                display_batches.append(b)

        for r, b in enumerate(display_batches):
            self.table.insertRow(r)
            if b.get("is_archived"):
                status = "📦 已退役"
            elif b["is_active"]:
                status = "✅ 使用中"
            else:
                status = "⏳ 待允收"
            vals = [
                b["lot_number"],
                str(b["expiry_date"] or ""),
                str(b["open_date"] or ""),
                status,
                str(b["created_at"])[:16],
                b["created_by_name"],
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, b)
                self.table.setItem(r, c, item)

        self._on_selection()

    def _on_selection(self):
        row = self.table.currentRow()
        has = row >= 0
        self.btn_activate.setEnabled(has)
        self.btn_accept.setEnabled(has)
        
        can_delete = False
        if has:
            b = self._get_selected()
            if b and not b.get("is_active") and not b.get("is_archived"):
                can_delete = True
        self.btn_delete.setEnabled(can_delete)

    def _get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _add_batch(self):
        dlg = BatchDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            batch_id = ReagentBatchService.create(
                d["lot_number"], d["expiry_date"], d["open_date"],
                d["notes"], self.user["user_id"]
            )
            self._load()

    def _activate_selected(self):
        b = self._get_selected()
        if not b:
            return
        if not self.confirm("確認", f"將批號 {b['lot_number']} 設為目前使用中？", default_yes=True):
            return
        ReagentBatchService.set_active(b["batch_id"])
        self._load()

    def _delete_batch(self):
        b = self._get_selected()
        if not b: return
        if self.confirm("警告", f"確定要刪除待允收批號 {b['lot_number']} 嗎？此操作無法還原。"):
            ReagentBatchService.delete(b["batch_id"])
            self._load()

    def _run_acceptance(self):
        b = self._get_selected()
        if not b:
            return
        dlg = AcceptanceDialog(self, b, self.user)
        dlg.exec()
        self._load()

    def _view_acceptance(self, row: int):
        item = self.table.item(row, 0)
        if not item:
            return
        b = item.data(Qt.ItemDataRole.UserRole)
        if not b:
            return
        records = ReagentBatchService.get_acceptance_records(b["batch_id"])
        dlg = AcceptanceViewDialog(self, b, records)
        dlg.exec()

    def on_page_show(self):
        self._load()


class BatchDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("新增試劑批號")
        self.setFixedWidth(400)
        self.setStyleSheet(PAGE_STYLE)
        form = QFormLayout(self)
        form.setSpacing(14)
        form.setContentsMargins(24, 24, 24, 24)

        self.f_lot = QLineEdit()
        self.f_lot.setPlaceholderText("輸入批號")
        self.f_exp = QDateEdit()
        self.f_exp.setCalendarPopup(True)
        self.f_exp.setDate(QDate.currentDate().addMonths(6))
        self.f_open = QDateEdit()
        self.f_open.setCalendarPopup(True)
        self.f_open.setDate(QDate.currentDate())
        self.f_notes = QTextEdit()
        self.f_notes.setFixedHeight(70)
        self.f_notes.setPlaceholderText("備註（選填）")

        form.addRow("批號 *",   self.f_lot)
        form.addRow("穩定效期",     self.f_exp)
        form.addRow("開封日",   self.f_open)
        form.addRow("備註",     self.f_notes)

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
            "lot_number":   self.f_lot.text().strip(),
            "expiry_date":  self.f_exp.date().toPyDate(),
            "open_date":    self.f_open.date().toPyDate(),
            "notes":        self.f_notes.toPlainText().strip(),
        }


class AcceptanceDialog(QDialog):
    """試劑批次允收對話框 — 智慧比對視窗"""

    def __init__(self, parent, batch: dict, user: dict, read_only: bool = False, snapshot_data: dict = None):
        super().__init__(parent)
        self.batch = batch
        self.user  = user
        self.read_only = read_only
        self._snapshot_data = snapshot_data or {"active_lot": "無", "rows": []}
        
        mode_str = "歷史允收" if read_only else "新進批號"
        self.setWindowTitle(f"試劑允收 — {mode_str} {batch['lot_number']}")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(PAGE_STYLE)

        # 取得現有使用中的批號
        if not self.read_only:
            self.active_batch = ReagentBatchService.get_active()
            self.active_times = ReagentBatchService.get_recent_qc_timepoints(self.active_batch['batch_id']) if self.active_batch else []
            self.new_times = ReagentBatchService.get_recent_qc_timepoints(self.batch['batch_id'])
        else:
            self.active_batch = None
            self.active_times = []
            self.new_times = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 上方控制區
        ctrl_layout = QHBoxLayout()
        
        # 現有批號
        active_grp = QGroupBox("現有批號 (Active Batch)")
        active_grp.setStyleSheet("font-weight: bold;")
        al = QVBoxLayout(active_grp)
        
        active_lot_txt = (self._snapshot_data.get("active_batch") or self._snapshot_data.get("active_lot", "無")) if self.read_only else (self.active_batch['lot_number'] if self.active_batch else '無')
        al.addWidget(QLabel(f"批號: {active_lot_txt}"))
        
        ctrl_layout.addWidget(active_grp)
        
        self.cmb_active = QComboBox()
        if self.read_only:
            t_str = self._snapshot_data.get("active_time")
            if t_str:
                self.cmb_active.addItem(t_str.replace("T", " ")[:16], t_str)
        else:
            for t in self.active_times:
                self.cmb_active.addItem(t.strftime("%Y-%m-%d %H:%M"), t)
                
        if self.cmb_active.count() == 0:
            self.cmb_active.addItem("無品管數據", None)
            self.cmb_active.setEnabled(False)
        else:
            if not self.read_only and self.cmb_active.count() > 1:
                self.cmb_active.setCurrentIndex(1)
            self.cmb_active.currentIndexChanged.connect(self._update_table)
        
        time_row1 = QHBoxLayout()
        time_row1.addWidget(QLabel("品管時間點:"))
        time_row1.addWidget(self.cmb_active)
        al.addLayout(time_row1)

        # 新進批號
        new_grp = QGroupBox("新進批號 (New Batch)")
        new_grp.setStyleSheet("font-weight: bold; color: #0056b3;")
        nl = QVBoxLayout(new_grp)
        nl.addWidget(QLabel(f"批號: {self.batch['lot_number']}"))
        
        self.cmb_new = QComboBox()
        if self.read_only:
            t_str = self._snapshot_data.get("new_time")
            if t_str:
                self.cmb_new.addItem(t_str.replace("T", " ")[:16], t_str)
        else:
            for t in self.new_times:
                self.cmb_new.addItem(t.strftime("%Y-%m-%d %H:%M"), t)
                
        if self.cmb_new.count() == 0:
            self.cmb_new.addItem("無品管數據", None)
            self.cmb_new.setEnabled(False)
        else:
            self.cmb_new.currentIndexChanged.connect(self._update_table)
            
        time_row2 = QHBoxLayout()
        time_row2.addWidget(QLabel("品管時間點:"))
        time_row2.addWidget(self.cmb_new)
        nl.addLayout(time_row2)
        ctrl_layout.addWidget(new_grp)
        layout.addLayout(ctrl_layout)

        # 對比表格
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QStyledItemDelegate
        from PyQt6.QtCore import QTimer
        from PyQt6.QtGui import QColor, QFont
        
        class EnterDelegate(QStyledItemDelegate):
            def __init__(self, table):
                super().__init__(table)
                self.table = table

            def setModelData(self, editor, model, index):
                from PyQt6.QtWidgets import QLineEdit
                if isinstance(editor, QLineEdit):
                    text = editor.text().strip().upper()
                    shortcuts = {
                        "N": "Neg",
                        "T": "Trace",
                        "1": "1+",
                        "2": "2+",
                        "3": "3+",
                        "4": "4+",
                    }
                    if text in shortcuts:
                        editor.setText(shortcuts[text])
                    super().setModelData(editor, model, index)

            def eventFilter(self, editor, event):
                if event.type() == event.Type.KeyPress and event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                    self.commitData.emit(editor)
                    self.closeEditor.emit(editor, QStyledItemDelegate.EndEditHint.NoHint)
                    
                    idx = self.table.currentIndex()
                    row, col = idx.row(), idx.column()
                    
                    next_row, next_col = row, col
                    while True:
                        if next_col == 2:
                            next_col = 5
                        else:
                            next_row += 1
                            next_col = 2
                            
                        if next_row >= self.table.rowCount():
                            break
                            
                        item = self.table.item(next_row, next_col)
                        if item and (item.flags() & Qt.ItemFlag.ItemIsEditable):
                            def edit_next(r=next_row, c=next_col):
                                self.table.setCurrentCell(r, c)
                                self.table.editItem(self.table.item(r, c))
                            QTimer.singleShot(0, edit_next)
                            break
                    return True
                return super().eventFilter(editor, event)
        
        self.table = QTableWidget()
        self.table.setItemDelegate(EnterDelegate(self.table))
        
        headers = [
            "項目",
            "Active L1", "New L1", "差值(Difference)",
            "Active L2", "New L2", "差值(Difference)"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setVisible(False)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Status / Summary
        if self.read_only:
            acc_by = self.batch.get("accepted_by_name", "Unknown")
            acc_at = self.batch.get("accepted_at", "Unknown")
            lbl_info = QLabel(f"歷史允收紀錄  |  執行人員：{acc_by}  |  時間：{acc_at}")
            lbl_info.setStyleSheet("color: #666; font-size: 14px; font-weight: bold;")
            layout.addWidget(lbl_info)
        
        # Bottom controls
        btn_layout = QHBoxLayout()
        btn_print = QPushButton("🖨️ 列印")
        btn_print.clicked.connect(self._print_pdf)
        
        if self.read_only:
            btn_print.setObjectName("btn_primary")
            btn_close = QPushButton("關閉")
            btn_close.clicked.connect(self.accept)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_close)
        else:
            btn_accept = QPushButton("允收")
            btn_accept.setObjectName("btn_primary")
            btn_cancel = QPushButton("取消")
            btn_reject = QPushButton("拒絕")
            btn_reject.setObjectName("btn_danger")
            
            btn_accept.clicked.connect(lambda: self._save_decision(1))
            btn_cancel.clicked.connect(self.reject)
            btn_reject.clicked.connect(lambda: self._save_decision(0))
            
            btn_layout.addWidget(btn_print)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_reject)
            btn_layout.addWidget(btn_cancel)
            btn_layout.addWidget(btn_accept)
            
            # Initial load
            self.table.itemChanged.connect(self._on_item_changed)
            self._update_table()
            
        layout.addLayout(btn_layout)
        
        if self.read_only:
            self.cmb_active.setEnabled(False)
            self.cmb_new.setEnabled(False)
            self._load_snapshot()

    def _build_table_headers(self):
        # 建立兩層式的 Header (Row 0 & Row 1)
        self.table.setRowCount(2)
        
        from PyQt6.QtGui import QColor, QFont
        h0_0 = QTableWidgetItem("項目")
        h0_0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_0.setBackground(QColor("#f0f0f0"))
        h0_0.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 0, h0_0)
        self.table.setSpan(0, 0, 2, 1)
        
        h0_1 = QTableWidgetItem("Level 1")
        h0_1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_1.setBackground(QColor("#f0f0f0"))
        h0_1.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 1, h0_1)
        self.table.setSpan(0, 1, 1, 3)
        
        h0_4 = QTableWidgetItem("Level 2")
        h0_4.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_4.setBackground(QColor("#f0f0f0"))
        h0_4.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 4, h0_4)
        self.table.setSpan(0, 4, 1, 3)
        
        sub_headers = ["現有", "新進", "差值", "現有", "新進", "差值"]
        for i, h in enumerate(sub_headers):
            it = QTableWidgetItem(h)
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(QColor("#f0f0f0"))
            it.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.table.setItem(1, i + 1, it)

    def _load_snapshot(self):
        self._build_table_headers()
        rows = self._snapshot_data.get("rows", [])
        
        def calc_diff(v1, v2, rname):
            if v1 == "—" or v2 == "—" or v1 is None or v2 is None:
                return "—"
            try:
                diff = float(v2) - float(v1)
                dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC", "pH") else 2)
                return f"{diff:.{dec}f}"
            except ValueError:
                s1, s2 = str(v1).strip().upper(), str(v2).strip().upper()
                if s1 == s2: return "一致"
                if "NEG" in (s1, s2): return "不同"
                semi_order = ["TRACE", "1+", "2+", "3+", "4+", "5+"]
                if s1 in semi_order and s2 in semi_order:
                    if abs(semi_order.index(s1) - semi_order.index(s2)) <= 1:
                        return "一致"
                return "不同"
                
        for r, vals in enumerate(rows):
            row_idx = r + 2
            self.table.insertRow(row_idx)
            
            if len(vals) >= 7:
                rname = vals[0]
                vals[3] = calc_diff(vals[1], vals[2], rname)
                vals[6] = calc_diff(vals[4], vals[5], rname)
                
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v) if v is not None else "—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row_idx, c, item)

    def _on_item_changed(self, item):
        if self.read_only: return
        col = item.column()
        row = item.row()
        if row < 2: return # Headers
        
        if col in (2, 5): # New L1 or New L2
            rname = self.table.item(row, 0).text()
            
            def calc_diff(v1, v2, rname):
                if not v1 or not v2 or v1 == "—" or v2 == "—":
                    return "—"
                try:
                    diff = float(v2) - float(v1)
                    dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC", "pH") else 2)
                    return f"{diff:.{dec}f}"
                except ValueError:
                    s1, s2 = str(v1).strip().upper(), str(v2).strip().upper()
                    if s1 == s2: return "一致"
                    if "NEG" in (s1, s2): return "不同"
                    semi_order = ["TRACE", "1+", "2+", "3+", "4+", "5+"]
                    if s1 in semi_order and s2 in semi_order:
                        if abs(semi_order.index(s1) - semi_order.index(s2)) <= 1:
                            return "一致"
                    return "不同"
            
            if col == 2:
                active_item = self.table.item(row, 1)
                diff_item = self.table.item(row, 3)
            else:
                active_item = self.table.item(row, 4)
                diff_item = self.table.item(row, 6)
                
            active_val = active_item.text() if active_item else "—"
            new_val = item.text()
            
            diff_str = calc_diff(active_val, new_val, rname)
            
            if diff_item:
                diff_item.setText(diff_str)
                from PyQt6.QtGui import QColor
                if diff_str == "不同":
                    diff_item.setForeground(QColor("#E74C3C"))
                else:
                    diff_item.setForeground(QColor("#000000"))

    def _update_table(self):
        if self.read_only:
            return
            
        active_time = self.cmb_active.currentData()
        new_time = self.cmb_new.currentData()
        
        active_data = {}
        if self.active_batch and active_time:
            active_data = ReagentBatchService.get_qc_results_by_time(self.active_batch['batch_id'], active_time)
            
        new_data = {}
        if new_time:
            new_data = ReagentBatchService.get_qc_results_by_time(self.batch['batch_id'], new_time)

        from services.qc_service import MasterService
        reagents = MasterService.get_reagents()
        self._build_table_headers()
        
        row_idx = 2
        
        self._snapshot_data = {
            "active_batch": self.active_batch['lot_number'] if self.active_batch else None,
            "active_time": active_time.isoformat() if active_time else None,
            "new_batch": self.batch['lot_number'],
            "new_time": new_time.isoformat() if new_time else None,
            "rows": []
        }
        
        for r, reagent in enumerate(reagents):
            rname = reagent["reagent_name"]
            
            a_row = active_data.get(rname, {})
            n_row = new_data.get(rname, {})
            
            def fmt_val(v):
                from decimal import Decimal
                if v == "—" or v is None: return "—"
                if isinstance(v, (int, float, Decimal)) or (isinstance(v, str) and v.replace('.','',1).replace('-','',1).isdigit()):
                    dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC", "pH") else 2)
                    return f"{float(v):.{dec}f}"
                return str(v)

            a_l1 = fmt_val(a_row.get("Level 1"))
            n_l1 = fmt_val(n_row.get("Level 1"))
            
            a_l2 = fmt_val(a_row.get("Level 2"))
            n_l2 = fmt_val(n_row.get("Level 2"))
            
            def calc_diff(v1, v2, rname):
                if v1 == "—" or v2 == "—" or v1 is None or v2 is None:
                    return "—"
                try:
                    diff = float(v2) - float(v1)
                    dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC", "pH") else 2)
                    return f"{diff:.{dec}f}"
                except ValueError:
                    s1, s2 = str(v1).strip().upper(), str(v2).strip().upper()
                    if s1 == s2: return "一致"
                    if "NEG" in (s1, s2): return "不同"
                    semi_order = ["TRACE", "1+", "2+", "3+", "4+", "5+"]
                    if s1 in semi_order and s2 in semi_order:
                        if abs(semi_order.index(s1) - semi_order.index(s2)) <= 1:
                            return "一致"
                    return "不同"
            
            d_l1 = calc_diff(a_l1, n_l1, rname)
            d_l2 = calc_diff(a_l2, n_l2, rname)
            
            self.table.insertRow(row_idx)
            
            vals = [
                reagent["reagent_name"],
                a_l1, n_l1, d_l1,
                a_l2, n_l2, d_l2
            ]
            
            self._snapshot_data["rows"].append(vals)
            
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v) if v is not None else "—")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                # Highlight if new differs from active
                if c == 2 and n_l1 != a_l1 and n_l1 is not None and a_l1 is not None:
                    item.setForeground(QColor("#0056b3"))
                if c == 5 and n_l2 != a_l2 and n_l2 is not None and a_l2 is not None:
                    item.setForeground(QColor("#0056b3"))
                    
                if c in (2, 5):
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
                    if v is None or v == "—":
                        item.setText("")
                        item.setBackground(QColor("#FFFFFF"))
                        # Optionally add a hint if empty
                        item.setToolTip("雙擊即可手動輸入數值")
                else:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                self.table.setItem(row_idx, c, item)
            self.table.blockSignals(False)
            row_idx += 1

    def _save_decision(self, status: int):
        status_map = {1: "允收", 2: "暫緩", 0: "拒絕"}
        st = status_map[status]
        
        # Read back table values into snapshot before saving
        for r in range(2, self.table.rowCount()):
            row_idx = r - 2
            if row_idx < len(self._snapshot_data["rows"]):
                self._snapshot_data["rows"][row_idx][2] = self.table.item(r, 2).text().strip()
                self._snapshot_data["rows"][row_idx][5] = self.table.item(r, 5).text().strip()
        
        if not self.confirm("確認決策", f"確定要將批號 {self.batch['lot_number']} 標記為「{st}」嗎？", default_yes=True):
            return
            
        ReagentBatchService.save_batch_acceptance(
            self.batch['batch_id'],
            status,
            self._snapshot_data,
            self.user['user_id']
        )
        
        QMessageBox.information(self, "完成", f"已成功儲存決策：{st}")
        
        # 如果是允收，自動設為使用中
        if status == 1:
            ReagentBatchService.set_active(self.batch['batch_id'])
                
        self.accept()

    def confirm(self, title, msg, default_yes=False):
        box = QMessageBox(self)
        box.setWindowTitle(title)
        box.setText(msg)
        box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        box.setDefaultButton(QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No)
        return box.exec() == QMessageBox.StandardButton.Yes
    def _print_pdf(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
        from PyQt6.QtCore import QMarginsF
        from PyQt6.QtWidgets import QFileDialog
        import datetime
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"允收記錄_{self.batch['lot_number']}.pdf", "PDF (*.pdf)")
        if not path: return
        
        # 處理舊批號與新批號
        if self.read_only:
            old_lot = self._snapshot_data.get("active_batch") or self._snapshot_data.get("active_lot", "無")
            old_exp = "—"
            from database.connection import DBContext
            with DBContext() as (_, cur):
                cur.execute("SELECT expiry_date FROM reagent_batches WHERE lot_number=%s", (old_lot,))
                r = cur.fetchone()
                if r and r["expiry_date"]:
                    old_exp = r["expiry_date"].strftime("%Y-%m-%d")
        else:
            old_lot = self.active_batch['lot_number'] if self.active_batch else "無"
            old_exp = self.active_batch['expiry_date'].strftime("%Y-%m-%d") if self.active_batch and self.active_batch['expiry_date'] else "—"
            
        new_lot = self.batch['lot_number']
        new_exp = self.batch['expiry_date'].strftime("%Y-%m-%d") if self.batch['expiry_date'] else "—"
        acc_time = self.batch.get('accepted_at', '未允收')
        acc_by = self.batch.get('accepted_by_name', '未設定')
        
        old_time = self._snapshot_data.get("active_time")
        old_time_str = old_time.replace("T", " ")[:16] if old_time else "無"
        
        new_time = self._snapshot_data.get("new_time")
        new_time_str = new_time.replace("T", " ")[:16] if new_time else "無"
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Arial', 'Microsoft JhengHei', sans-serif; padding: 0pt 20pt 10pt 20pt; color: #000; font-size: 12pt; }}
                h1 {{ text-align: center; color: #2C3E50; margin-top: 5pt; font-size: 16pt; margin-bottom: 5pt; }}
                .meta {{ font-size: 12pt; line-height: 1.2; margin-bottom: 10pt; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 5pt; font-size: 12pt; border: 1px solid black; }}
                th, td {{ border: 1px solid black; text-align: center; }}
                th {{ font-weight: normal; color: #000; }}
                .highlight {{ font-weight: bold; color: #E74C3C; }}
            </style>
        </head>
        <body>
            <h1>試劑允收紀錄</h1>
            <br/>
            
            <div class="meta">
                舊批號：{old_lot} &nbsp;&nbsp;&nbsp;&nbsp;穩定效期：{old_exp} &nbsp;&nbsp;&nbsp;&nbsp;品管時間：{old_time_str}<br/>
                新批號：{new_lot} &nbsp;&nbsp;&nbsp;&nbsp;穩定效期：{new_exp} &nbsp;&nbsp;&nbsp;&nbsp;品管時間：{new_time_str}<br/>
                允收時間：{acc_time} &nbsp;&nbsp;&nbsp;&nbsp; 執行人員：{acc_by}
            </div>
            
            <table width="100%" cellpadding="6" cellspacing="0" style="border-collapse: collapse;">
                <thead>
                    <tr>
                        <th rowspan="2" style="vertical-align: middle;">項目</th>
                        <th colspan="3">Level 1</th>
                        <th colspan="3">Level 2</th>
                    </tr>
                    <tr>
                        <th>現有</th><th>新進</th><th>差值</th>
                        <th>現有</th><th>新進</th><th>差值</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Populate table data (Skip first 2 rows which are headers)
        for r in range(2, self.table.rowCount()):
            bg_color = "#f4f4f4" if r % 2 == 0 else "#ffffff"
            html += f"<tr style='background-color: {bg_color};'>"
            for c in range(7):
                item = self.table.item(r, c)
                text = item.text() if item else ""
                if text == "—":
                    text = "" # Clean up display according to attachment
                if text == "不同":
                    text = f"<span class='highlight'>{text}</span>"
                html += f"<td>{text}</td>"
            html += "</tr>"
            
        html += """
                </tbody>
            </table>
            
            <br/>
            <div style="font-size: 14pt;">
                組長： &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 技術主任：
            </div>
        </body>
        </html>
        """
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        
        layout = QPageLayout()
        layout.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        layout.setOrientation(QPageLayout.Orientation.Portrait)
        layout.setMargins(QMarginsF(15, 15, 15, 15))
        printer.setPageLayout(layout)
        
        doc.print(printer)
        
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "匯出成功", f"PDF 已儲存至 {path}")

class AcceptanceViewDialog(QDialog):
    """查看允收紀錄"""
    def __init__(self, parent, batch: dict, records: list):
        super().__init__(parent)
        self.setWindowTitle(f"歷史允收記錄 — {batch['lot_number']}")
        self.setMinimumSize(500, 300)
        self.setStyleSheet(PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("此視窗供未來擴充查看詳細歷史紀錄用。\n（可從 reagent_batch_acceptance 抓取 snapshot_data 渲染表格）"))
        
