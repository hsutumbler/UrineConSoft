import re

with open("ui/qc/reagent_batch.py", "r") as f:
    content = f.read()

# We want to replace everything from class AcceptanceDialog to the end of the file.
start_idx = content.find("class AcceptanceDialog(QDialog):")
if start_idx != -1:
    content = content[:start_idx]
else:
    print("Could not find AcceptanceDialog")

new_code = """class AcceptanceDialog(QDialog):
    \"\"\"試劑批次允收對話框 — 智慧比對視窗\"\"\"

    def __init__(self, parent, batch: dict, user: dict):
        super().__init__(parent)
        self.batch = batch
        self.user  = user
        self.setWindowTitle(f"試劑允收 — 新進批號 {batch['lot_number']}")
        self.setMinimumSize(900, 700)
        self.setStyleSheet(PAGE_STYLE)

        # 取得現有使用中的批號
        self.active_batch = ReagentBatchService.get_active()
        
        # 取得時間點
        self.active_times = ReagentBatchService.get_recent_qc_timepoints(self.active_batch['batch_id']) if self.active_batch else []
        self.new_times = ReagentBatchService.get_recent_qc_timepoints(self.batch['batch_id'])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # 上方控制區
        ctrl_layout = QHBoxLayout()
        
        # 現有批號
        active_grp = QGroupBox("現有批號 (Active Batch)")
        active_grp.setStyleSheet("font-weight: bold;")
        al = QVBoxLayout(active_grp)
        al.addWidget(QLabel(f"批號: {self.active_batch['lot_number'] if self.active_batch else '無'}"))
        
        ctrl_layout.addWidget(active_grp)
        
        self.cmb_active = QComboBox()
        for t in self.active_times:
            self.cmb_active.addItem(t.strftime("%Y-%m-%d %H:%M"), t)
        if not self.active_times:
            self.cmb_active.addItem("無品管數據", None)
            self.cmb_active.setEnabled(False)
        else:
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
        for t in self.new_times:
            self.cmb_new.addItem(t.strftime("%Y-%m-%d %H:%M"), t)
        if not self.new_times:
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
        from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView
        from PyQt6.QtGui import QColor, QFont
        
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "項目", 
            "Level 1 現有", "Level 1 新進", "Level 1 範圍", 
            "Level 2 現有", "Level 2 新進", "Level 2 範圍"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget { font-size: 14px; } QHeaderView::section { font-weight: bold; }")
        
        layout.addWidget(self.table)

        # 下方按鈕
        btn_row = QHBoxLayout()
        
        btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
        btn_print.clicked.connect(self._print_pdf)
        
        btn_accept = QPushButton("✅ 允收試劑")
        btn_accept.setObjectName("btn_primary")
        btn_accept.clicked.connect(lambda: self._save_decision(1))
        
        btn_hold = QPushButton("⏸️ 暫緩允收")
        btn_hold.setStyleSheet(f"background-color: {COLORS['warning']}; color: white; border-radius: 4px; padding: 8px 16px;")
        btn_hold.clicked.connect(lambda: self._save_decision(2))
        
        btn_reject = QPushButton("❌ 拒絕試劑")
        btn_reject.setStyleSheet(f"background-color: {COLORS['danger']}; color: white; border-radius: 4px; padding: 8px 16px;")
        btn_reject.clicked.connect(lambda: self._save_decision(0))
        
        btn_row.addWidget(btn_print)
        btn_row.addStretch()
        btn_row.addWidget(btn_reject)
        btn_row.addWidget(btn_hold)
        btn_row.addWidget(btn_accept)
        
        layout.addLayout(btn_row)

        self._snapshot_data = {}
        self._update_table()

    def _update_table(self):
        active_time = self.cmb_active.currentData()
        new_time = self.cmb_new.currentData()
        
        active_data = {}
        if self.active_batch and active_time:
            active_data = ReagentBatchService.get_qc_results_by_time(self.active_batch['batch_id'], active_time)
            
        new_data = {}
        if new_time:
            new_data = ReagentBatchService.get_qc_results_by_time(self.batch['batch_id'], new_time)

        reagents = MasterService.get_reagents()
        self.table.setRowCount(0)
        
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
            
            # Form values
            a_l1 = a_row.get("Level 1", "—")
            n_l1 = n_row.get("Level 1", "—")
            t_l1 = n_row.get("Target 1") or a_row.get("Target 1") or "未設定"
            
            a_l2 = a_row.get("Level 2", "—")
            n_l2 = n_row.get("Level 2", "—")
            t_l2 = n_row.get("Target 2") or a_row.get("Target 2") or "未設定"
            
            self.table.insertRow(r)
            
            vals = [
                reagent["reagent_label"],
                a_l1, n_l1, t_l1,
                a_l2, n_l2, t_l2
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
                    
                self.table.setItem(r, c, item)

    def _save_decision(self, status: int):
        status_map = {1: "允收", 2: "暫緩", 0: "拒絕"}
        st = status_map[status]
        
        if not self.confirm("確認決策", f"確定要將批號 {self.batch['lot_number']} 標記為「{st}」嗎？", default_yes=True):
            return
            
        ReagentBatchService.save_batch_acceptance(
            self.batch['batch_id'],
            status,
            self._snapshot_data,
            self.user['user_id']
        )
        
        QMessageBox.information(self, "完成", f"已成功儲存決策：{st}")
        
        # 如果是允收，問要不要啟用
        if status == 1:
            if self.confirm("啟用批號", "是否立即將此允收批號設為目前使用中？", default_yes=True):
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
        from PyQt6.QtGui import QPainter, QPdfWriter
        from PyQt6.QtWidgets import QFileDialog
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"允收記錄_{self.batch['lot_number']}.pdf", "PDF (*.pdf)")
        if not path: return
        
        writer = QPdfWriter(path)
        writer.setPageSize(QPdfWriter.PageSize.A4)
        writer.setResolution(300)
        
        painter = QPainter(writer)
        # Render the table to PDF (simplified)
        self.table.render(painter)
        painter.end()
        QMessageBox.information(self, "匯出成功", f"PDF 已儲存至 {path}")

class AcceptanceViewDialog(QDialog):
    \"\"\"查看允收紀錄\"\"\"
    def __init__(self, parent, batch: dict, records: list):
        super().__init__(parent)
        self.setWindowTitle(f"歷史允收記錄 — {batch['lot_number']}")
        self.setMinimumSize(500, 300)
        self.setStyleSheet(PAGE_STYLE)
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("此視窗供未來擴充查看詳細歷史紀錄用。\\n（可從 reagent_batch_acceptance 抓取 snapshot_data 渲染表格）"))
        
"""

with open("ui/qc/reagent_batch.py", "w") as f:
    f.write(content + new_code)
