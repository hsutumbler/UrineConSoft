import traceback
from datetime import date
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QMessageBox, QGroupBox, QTabWidget,
                             QDateEdit, QComboBox, QDialog, QFileDialog)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtPrintSupport import QPrinter

from ui.base_page import COLORS
from ui.base_page import BasePage
from services.inquiry_service import InquiryService

class QCReportDialog(QDialog):
    def __init__(self, parent, user, d_from, d_to, inst_id, lot_number, inst_name, expiry_date=""):
        super().__init__(parent)
        self.user = user
        self.d_from = d_from
        self.d_to = d_to
        self.inst_id = inst_id
        self.lot_number = lot_number
        self.inst_name = inst_name
        self.expiry_date = expiry_date
        
        self.current_records = []
        
        self.setWindowTitle("報表檢視 — " + f"{self.inst_name} ({self.lot_number})")
        self.resize(1000, 750)
        
        self.lot_prefix = self.lot_number.upper()[0] if self.lot_number else ""
        self.show_qual = self.lot_prefix != 'D'
        self.show_quant = True
        
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

        self.level_tabs = {}
        
        if not self.show_qual:
            page = QWidget()
            page_layout = QVBoxLayout(page)
            for lvl in ["1", "2"]:
                lvl_label = QLabel(f"Level {lvl}")
                lvl_label.setStyleSheet("font-weight: bold; font-size: 14px; margin-top: 5px;")
                page_layout.addWidget(lvl_label)
                
                tables = {}
                quant_group = QWidget()
                quant_layout = QVBoxLayout(quant_group)
                quant_layout.setContentsMargins(0, 0, 0, 0)
                table_quant = QTableWidget()
                table_quant.setColumnCount(11)
                table_quant.setHorizontalHeaderLabels([
                    "項目", "N", "TM", "AM", "TSD", "ASD", "CV%", "Bias%", "TE%", "TEa%", "評估"
                ])
                table_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table_quant.verticalHeader().setVisible(False)
                table_quant.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                table_quant.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                quant_layout.addWidget(table_quant)
                
                page_layout.addWidget(quant_group, 1)
                tables['quant'] = table_quant
                self.level_tabs[lvl] = tables
                
            note_quant = QLabel("備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD")
            note_quant.setObjectName("page_subtitle")
            page_layout.addWidget(note_quant)
            layout.addWidget(page)
        else:
            self.tabs = QTabWidget()
            for lvl in ["1", "2"]:
                tab = QWidget()
                t_layout = QVBoxLayout(tab)
                
                tables = {}
                qual_group = QWidget()
                qual_layout = QVBoxLayout(qual_group)
                qual_layout.setContentsMargins(0, 0, 0, 0)
                table_qual = QTableWidget()
                table_qual.setColumnCount(4)
                table_qual.setHorizontalHeaderLabels(["項目", "N", "合格數", "不合格數"])
                table_qual.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                table_qual.verticalHeader().setVisible(False)
                table_qual.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                table_qual.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                qual_layout.addWidget(table_qual)
                t_layout.addWidget(qual_group, 3 if self.show_quant else 1)
                tables['qual'] = table_qual
                
                if self.show_quant:
                    quant_group = QWidget()
                    quant_layout = QVBoxLayout(quant_group)
                    quant_layout.setContentsMargins(0, 0, 0, 0)
                    table_quant = QTableWidget()
                    table_quant.setColumnCount(11)
                    table_quant.setHorizontalHeaderLabels([
                        "項目", "N", "TM", "AM", "TSD", "ASD", "CV%", "Bias%", "TE%", "TEa%", "評估"
                    ])
                    table_quant.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
                    table_quant.verticalHeader().setVisible(False)
                    table_quant.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                    table_quant.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
                    quant_layout.addWidget(table_quant)
                    
                    note_quant = QLabel("備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD")
                    note_quant.setObjectName("page_subtitle")
                    quant_layout.addWidget(note_quant)
                    t_layout.addWidget(quant_group, 1)
                    tables['quant'] = table_quant
                    
                self.level_tabs[lvl] = tables
                self.tabs.addTab(tab, f"Level {lvl}")
                
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
        
        for tables in self.level_tabs.values():
            if 'qual' in tables: tables['qual'].setRowCount(0)
            if 'quant' in tables: tables['quant'].setRowCount(0)
        
        for rec in self.current_records:
            param = rec["reagent_name"]
            lvl_name = rec["level_name"]
            lvl = "1" if "1" in str(lvl_name) else "2"
            
            if lvl not in self.level_tabs:
                continue
                
            tables = self.level_tabs[lvl]
            n = str(rec["n"])
            acc = str(rec["accepts"])
            rej = str(rec["rejects"])
            
            if rec["param_type"] == 1 and 'quant' in tables:
                t = tables['quant']
                r = t.rowCount()
                t.insertRow(r)
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

                vals = [param, n, tm, mean, tsd, sd, cv, bias, te, tea, eval_res]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if c == 10 and eval_res == "不合格":
                        item.setForeground(Qt.GlobalColor.red)
                    t.setItem(r, c, item)
            elif rec["param_type"] != 1 and 'qual' in tables:
                t = tables['qual']
                r = t.rowCount()
                t.insertRow(r)
                
                vals = [param, n, acc, rej]
                for c, v in enumerate(vals):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    t.setItem(r, c, item)

    def _print_report(self):
        doc_id = "FM-LA-38-03"
        group = "鏡檢組"
        stat_date = f"{self.d_from.replace('-', '/')} - {self.d_to.replace('-', '/')}"
        
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
        """
        
        for i, lvl in enumerate(["1", "2"]):
            tables = self.level_tabs[lvl]
            if i > 0:
                html += '<div style="page-break-before: always;"></div>'
                
            html += f"""
                <div class="title">品管報表</div>
                <div class="doc-id">文件編號：{doc_id}</div>
                <div class="info">
                    <div>統計日期：{stat_date}</div>
                    <div>組別：{group}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;儀器：{self.inst_name}</div>
                    <div>品管液批號：{self.lot_number}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Level：{lvl}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;穩定效期：{self.expiry_date}</div>
                </div>
            """
            
            if 'qual' in tables and tables['qual'].rowCount() > 0:
                html += '<div class="section-title">定性 / 半定量</div>'
                html += '<table class="data-table" width="100%"><thead><tr>'
                cols = tables['qual'].columnCount()
                for c in range(cols):
                    html += f"<th>{tables['qual'].horizontalHeaderItem(c).text()}</th>"
                html += "</tr></thead><tbody>"
                for r in range(tables['qual'].rowCount()):
                    html += "<tr>"
                    for c in range(cols):
                        item = tables['qual'].item(r, c)
                        val = item.text() if item else ""
                        if "不合格" in val:
                            html += f"<td><span style='color: red;'>{val}</span></td>"
                        else:
                            html += f"<td>{val}</td>"
                    html += "</tr>"
                html += "</tbody></table>"
 
            if 'quant' in tables and tables['quant'].rowCount() > 0:
                html += '<div class="section-title">定量</div>'
                html += '<table class="data-table" width="100%"><thead><tr>'
                cols = tables['quant'].columnCount()
                for c in range(cols):
                    html += f"<th>{tables['quant'].horizontalHeaderItem(c).text()}</th>"
                html += "</tr></thead><tbody>"
                for r in range(tables['quant'].rowCount()):
                    html += "<tr>"
                    for c in range(cols):
                        item = tables['quant'].item(r, c)
                        val = item.text() if item else ""
                        if "不合格" in val:
                            html += f"<td><span style='color: red;'>{val}</span></td>"
                        else:
                            html += f"<td>{val}</td>"
                    html += "</tr>"
                html += "</tbody></table>"
                html += '<div class="footer">備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD</div>'
                
            html += f'<div class="footer">列印日期：{print_date}</div>'
            html += """
                <table width="100%" border="0" style="margin-top: 40px;">
                    <tr>
                        <td width="50%" align="left" style="border: none; font-size: 12pt;">組長：</td>
                        <td width="50%" align="left" style="border: none; font-size: 12pt;">技術主任：</td>
                    </tr>
                </table>
            """
            
        html += "</body></html>"
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        from PyQt6.QtPrintSupport import QPrintDialog
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            doc.print(printer)

class ReportInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("品管報表", "列印或匯出 L-J 報表與統計資料", user)
        self.is_subpage = is_subpage
        self._build_ui()

    def _build_ui(self):
        # When embedded in ComprehensiveInquiryPage, the filters are provided by the parent.
        # We display the search results (lots) in a table.
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

        # Add the table to the content layout provided by BasePage
        self.content_layout.addWidget(self.table)

    def execute_query(self, d_from, d_to, inst, lot=None):
        self.d_from_str = d_from.strftime("%Y-%m-%d") if hasattr(d_from, "strftime") else d_from
        self.d_to_str = d_to.strftime("%Y-%m-%d") if hasattr(d_to, "strftime") else d_to

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
            QMessageBox.warning(self, "提示", "請先從表格中選擇一個批號。")
            return
            
        row = selected[0].row()
        item = self.table.item(row, 0)
        if not item: return
        
        b = item.data(Qt.ItemDataRole.UserRole)
        if not b: return
        
        exp_date = b.get("expiry_date", "")
        if exp_date and hasattr(exp_date, "strftime"):
            exp_date = exp_date.strftime("%Y/%m/%d")
            
        try:
            dialog = QCReportDialog(self, self.user, self.d_from_str, self.d_to_str, b["instrument_id"], b["lot_number"], b["instrument_name"], exp_date)
            dialog.exec()
        except Exception as e:
            err_msg = traceback.format_exc()
            QMessageBox.critical(self, "發生錯誤", f"開啟報表檢視時發生錯誤:\n{err_msg}")



    def _print_report(self):
        self._on_view_clicked()
