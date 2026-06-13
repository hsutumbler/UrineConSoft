from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox, QTabWidget, QDialog
)
from PyQt6.QtCore import Qt, QDate
from ui.base_page import PAGE_STYLE, BasePage, COLORS
from services.inquiry_service import InquiryService
from services.qc_service import MasterService

class ReportDetailDialog(QDialog):
    def __init__(self, parent, user, d_from, d_to, inst_id, lot_number, inst_name, expiry_date=""):
        super().__init__(parent)
        self.user = user
        self.d_from = d_from
        self.d_to = d_to
        self.inst_id = inst_id
        self.lot_number = lot_number
        self.inst_name = inst_name
        self.expiry_date = expiry_date
        self.setWindowTitle(f"報表檢視 — {inst_name} ({lot_number})")
        self.setMinimumSize(1000, 600)
        self.setStyleSheet(PAGE_STYLE)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        top = QHBoxLayout()
        title = QLabel(f"品管報表統計 — 儀器: {self.inst_name} / 批號: {self.lot_number}")
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS.get('primary', '#000')};")
        top.addWidget(title)
        top.addStretch()
        

        
        layout.addLayout(top)

        self.tabs = QTabWidget()
        
        # Qualitative/Semi-quantitative (定性/半定量)
        self.tab_qual = QWidget()
        layout_qual = QVBoxLayout(self.tab_qual)
        self.table_qual = QTableWidget()
        self.table_qual.setColumnCount(5)
        self.table_qual.setHorizontalHeaderLabels(["項目", "Level", "N", "合格數", "不合格數"])
        self.table_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_qual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_qual.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout_qual.addWidget(self.table_qual)
        
        # Quantitative (定量)
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
        
        self.tabs.addTab(self.tab_qual, "定性 / 半定量")
        self.tabs.addTab(self.tab_quant, "定量")
        
        layout.addWidget(self.tabs)        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_print = QPushButton("🖨️ 列印")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _load_data(self):
        records = InquiryService.get_qc_reports(self.d_from, self.d_to, self.inst_id, self.lot_number)
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
                r = self.table_quant.rowCount()
                self.table_quant.insertRow(r)
                dec = 3 if param == "SG" else (1 if param in ("RBC", "WBC") else 2)
                
                tm = f"{rec['tm']:.{dec}f}" if rec.get('tm') is not None else "—"
                mean = f"{rec['mean']:.{dec}f}"
                tsd = f"{rec['tsd']:.{dec}f}" if rec.get('tsd') is not None else "—"
                sd = f"{rec['sd']:.{dec}f}"
                cv = f"{rec['cv']:.2f}%"
                bias = f"{rec['bias_pct']:.2f}%" if rec.get('bias_pct') is not None else "—"
                te = f"{rec['te']:.2f}%" if rec.get('te') is not None else "—"
                tea = f"{rec['tea_percent']:.2f}%" if rec.get('tea_percent') is not None else "—"

                if rec.get('te') is not None and rec.get('tea_percent') is not None:
                    eval_res = "不合格" if rec['te'] > rec['tea_percent'] else "合格"
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
                r = self.table_qual.rowCount()
                self.table_qual.insertRow(r)
                
                vals = [param, lvl, n, acc, rej]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table_qual.setItem(r, c, item)

    def _print_report(self):
        from PyQt6.QtPrintSupport import QPrinter
        from PyQt6.QtGui import QTextDocument, QPageLayout
        from PyQt6.QtCore import QDate
        from PyQt6.QtWidgets import QFileDialog
        
        if self.table_qual.rowCount() == 0 and self.table_quant.rowCount() == 0:
            QMessageBox.warning(self, "無資料", "目前表格沒有資料可以列印。")
            return
            
        title = "尿液品管定量與半定量月報表"
        group = "鏡檢"
        stat_date = f"{self.d_from.strftime('%Y-%m-%d')} ~ {self.d_to.strftime('%Y-%m-%d')}"
        doc_id = "LL-Q010/04-D"
        
        print_date = QDate.currentDate().toString("yyyy-MM-dd")
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                @page {{ margin: 10mm; }}
                .title {{ font-size: 16pt; text-align: center; font-weight: bold; margin-bottom: 5px; }}
                .doc-id {{ font-size: 12pt; text-align: right; margin-bottom: 5px; }}
                .info {{ font-size: 12pt; margin-bottom: 10px; line-height: 1.2; }}
                .section-title {{ font-size: 12pt; font-weight: bold; margin-top: 15px; margin-bottom: 5px; text-align: left; }}
                .data-table {{ font-size: 10pt; margin-bottom: 10px; border-collapse: collapse; }}
                .data-table th, .data-table td {{ text-align: center; padding: 2px; border: 1px solid black; }}
                .data-table th {{ background-color: #f2f2f2; }}
                .footer {{ font-size: 12pt; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="title">{title}</div>
            <div class="doc-id">文件編號：{doc_id}</div>
            <div class="info">
                <div>組別：{group}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;統計日期：{stat_date}</div>
                <div style="margin-top: 5px;">品管液批號：{self.lot_number}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;穩定效期：{self.expiry_date}</div>
            </div>
        """
        
        if self.table_qual.rowCount() > 0:
            html += '<div class="section-title">定性 / 半定量</div>'
            html += '<table class="data-table" width="100%"><thead><tr>'
            cols = self.table_qual.columnCount()
            for c in range(cols):
                html += f"<th>{self.table_qual.horizontalHeaderItem(c).text()}</th>"
            html += "</tr></thead><tbody>"
            for r in range(self.table_qual.rowCount()):
                html += "<tr>"
                for c in range(cols):
                    item = self.table_qual.item(r, c)
                    val = item.text() if item else ""
                    if "不合格" in val:
                        html += f"<td><span style='color: red;'>{val}</span></td>"
                    else:
                        html += f"<td>{val}</td>"
                html += "</tr>"
            html += "</tbody></table>"

        if self.table_quant.rowCount() > 0:
            html += '<div class="section-title">定量</div>'
            html += '<table class="data-table" width="100%"><thead><tr>'
            cols = self.table_quant.columnCount()
            for c in range(cols):
                html += f"<th>{self.table_quant.horizontalHeaderItem(c).text()}</th>"
            html += "</tr></thead><tbody>"
            for r in range(self.table_quant.rowCount()):
                html += "<tr>"
                for c in range(cols):
                    item = self.table_quant.item(r, c)
                    val = item.text() if item else ""
                    if "不合格" in val:
                        html += f"<td><span style='color: red;'>{val}</span></td>"
                    else:
                        html += f"<td>{val}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            
        html += f'<div class="footer">列印日期：{print_date}</div>'
        if self.table_quant.rowCount() > 0:
            html += '<div class="footer">備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD</div>'
            
        html += """
            <table width="100%" border="0" style="margin-top: 40px;">
                <tr>
                    <td width="50%" align="left" style="border: none; font-size: 12pt;">組長：</td>
                    <td width="50%" align="left" style="border: none; font-size: 12pt;">技術主任：</td>
                </tr>
            </table>
        </body></html>
        """
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"品管報表_{self.lot_number}.pdf", "PDF (*.pdf)")
        if not path: return
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        from PyQt6.QtGui import QPageSize
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功儲存至:\\n{path}")


class ReportInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("品管報表", "列印或匯出 L-J 報表與統計資料", user)
        self.is_subpage = is_subpage
        self.setStyleSheet(PAGE_STYLE)
        self._build_ui()

    def _build_ui(self):
        # We only use this page embedded in ComprehensiveInquiryPage, 
        # so filter UI is not added here if is_subpage is True.
        # But we still build it just in case.
        filter_layout = QVBoxLayout()
        # (Omitted filter building since it's only used as subpage)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["儀器", "批號", "Level", "穩定效期"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self._on_view_clicked)
        
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

        if not self.is_subpage:
            self.content_layout.addWidget(self.table)
        else:
            self.layout().addWidget(self.table)

    def execute_query(self, d_from, d_to, inst, lot):
        # 'lot' is ignored since we just want all batches in the date range
        self.d_from = d_from
        self.d_to = d_to
        inst_id = inst["instrument_id"] if inst else None
        
        batches = InquiryService.get_qc_report_batches(d_from, d_to, inst_id)
        
        self.table.setRowCount(0)
        for b in batches:
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            i1 = QTableWidgetItem(b["instrument_name"])
            i1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            i1.setData(Qt.ItemDataRole.UserRole, b)
            self.table.setItem(r, 0, i1)
            
            i2 = QTableWidgetItem(b["lot_number"])
            i2.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 1, i2)
            
            i3 = QTableWidgetItem(b["level_name"])
            i3.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 2, i3)
            
            exp_date = b["expiry_date"].strftime("%Y/%m/%d") if b.get("expiry_date") else ""
            i4 = QTableWidgetItem(exp_date)
            i4.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(r, 3, i4)

    def _on_view_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇一個批號。")
            return
            
        row = selected[0].row()
        item = self.table.item(row, 0)
        if not item: return
        
        b = item.data(Qt.ItemDataRole.UserRole)
        if not b: return
        
        try:
            exp_date = b.get("expiry_date", "")
            if exp_date and hasattr(exp_date, "strftime"):
                exp_date = exp_date.strftime("%Y/%m/%d")
            dlg = ReportDetailDialog(self, self.user, self.d_from, self.d_to, b["instrument_id"], b["lot_number"], b["instrument_name"], exp_date)
            dlg.exec()
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            QMessageBox.critical(self, "發生錯誤", f"開啟報表檢視時發生錯誤:\\n{err_msg}")


    def _print_report(self):
        self._on_view_clicked()
