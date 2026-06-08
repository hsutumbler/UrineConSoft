from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from ui.base_page import PAGE_STYLE, BasePage
from services.inquiry_service import InquiryService
from services.qc_service import MasterService

class ReportInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("品管報表", "列印或匯出 L-J 報表與統計資料", user)
        self.is_subpage = is_subpage
        self.setStyleSheet(PAGE_STYLE)
        self._build_ui()
        self._load_instruments()

    def _build_ui(self):
        # Filters
        filter_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("儀器："))
        self.cmb_inst = QComboBox()
        self.cmb_inst.setMinimumWidth(120)
        row1.addWidget(self.cmb_inst)
        
        row1.addSpacing(20)
        
        row1.addWidget(QLabel("日期區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy/MM/dd")
        self.date_from.setMinimumWidth(120)
        self.date_from.setDate(QDate.currentDate().addDays(-QDate.currentDate().day() + 1))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy/MM/dd")
        self.date_to.setMinimumWidth(120)
        self.date_to.setDate(QDate.currentDate())
        
        row1.addWidget(self.date_from)
        row1.addWidget(QLabel(" ~ "))
        row1.addWidget(self.date_to)
        
        row1.addSpacing(20)
        row1.addWidget(QLabel("批號："))
        self.cmb_lot = QComboBox()
        self.cmb_lot.setMinimumWidth(150)
        self.cmb_lot.addItem("全部")
        row1.addWidget(self.cmb_lot)
        row1.addStretch()
        filter_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addStretch()
        btn_query = QPushButton("🔍 查詢")
        btn_query.setObjectName("btn_primary")
        btn_query.setMinimumWidth(100)
        btn_query.clicked.connect(self._load_data)
        row2.addWidget(btn_query)
        
        btn_print = QPushButton("列印 / 匯出 PDF")
        btn_print.setMinimumWidth(150)
        btn_print.clicked.connect(self._print_report)
        row2.addWidget(btn_print)
        row2.addStretch()
        filter_layout.addLayout(row2)
        
        if not self.is_subpage:
            self.content_layout.addLayout(filter_layout)

        # Tab 1: Quantitative (定量)
        self.tabs = QTabWidget()
        self.tab_quant = QWidget()
        layout_quant = QVBoxLayout(self.tab_quant)
        self.table_quant = QTableWidget()
        self.table_quant.setColumnCount(12)
        self.table_quant.setHorizontalHeaderLabels([
            "項目", "Level", "N", "TM", "AM", "TSD", "ASD", "CV%", "Bias%", "TE%", "TEa%", "評估"
        ])
        self.table_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_quant.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_quant.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout_quant.addWidget(self.table_quant)
        
        note_quant = QLabel("備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD")
        note_quant.setObjectName("page_subtitle")
        layout_quant.addWidget(note_quant)
        
        # Tab 2: Qualitative/Semi-quantitative (定性/半定量)
        self.tab_qual = QWidget()
        layout_qual = QVBoxLayout(self.tab_qual)
        self.table_qual = QTableWidget()
        self.table_qual.setColumnCount(5)
        self.table_qual.setHorizontalHeaderLabels([
            "項目", "Level", "N", "合格數", "不合格數"
        ])
        self.table_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_qual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_qual.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout_qual.addWidget(self.table_qual)
        
        self.tabs.addTab(self.tab_qual, "定性 / 半定量")
        self.tabs.addTab(self.tab_quant, "定量")
        
        if not self.is_subpage:
            self.content_layout.addWidget(self.tabs)
        else:
            self.layout().addWidget(self.tabs)

    def execute_query(self, d_from, d_to, inst, lot):
        if not inst:
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "錯誤", "請選擇儀器")
            return
            
        self.date_from.setDate(QDate(d_from.year, d_from.month, d_from.day))
        self.date_to.setDate(QDate(d_to.year, d_to.month, d_to.day))
        
        inst_id = inst["instrument_id"]
        lot_num = lot["lot_number"] if lot else "全部"
        
        from services.inquiry_service import InquiryService
        records = InquiryService.get_qc_reports(d_from, d_to, inst_id, lot_num)
        self.current_records = records
        
        self.table_quant.setRowCount(0)
        self.table_qual.setRowCount(0)
        
        for rec in self.current_records:
            param = rec["reagent_name"]
            lvl = rec["level_name"]
            n = str(rec["n"])
            acc = str(rec["accepts"])
            rej = str(rec["rejects"])
            
            if rec["param_type"] == 1:
                # Quantitative
                r = self.table_quant.rowCount()
                self.table_quant.insertRow(r)
                
                tm = f"{rec['tm']:.4f}" if rec.get('tm') is not None else "—"
                mean = f"{rec['mean']:.4f}"
                tsd = f"{rec['tsd']:.4f}" if rec.get('tsd') is not None else "—"
                sd = f"{rec['sd']:.4f}"
                cv = f"{rec['cv']:.2f}%"
                bias = f"{rec['bias_pct']:.2f}%" if rec.get('bias_pct') is not None else "—"
                te = f"{rec['te']:.2f}%" if rec.get('te') is not None else "—"
                tea = f"{rec['tea_percent']:.2f}%" if rec.get('tea_percent') is not None else "—"

                if rec.get('te') is not None and rec.get('tea_percent') is not None:
                    if rec['te'] > rec['tea_percent']:
                        eval_res = "不合格"
                    else:
                        eval_res = "合格"
                else:
                    eval_res = "—"

                vals = [param, lvl, n, tm, mean, tsd, sd, cv, bias, te, tea, eval_res]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if c == 11 and eval_res == "不合格":
                        item.setForeground(Qt.GlobalColor.red)
                    self.table_quant.setItem(r, c, item)
            else:
                # Qualitative / Semi-quantitative
                r = self.table_qual.rowCount()
                self.table_qual.insertRow(r)
                
                vals = [param, lvl, n, acc, rej]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_qual.setItem(r, c, item)
        

    def _load_instruments(self):
        self.cmb_inst.blockSignals(True)
        self.cmb_inst.clear()
        insts = MasterService.get_instruments()
        for i in insts:
            self.cmb_inst.addItem(i["instrument_name"], i["instrument_id"])
        self.cmb_inst.blockSignals(False)
        self._load_lots()
        # Clear data on load instead of auto-loading
        self.table_quant.setRowCount(0)
        self.table_qual.setRowCount(0)
        self.current_records = []

    def _load_lots(self):
        from services.qc_service import QCBatchService
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        batches = QCBatchService.get_all()
        seen = set()
        for b in batches:
            if b["lot_number"] not in seen:
                seen.add(b["lot_number"])
                self.cmb_lot.addItem(b["lot_number"])
        self.cmb_lot.blockSignals(False)

    def _load_data(self):
        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            self.table.setRowCount(0)
            return
            
        from_d = self.date_from.date().toPyDate()
        to_d = self.date_to.date().toPyDate()
        lot = self.cmb_lot.currentText()
        
        records = InquiryService.get_qc_reports(from_d, to_d, inst_id, lot)
        self.current_records = records
        
        self.table_quant.setRowCount(0)
        self.table_qual.setRowCount(0)
        
        for rec in self.current_records:
            param = rec["reagent_name"]
            lvl = rec["level_name"]
            n = str(rec["n"])
            acc = str(rec["accepts"])
            rej = str(rec["rejects"])
            
            if rec["param_type"] == 1:
                # Quantitative
                r = self.table_quant.rowCount()
                self.table_quant.insertRow(r)
                
                tm = f"{rec['tm']:.4f}" if rec.get('tm') is not None else "—"
                mean = f"{rec['mean']:.4f}"
                tsd = f"{rec['tsd']:.4f}" if rec.get('tsd') is not None else "—"
                sd = f"{rec['sd']:.4f}"
                cv = f"{rec['cv']:.2f}%"
                bias = f"{rec['bias_pct']:.2f}%" if rec.get('bias_pct') is not None else "—"
                te = f"{rec['te']:.2f}%" if rec.get('te') is not None else "—"
                tea = f"{rec['tea_percent']:.2f}%" if rec.get('tea_percent') is not None else "—"

                if rec.get('te') is not None and rec.get('tea_percent') is not None:
                    if rec['te'] > rec['tea_percent']:
                        eval_res = "不合格"
                    else:
                        eval_res = "合格"
                else:
                    eval_res = "—"

                vals = [param, lvl, n, tm, mean, tsd, sd, cv, bias, te, tea, eval_res]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if c == 11 and eval_res == "不合格":
                        item.setForeground(Qt.GlobalColor.red)
                    self.table_quant.setItem(r, c, item)
            else:
                # Qualitative / Semi-quantitative
                r = self.table_qual.rowCount()
                self.table_qual.insertRow(r)
                
                vals = [param, lvl, n, acc, rej]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_qual.setItem(r, c, item)

    def on_page_show(self):
        self._load_instruments()

    def _print_report(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QTextDocument, QPageLayout
        from PyQt6.QtCore import QDate
        from PyQt6.QtWidgets import QFileDialog
        
        idx = self.tabs.currentIndex()
        tab_name = self.tabs.tabText(idx)
        table = self.table_qual if idx == 0 else self.table_quant
        
        if table.rowCount() == 0:
            QMessageBox.warning(self, "無資料", "目前表格沒有資料可以列印。")
            return
            
        # Get Header info
        title = "尿液品管定量與半定量月報表"
        group = "鏡檢"
        stat_date = f"{self.date_from.date().toString('yyyy-MM-dd')} ~ {self.date_to.date().toString('yyyy-MM-dd')}"
        doc_id = "LL-Q010/04-D"
        
        # Get unique lot numbers
        lots = set()
        if hasattr(self, 'current_records'):
            for rec in self.current_records:
                if rec.get("param_type") == (1 if idx == 1 else 2): # Very rough approximation, better to just collect all or filter by type
                    pass
            # Actually let's just collect lots from all current_records that match the tab's param_type condition
            for rec in self.current_records:
                if idx == 1 and rec.get("param_type") == 1:
                    lots.add(rec["lot_number"])
                elif idx == 0 and rec.get("param_type") != 1:
                    lots.add(rec["lot_number"])
        
        lot_str = "、".join(sorted(list(lots))) if lots else self.cmb_lot.currentText()
        if lot_str == "全部": lot_str = "" # Fallback
        
        print_date = QDate.currentDate().toString("yyyy-MM-dd")
        
        # Build HTML table
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                .title {{ font-size: 16pt; text-align: center; font-weight: bold; margin-bottom: 5px; }}
                .doc-id {{ font-size: 10pt; text-align: right; margin-bottom: 5px; }}
                .info {{ font-size: 12pt; margin-bottom: 10px; line-height: 1.5; }}
                .data-table {{ font-size: 12pt; margin-bottom: 10px; }}
                .data-table th, .data-table td {{ text-align: center; }}
                .data-table th {{ background-color: #f2f2f2; }}
                .footer {{ font-size: 12px; margin-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="title">{title}</div>
            <div class="doc-id">文件編號：{doc_id}</div>
            <div class="info">
                組別：{group}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;統計日期：{stat_date}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;品管液批號：{lot_str}
            </div>
            
            <table class="data-table" border="1" cellspacing="0" cellpadding="5" width="100%">
                <thead>
                    <tr>
        """
        
        cols = table.columnCount()
        for c in range(cols):
            html += f"<th>{table.horizontalHeaderItem(c).text()}</th>"
        html += "</tr></thead><tbody>"
        
        for r in range(table.rowCount()):
            html += "<tr>"
            for c in range(cols):
                item = table.item(r, c)
                val = item.text() if item else ""
                # Red text for eval fail
                if "不合格" in val:
                    html += f"<td style='color: red;'>{val}</td>"
                else:
                    html += f"<td>{val}</td>"
            html += "</tr>"
            
        html += """
                </tbody>
            </table>
        """
        
        html += f'<div class="footer">列印日期：{print_date}</div>'
        if idx == 1: # Quantitative
            html += '<div class="footer">備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD</div>'
            
        html += """
        </body>
        </html>
        """
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"品管報表_{tab_name}.pdf", "PDF (*.pdf)")
        if not path: return
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功儲存至:\n{path}")
