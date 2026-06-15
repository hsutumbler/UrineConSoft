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

        
        self.btn_delete = QPushButton("🗑️ 刪除批號")
        self.btn_delete.setEnabled(False)
        self.btn_delete.setStyleSheet("color: #E74C3C;")
        self.btn_delete.clicked.connect(self._delete_batch)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(self.btn_target)
        toolbar.addWidget(self.btn_accept)
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
        row = self.table.currentRow()
        has = row >= 0
        if not has:
            self.btn_accept.setEnabled(False)
            self.btn_target.setEnabled(False)
            self.btn_delete.setEnabled(False)
            return

        b = self._get_selected()
        is_archived = b.get("is_archived", False) if b else False

        self.btn_target.setEnabled(True)
        self.btn_delete.setEnabled(not is_archived)
        self.btn_accept.setEnabled(not is_archived)

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
        # For mother lots, use created_at or open_date as the end date.
        accepted_at = None
        if b.get("created_at"):
            accepted_at = b["created_at"].date() if hasattr(b["created_at"], "date") else b["created_at"]
        elif b.get("open_date"):
            accepted_at = b["open_date"].date() if hasattr(b["open_date"], "date") else b["open_date"]
            
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
        is_sed_lot = batch.get("lot_number", "").upper().startswith("D")
        self.setMinimumSize(950, 420 if is_sed_lot else 750)
        self.resize(950, 420 if is_sed_lot else 750)
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

        sub_lots = batch.get("sub_lots", [])
        if not sub_lots:
            empty_lbl = QLabel("查無品管液允收資料或未設定子批號")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #888; font-size: 14px; margin: 20px;")
            self.tabs.addTab(empty_lbl, "無資料")

        for sub in sub_lots:
            level_id = sub["level_id"]
            lvl_name = sub["level_name"]
            
            tab_widget = QWidget()
            tab_layout = QVBoxLayout(tab_widget)
            
            t_qual = QTableWidget()
            t_qual.setColumnCount(7)
            t_qual.setHorizontalHeaderLabels(["項目", "N", "正常數", "異常數", "合格率", "允收目標", "評估結果"])
            t_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_qual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            
            t_qual.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            t_qual.setMinimumHeight(380)
            t_qual.setMaximumHeight(380)
            
            if not is_sed_lot:
                tab_layout.addWidget(t_qual, 4)
            
            t_quant = QTableWidget()
            t_quant.setColumnCount(9)
            t_quant.setHorizontalHeaderLabels(["項目", "N", "TM", "TSD", "AM", "ASD", "CV%", "設定Mean", "設定SD"])
            t_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            t_quant.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers if not read_only else QTableWidget.EditTrigger.NoEditTriggers)
            
            from PyQt6.QtWidgets import QStyledItemDelegate, QDoubleSpinBox
            class QuantDelegate(QStyledItemDelegate):
                def createEditor(self, parent, option, index):
                    if index.column() in (7, 8):
                        sp = QDoubleSpinBox(parent)
                        sp.setRange(-9999, 9999)
                        sp.setDecimals(2)
                        sp.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
                        return sp
                    return super().createEditor(parent, option, index)

                def setModelData(self, editor, model, index):
                    if isinstance(editor, QDoubleSpinBox):
                        model.setData(index, f"{editor.value():.2f}", Qt.ItemDataRole.EditRole)
                    else:
                        super().setModelData(editor, model, index)

            t_quant.setItemDelegate(QuantDelegate(self))
            
            t_quant.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            t_quant.verticalHeader().setDefaultSectionSize(40)
            t_quant.setMinimumHeight(140)
            t_quant.setMaximumHeight(140)
            
            lbl_quant = QLabel("定量項目：")
            lbl_quant.setStyleSheet("font-weight: bold; margin-top: 10px;")
            tab_layout.addWidget(lbl_quant)
            tab_layout.addWidget(t_quant)
            
            if is_sed_lot:
                tab_layout.addStretch()
            
            self.tabs.addTab(tab_widget, f"{lvl_name} ({sub['batch_id']})")
            self.tab_widgets[level_id] = {"qual": t_qual, "quant": t_quant, "sub": sub}

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("關閉" if read_only else "取消")
        btn_cancel.clicked.connect(self.reject)
        
        if read_only:
            btn_print = QPushButton("🖨️ 列印")
            btn_print.setObjectName("btn_primary")
            btn_print.clicked.connect(self._print_report)
            btn_row.addStretch()
            btn_row.addWidget(btn_print)
            btn_row.addWidget(btn_cancel)
        else:
            btn_accept = QPushButton("允收")
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
                n = data["n"]
                passed = data["passed"]
                failed = data["failed"]
                pass_rate = (passed / n * 100) if n > 0 else 0.0
                eval_res = "合格" if pass_rate >= 95 else "不合格"
                
                items = [
                    (0, QTableWidgetItem(rname)),
                    (1, QTableWidgetItem(str(n))),
                    (2, QTableWidgetItem(str(passed))),
                    (3, QTableWidgetItem(str(failed))),
                    (4, QTableWidgetItem(f"{pass_rate:.1f}%")),
                    (5, QTableWidgetItem("95%")),
                    (6, QTableWidgetItem(eval_res))
                ]
                
                for col, itm in items:
                    itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    t_qual.setItem(r, col, itm)
                
            t_quant.setRowCount(0)
            for rname, data in stats["quant"].items():
                r = t_quant.rowCount()
                t_quant.insertRow(r)
                
                n = data.get("n", 0)
                am = data["am"]
                asd = data["asd"]
                tm = data.get("tm")
                tsd = data.get("tsd")
                cv = (asd / am * 100) if am and asd is not None else 0
                
                n_str = str(n)
                tm_str = f"{tm:.2f}" if tm is not None else "-"
                tsd_str = f"{tsd:.2f}" if tsd is not None else "-"
                am_str = f"{am:.2f}" if am is not None else "-"
                asd_str = f"{asd:.2f}" if asd is not None else "-"
                cv_str = f"{cv:.1f}%" if am is not None else "-"
                
                item_rname = QTableWidgetItem(rname)
                item_rname.setData(Qt.ItemDataRole.UserRole, data.get("reagent_id"))
                items = [
                    (0, item_rname),
                    (1, QTableWidgetItem(n_str)),
                    (2, QTableWidgetItem(tm_str)),
                    (3, QTableWidgetItem(tsd_str)),
                    (4, QTableWidgetItem(am_str)),
                    (5, QTableWidgetItem(asd_str)),
                    (6, QTableWidgetItem(cv_str))
                ]
                for col, itm in items:
                    itm.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    itm.setFlags(itm.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    t_quant.setItem(r, col, itm)
                
                from PyQt6.QtGui import QColor, QBrush
                it_mean = QTableWidgetItem(f"{am:.2f}" if am is not None else "")
                it_mean.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                it_sd = QTableWidgetItem(f"{tsd:.2f}" if tsd is not None else "")
                it_sd.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if not self.read_only:
                    it_mean.setBackground(QBrush(QColor("#E3F2FD")))
                    it_mean.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                    it_sd.setBackground(QBrush(QColor("#E3F2FD")))
                    it_sd.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                else:
                    it_mean.setFlags(it_mean.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    it_sd.setFlags(it_sd.flags() & ~Qt.ItemFlag.ItemIsEditable)

                t_quant.setItem(r, 7, it_mean)
                t_quant.setItem(r, 8, it_sd)

    def _save(self, status: int):
        from services.qc_service import QCBatchService, TargetSettingService
        from datetime import date
        
        # Save Target Settings for each quantitative row
        for level_id, widgets in self.tab_widgets.items():
            sub = widgets["sub"]
            batch_id = sub["batch_id"]
            t_quant = widgets["quant"]
            
            for r in range(t_quant.rowCount()):
                item_rname = t_quant.item(r, 0)
                if not item_rname: continue
                reagent_id = item_rname.data(Qt.ItemDataRole.UserRole)
                if not reagent_id: continue
                
                it_mean = t_quant.item(r, 7)
                it_sd = t_quant.item(r, 8)
                
                if it_mean and it_sd:
                    try:
                        tm_val = float(it_mean.text())
                        tsd_val = float(it_sd.text())
                    except ValueError:
                        continue
                        
                    iqi_id = f"{reagent_id}_{level_id}"
                    
                    TargetSettingService.save(
                        iqi_id=iqi_id, 
                        qc_batch_id=batch_id, 
                        tm=tm_val, 
                        tsd=tsd_val,
                        cva=0.0,
                        tea=0.0,
                        mode=0,
                        effective_from=date.today(),
                        set_by=self.user["user_id"],
                        change_reason="允收後設定"
                    )
        if status == 1:
            QCBatchService.activate_and_retire_old(self.batch["lot_number"], "允收通過")
            QMessageBox.information(self, "完成", "允收紀錄與新的品管目標已儲存，且已自動切換為使用中。")
        else:
            QMessageBox.information(self, "完成", "允收拒絕紀錄已儲存。")
            
        self.accept()

    def _print_report(self):
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from PyQt6.QtGui import QTextDocument, QPageLayout
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QMarginsF, QSizeF
        
        if not self.tab_widgets:
            QMessageBox.warning(self, "無資料", "目前沒有資料可以列印。")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"{self.batch.get('lot_number', 'QC')}_品管允收.pdf", "PDF (*.pdf)")
        if not path: return
        
        acc_time = self.batch.get("accepted_at") or self.batch.get("created_at") or self.batch.get("open_date") or ""
        if hasattr(acc_time, 'strftime'):
            acc_time_str = acc_time.strftime("%Y/%m/%d %H:%M")
        else:
            acc_time_str = str(acc_time)[:16] if acc_time else "無紀錄"
            
        expiry = self.batch.get("expiry_date", "")
        if hasattr(expiry, 'strftime'):
            expiry_str = expiry.strftime("%Y/%m/%d")
        else:
            expiry_str = str(expiry) if expiry else "未設定"
            
        lot = self.batch.get("lot_number", "")
        
        sub_lots = self.batch.get("sub_lots", [])
        levels = "/".join(str(s.get("level_id", "")) for s in sub_lots)
        level_text = f"Level:{levels}" if levels else ""
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; font-size: 12px; }}
                h1 {{ font-size: 16pt; margin-bottom: 20px; text-align: center; }}
                .info {{ font-size: 12pt; margin-bottom: 10px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }}
                th {{ border: 1px solid black; background-color: #eee; padding: 6px; text-align: center; font-size: 10pt; }}
                td {{ border: 1px solid black; padding: 4px; text-align: center; font-size: 10pt; }}
                h2 {{ font-size: 12pt; margin-top: 20px; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <h1>新批號品管液允收</h1>
            <div class='info'>允收時間：{acc_time_str}</div>
            <div class='info'>允收品管液批號：{lot}&nbsp;&nbsp;&nbsp;&nbsp;{level_text}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;穩定效期：{expiry_str}</div>
        """
        
        qual_items = []
        qual_data = {}
        quant_items = []
        quant_data = {}
        levels_ordered = []
        
        for level_id, widgets in self.tab_widgets.items():
            sub = widgets["sub"]
            lvl_name = f"{sub['level_name'].replace(' ', '')}({sub.get('batch_id', '')})"
            levels_ordered.append((level_id, lvl_name, sub.get('batch_id', '')))
            
            t_qual = widgets.get("qual")
            if t_qual:
                for r in range(t_qual.rowCount()):
                    item_name = t_qual.item(r, 0).text() if t_qual.item(r, 0) else ""
                    if not item_name: continue
                    if item_name not in qual_data:
                        qual_items.append(item_name)
                        qual_data[item_name] = {}
                    qual_data[item_name][level_id] = [
                        t_qual.item(r, c).text() if t_qual.item(r, c) else ""
                        for c in range(1, 7)
                    ]
                    
            t_quant = widgets.get("quant")
            if t_quant:
                for r in range(t_quant.rowCount()):
                    item_name = t_quant.item(r, 0).text() if t_quant.item(r, 0) else ""
                    if not item_name: continue
                    if item_name not in quant_data:
                        quant_items.append(item_name)
                        quant_data[item_name] = {}
                    quant_data[item_name][level_id] = [
                        t_quant.item(r, c).text() if t_quant.item(r, c) else ""
                        for c in range(1, 9)
                    ]
                    
        if qual_items:
            html += "<table><thead>"
            html += "<tr><th rowspan='2'>項目</th>"
            for lvl_id, lvl_name, _ in levels_ordered:
                html += f"<th colspan='6'>{lvl_name}</th>"
            html += "</tr><tr>"
            for _ in levels_ordered:
                html += "<th>N</th><th>正常數</th><th>異常數</th><th>合格率</th><th>允收目標</th><th>評估結果</th>"
            html += "</tr></thead><tbody>"
            
            for item in qual_items:
                html += f"<tr><td>{item}</td>"
                for lvl_id, _, _ in levels_ordered:
                    vals = qual_data[item].get(lvl_id, [""] * 6)
                    for v in vals:
                        html += f"<td>{v}</td>"
                html += "</tr>"
            html += "</tbody></table><br>"
            
        if quant_items:
            for item in quant_items:
                html += f"<h2>{item}</h2>"
                html += "<table><thead><tr>"
                html += "<th>Assay</th><th>Lot</th><th>N</th><th>TM</th><th>TSD</th><th>AM</th><th>ASD</th><th>CV</th><th>設定 Mean</th><th>設定 SD</th>"
                html += "</tr></thead><tbody>"
                for lvl_id, lvl_name, batch_id in levels_ordered:
                    if lvl_id in quant_data[item]:
                        vals = quant_data[item][lvl_id]
                        assay_name = lvl_name.split('(')[0].strip()
                        html += "<tr>"
                        html += f"<td>{assay_name}</td><td>{batch_id}</td>"
                        for v in vals:
                            html += f"<td>{v}</td>"
                        html += "</tr>"
                html += "</tbody></table><br>"
                
        html += """
        </body>
        </html>
        """
        
        doc = QTextDocument()
        doc.setHtml(html)
        doc.setDocumentMargin(0)
        
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageMargins(QMarginsF(8, 10, 8, 10), QPageLayout.Unit.Millimeter)
        
        rect = printer.pageRect(QPrinter.Unit.Point)
        doc.setPageSize(QSizeF(rect.width(), rect.height()))
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功匯出至：\n{path}")

class TargetSettingDialog(QDialog):
    """設定品管範圍 (母子批號雙濃度)"""
    def __init__(self, parent, batch: dict, user: dict):
        super().__init__(parent)
        self.batch = batch
        self.user = user
        self.is_archived = batch.get("is_archived", False)
        self.setWindowTitle(f"設定品管範圍 — 商品套組 {batch['lot_number']}")
        self.setMinimumSize(750, 650)
        self.setStyleSheet(PAGE_STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        top_row = QHBoxLayout()
        title_suffix = " (唯讀：已退役批號無法修改)" if self.is_archived else ""
        info = QLabel(f"設定商品套組 {batch['lot_number']} 的品管範圍{title_suffix}")
        info.setStyleSheet("font-size:14px; color:#A48753; font-weight:bold;")
        top_row.addWidget(info)
        
        btn_load_active = QPushButton("📥 載入品管範圍")
        btn_load_active.setToolTip("將目前使用中批號的範圍載入至下方")
        btn_load_active.clicked.connect(self._load_active_targets)
        top_row.addStretch()
        top_row.addWidget(btn_load_active)
        
        if self.is_archived:
            btn_load_active.setVisible(False)
            
        layout.addLayout(top_row)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabWidget::pane { border: 1px solid #E0E0E0; background: #FFF; border-radius: 4px; }")
        layout.addWidget(self.tabs)

        self._inputs = {}
        
        from services.qc_service import MasterService, TargetSettingService
        reagents = MasterService.get_reagents()
        
        # Build a tab for each sub_lot
        sub_lots = batch.get("sub_lots", [])
        if not sub_lots:
            empty_lbl = QLabel("查無品管液資料或未設定子批號")
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #888; font-size: 14px; margin: 20px;")
            self.tabs.addTab(empty_lbl, "無資料")

        for sub in sub_lots:
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
                        
                    if self.is_archived:
                        c_min.setEnabled(False)
                        c_max.setEnabled(False)
                        
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
                        
                    if self.is_archived:
                        inp_tm.setReadOnly(True)
                        inp_tsd.setReadOnly(True)
                        inp_tea.setReadOnly(True)
                        
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
        btn_cancel = QPushButton("關閉" if self.is_archived else "取消")
        btn_cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)
        
        if self.is_archived:
            reason_container.setVisible(False)
            btn_save.setVisible(False)

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

