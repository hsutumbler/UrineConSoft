from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from ui.base_page import PAGE_STYLE
from services.inquiry_service import InquiryService

class ReagentInquiryPage(QWidget):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__()
        self.user = user
        self.is_subpage = is_subpage
        self.setStyleSheet(PAGE_STYLE)
        self._build_ui()
        if not self.is_subpage:
            self._load_lots()
        self.table.setRowCount(0)
        
    def on_page_show(self):
        self._load_lots()
        self.table.setRowCount(0)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        header = QVBoxLayout()
        self.header = QWidget()
        self.header.setLayout(header)
        title = QLabel("試劑允收查詢")
        title.setObjectName("page_title")
        subtitle = QLabel("查詢歷史試劑允收紀錄")
        subtitle.setObjectName("page_subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        if not self.is_subpage:
            layout.addWidget(self.header)

        # Filters
        filter_bar = QHBoxLayout()
        filter_bar.addWidget(QLabel("日期區間："))
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-3))
        self.date_from.setDisplayFormat("yyyy/MM/dd")
        self.date_from.setMinimumWidth(120)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.setDisplayFormat("yyyy/MM/dd")
        self.date_to.setMinimumWidth(120)
        
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel(" ~ "))
        filter_bar.addWidget(self.date_to)
        
        filter_bar.addSpacing(20)
        filter_bar.addWidget(QLabel("試劑批號："))
        
        from PyQt6.QtWidgets import QComboBox, QPushButton
        self.cmb_lot = QComboBox()
        self.cmb_lot.addItem("全部")
        self.cmb_lot.setMinimumWidth(150)
        filter_bar.addWidget(self.cmb_lot)
        
        filter_bar.addSpacing(20)
        btn_query = QPushButton("🔍 查詢")
        btn_query.setObjectName("btn_primary")
        btn_query.setMinimumWidth(100)
        btn_query.clicked.connect(self._load_data)
        filter_bar.addWidget(btn_query)
        
        self.btn_view = QPushButton("檢視")
        self.btn_view.setMinimumWidth(100)
        self.btn_view.clicked.connect(self._on_view_clicked)
        filter_bar.addWidget(self.btn_view)
        
        filter_bar.addStretch()
        
        if not self.is_subpage:
            layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "日期", "原批號", "本試劑批號", "執行人員"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Right click menu
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        layout.addWidget(self.table)

    def _load_lots(self):
        from services.qc_service import ReagentBatchService
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        batches = ReagentBatchService.get_all()
        seen = set()
        for b in batches:
            if b["lot_number"] not in seen:
                seen.add(b["lot_number"])
                self.cmb_lot.addItem(b["lot_number"])
        self.cmb_lot.blockSignals(False)

    def _load_data(self):
        from_d = self.date_from.date().toPyDate()
        to_d = self.date_to.date().toPyDate()
        lot = self.cmb_lot.currentText()
        records = InquiryService.get_reagent_acceptances(from_d, to_d, lot)
        self._populate_table(records)

    def _populate_table(self, records):
        self.table.setRowCount(0)
        for r, rec in enumerate(records):
            self.table.insertRow(r)
            
            dt = str(rec["accepted_at"])[:16]
            new_lot = rec["lot_number"]
            by = rec["accepted_by_name"]
            
            import json
            snap = rec["snapshot_data"]
            old_lot = ""
            
            if snap:
                try:
                    s_data = json.loads(snap) if isinstance(snap, str) else snap
                    old_lot = s_data.get("active_lot", "")
                except:
                    pass

            vals = [dt, old_lot, new_lot, by]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setData(Qt.ItemDataRole.UserRole, rec)
                self.table.setItem(r, c, item)

    def execute_query(self, d_from, d_to, reagent, lot):
        self.date_from.setDate(QDate(d_from.year, d_from.month, d_from.day))
        self.date_to.setDate(QDate(d_to.year, d_to.month, d_to.day))
        lot_num = lot["lot_number"] if lot else None
        
        data = InquiryService.get_reagent_acceptances(d_from, d_to, lot_num)
        self._populate_table(data)
        
    def _show_context_menu(self, pos):
        from PyQt6.QtWidgets import QMenu
        item = self.table.itemAt(pos)
        if not item:
            return
            
        menu = QMenu(self)
        act_view = menu.addAction("檢視允收資料")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        
        if action == act_view:
            rec = self.table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            self._view_acceptance(rec)

    def _on_view_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "提示", "請先選擇一筆允收紀錄")
            return
            
        row = selected[0].row()
        item = self.table.item(row, 0)
        if not item:
            return
            
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
            
        self._view_acceptance(rec)
            
    def _view_acceptance(self, rec):
        from ui.qc.reagent_batch import AcceptanceDialog
        b = {
            "batch_id": rec["reagent_batch_id"],
            "lot_number": rec["lot_number"],
            "expiry_date": rec["expiry_date"],
            "open_date": rec["open_date"],
            "accepted_by_name": rec.get("accepted_by_name"),
            "accepted_at": str(rec.get("accepted_at"))[:16]
        }
        
        import json
        snap = rec.get("snapshot_data")
        if isinstance(snap, str):
            try:
                snap = json.loads(snap)
            except:
                pass
                
        dlg = AcceptanceDialog(self, b, self.user, read_only=True, snapshot_data=snap)
        dlg.exec()

    def _print_report(self):
        if self.table.rowCount() == 0:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "無資料", "目前沒有資料可以列印。")
            return
            
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        from PyQt6.QtGui import QTextDocument, QPageLayout
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtCore import QMarginsF, QSizeF
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", "試劑允收查詢.pdf", "PDF (*.pdf)")
        if not path: return
        
        rows_html = ""
        for r in range(self.table.rowCount()):
            dt = self.table.item(r, 0).text()
            old_lot = self.table.item(r, 1).text()
            new_lot = self.table.item(r, 2).text()
            by = self.table.item(r, 3).text()
            
            rows_html += f"""
            <tr>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{dt}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{old_lot}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{new_lot}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{by}</td>
            </tr>
            """
            
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                th {{ border: 1px solid #666; background-color: #eee; padding: 6px; text-align: center; }}
                h2 {{ text-align: center; margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h2>試劑允收查詢</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>原批號</th>
                        <th>本試劑批號</th>
                        <th>執行人員</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
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
