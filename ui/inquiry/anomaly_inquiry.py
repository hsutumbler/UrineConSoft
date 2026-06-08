from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QDateEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QWidget, QFrame, QMessageBox, QDialog, QFileDialog
)
from PyQt6.QtCore import Qt, QDate, QMarginsF, QSizeF
from PyQt6.QtGui import QTextDocument, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from ui.base_page import BasePage, COLORS
from services.anomaly_service import AnomalyService
from PyQt6.QtWidgets import QComboBox
from services.qc_service import MasterService

class AnomalyInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("異常紀錄查詢", "查詢與列印品管異常紀錄", user)
        self.is_subpage = is_subpage
        self._build()

    def _build(self):
        # 篩選列
        filter_bar = QHBoxLayout()
        
        filter_bar.addWidget(QLabel("日期區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel("~"))
        filter_bar.addWidget(self.date_to)
        
        filter_bar.addSpacing(15)
        filter_bar.addWidget(QLabel("儀器："))
        self.cmb_inst = QComboBox()
        self.cmb_inst.addItem("全部", None)
        for inst in MasterService.get_instruments():
            self.cmb_inst.addItem(inst["instrument_name"], inst["instrument_id"])
        filter_bar.addWidget(self.cmb_inst)
        
        btn_search = QPushButton("查詢")
        btn_search.setObjectName("btn_primary")
        btn_search.clicked.connect(self._do_search)
        
        btn_view = QPushButton("檢視")
        btn_view.setMinimumWidth(80)
        btn_view.clicked.connect(self._on_view_clicked)
        
        filter_bar.addSpacing(10)
        filter_bar.addWidget(btn_search)
        filter_bar.addSpacing(10)
        filter_bar.addWidget(btn_view)
        filter_bar.addStretch()
        
        if not self.is_subpage:
            self.content_layout.addLayout(filter_bar)
        else:
            # We just don't add the filter bar layout
            pass
        
        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "單號", "發生時間", "儀器", "Level", "項目", "異常原因", "建立者"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch) # 異常原因 stretch
        
        self.table.setColumnWidth(1, 160) # 放寬發生時間欄位
        self.table.setColumnWidth(0, 110) # 放寬單號

        
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background: {COLORS.get('bg_input', '#FFFFFF')};
                border: 1px solid {COLORS.get('border', '#CCCCCC')};
                border-radius: 8px;
            }}
            QHeaderView::section {{
                background-color: {COLORS.get('table_header', '#F0EAD6')};
                padding: 4px;
                border: 1px solid {COLORS.get('grid', '#EEEEEE')};
                font-weight: bold;
            }}
        """)
        
        self.content_layout.addWidget(self.table, 1)

    def on_page_show(self):
        pass

    def execute_query(self, d_from, d_to, inst):
        self.date_from.setDate(QDate(d_from.year, d_from.month, d_from.day))
        self.date_to.setDate(QDate(d_to.year, d_to.month, d_to.day))
        
        start_date = d_from.strftime("%Y-%m-%d")
        end_date = d_to.strftime("%Y-%m-%d")
        inst_id = inst["instrument_id"] if inst else None
        
        records = AnomalyService.get_all_records(start_date, end_date, inst_id)
        self.current_data = records
        self._populate_table(records)

    def _do_search(self):
        start_date = self.date_from.date().toPyDate().strftime("%Y-%m-%d")
        end_date = self.date_to.date().toPyDate().strftime("%Y-%m-%d")
        inst_id = self.cmb_inst.currentData()
        
        records = AnomalyService.get_all_records(start_date, end_date, inst_id)
        self.current_data = records
        self._populate_table(records)
        
    def _populate_table(self, records):
        self.table.setRowCount(0)
        for r in records:
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            # Formatting
            dt = r.get("occurrence_time") or ""
            inst = r.get("instrument_name") or ""
            lvl = r.get("qc_level") or ""
            param = r.get("reagent_name") or ""
            cause = r.get("anomaly_cause") or ""
            creator = r.get("creator_name") or ""
            serial = r.get("serial_number") or ""
            
            self._set_item(row, 0, serial, user_data=r)
            self._set_item(row, 1, str(dt)[:16] if dt else "")
            self._set_item(row, 2, inst)
            self._set_item(row, 3, lvl)
            self._set_item(row, 4, param)
            self._set_item(row, 5, cause)
            self._set_item(row, 6, creator)
            
    def _set_item(self, row, col, text, user_data=None):
        item = QTableWidgetItem(str(text))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        if user_data:
            item.setData(Qt.ItemDataRole.UserRole, user_data)
        self.table.setItem(row, col, item)

    def _show_context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item: return
        
        from PyQt6.QtWidgets import QMenu
        menu = QMenu()
        act_view = menu.addAction("檢視異常紀錄")
        
        action = menu.exec(self.table.viewport().mapToGlobal(pos))
        if action == act_view:
            rec = self.table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
            self._show_detail(rec)

    def _on_view_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇一筆異常紀錄")
            return
            
        row = selected[0].row()
        item = self.table.item(row, 0)
        if not item: return
            
        rec = item.data(Qt.ItemDataRole.UserRole)
        if rec:
            self._show_detail(rec)

    def _show_detail(self, r):
        # reuse the dialog but maybe readonly?
        # Actually it's easier to just show a QMessageBox or a custom simple dialog
        from ui.qc.anomaly_dialog import AnomalyRecordDialog
        
        # We need to construct result_data mock
        r_mock = {
            "result_id": r["result_id"],
            "measured_value": r["anomaly_data"],
            "result_date": r["occurrence_time"],
            "westgard_flag": r["violated_rule"],
            "instrument_name": r["instrument_name"],
            "lot_number": r["qc_lot_number"]
        }
        
        dlg = AnomalyRecordDialog(self, self.user, r_mock, r["qc_level"])
        dlg.exec()
        self._do_search() # refresh

    def _print_report(self):
        if not hasattr(self, 'current_data') or not self.current_data:
            QMessageBox.warning(self, "無資料", "目前沒有資料可以列印。")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", "異常紀錄查詢.pdf", "PDF (*.pdf)")
        if not path: return
        
        html = self._build_html_table()
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

    def _build_html_table(self) -> str:
        rows_html = ""
        for r in self.current_data:
            dt = str(r.get("occurrence_time") or "")[:16]
            inst = str(r.get("instrument_name") or "")
            lvl = str(r.get("qc_level") or "")
            param = str(r.get("reagent_name") or "")
            cause = str(r.get("anomaly_cause") or "")
            creator = str(r.get("creator_name") or "")
            serial = str(r.get("serial_number") or "")
            
            rows_html += f"""
            <tr>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{serial}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{dt}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{inst}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{lvl}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{param}</td>
                <td style='border: 1px solid #ccc; padding: 4px;'>{cause}</td>
                <td style='border: 1px solid #ccc; padding: 4px; text-align: center;'>{creator}</td>
            </tr>
            """
            
        return f"""
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
            <h2>異常紀錄查詢</h2>
            <table>
                <thead>
                    <tr>
                        <th width="10%">表單編號</th>
                        <th width="15%">發生時間</th>
                        <th width="10%">儀器</th>
                        <th width="10%">Level</th>
                        <th width="15%">異常項目</th>
                        <th width="25%">異常原因</th>
                        <th width="15%">建檔人員</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </body>
        </html>
        """
