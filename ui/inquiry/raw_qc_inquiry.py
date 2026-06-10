import sys
from collections import defaultdict
from datetime import datetime, date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QTableWidget, QTableWidgetItem, 
    QHeaderView, QMessageBox, QDialog, QRadioButton, QButtonGroup, QFileDialog, QFormLayout
)
from PyQt6.QtCore import Qt, QDate, QMarginsF, QSizeF
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument, QPageLayout

from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import MasterService, QCBatchService
from services.inquiry_service import InquiryService


class RawQCInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("品管數據查詢", "查詢各時間點之品管全項目數值", user)
        self.is_subpage = is_subpage
        self.current_data = []
        self.reagents = []
        self._build()
        if not self.is_subpage:
            self._load_filters()

    def _build(self):
        filter_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("選擇儀器："))
        self.cmb_inst = QComboBox()
        self.cmb_inst.setMinimumWidth(120)
        self.cmb_inst.currentIndexChanged.connect(self._on_inst_changed)
        row1.addWidget(self.cmb_inst)
        
        row1.addSpacing(20)
        row1.addWidget(QLabel("日期區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy/MM/dd")
        self.date_from.setMinimumWidth(120)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        
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

        # 表格區 (Pivot Table)
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_layout.addWidget(self.table)
        
    def execute_query(self, d_from, d_to, inst, lot):
        if not inst:
            QMessageBox.warning(self, "錯誤", "請選擇儀器")
            return
        
        self.reagents = MasterService.get_reagents()
        
        inst_id = inst["instrument_id"]
        lot_num = lot["lot_number"] if lot else "全部"
        
        from services.inquiry_service import InquiryService
        data = InquiryService.get_qc_raw_data(
            d_from, 
            d_to, 
            inst_id, 
            lot_num
        )
        self.current_data = data
        self._populate_table()

    def _load_filters(self):
        insts = MasterService.get_instruments()
        self.cmb_inst.blockSignals(True)
        self.cmb_inst.clear()
        for inst in insts:
            self.cmb_inst.addItem(inst["instrument_name"], inst)
        self.cmb_inst.blockSignals(False)
        self._on_inst_changed()

    def _on_inst_changed(self):
        inst = self.cmb_inst.currentData()
        if not inst: return
        
        # Load lots
        lots = QCBatchService.get_all()
        unique_lots = list(set(b["lot_number"] for b in lots if b["lot_number"]))
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        for l in unique_lots:
            self.cmb_lot.addItem(l)
        self.cmb_lot.blockSignals(False)
        
        # Load Reagents
        self.reagents = MasterService.get_reagents()
        
        # Setup Table headers
        cols = ["時間", "批號", "Level"] + [r["reagent_name"] for r in self.reagents]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        # Clear data on inst change instead of auto-loading
        self.table.setRowCount(0)
        self.current_data = []

    def _load_data(self):
        inst = self.cmb_inst.currentData()
        if not inst: return
        
        d_from = self.date_from.date().toPyDate()
        d_to = self.date_to.date().toPyDate()
        lot = self.cmb_lot.currentText()
        
        raw_data = InquiryService.get_qc_raw_data(d_from, d_to, inst["instrument_id"], lot)
        self.current_data = raw_data
        self._populate_table()
        
    def _populate_table(self):
        if not hasattr(self, 'reagents') or not self.reagents:
            self.reagents = MasterService.get_reagents()
            
        cols = ["時間", "批號", "Level"] + [r["reagent_name"] for r in self.reagents]
        self.table.setColumnCount(len(cols))
        self.table.setHorizontalHeaderLabels(cols)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        
        raw_data = self.current_data
        
        # Pivot by (result_date, level_name)
        # { (dt, level_name): { "lot_number": x, "items": { reagent_name: value_str } } }
        pivot = {}
        for r in raw_data:
            dt = r["result_date"]
            level = r["level_name"]
            key = (dt, level)
            if key not in pivot:
                pivot[key] = {"lot_number": r["lot_number"] or "未設定", "items": {}}
                
            val_str = ""
            if r["param_type"] in (1, 3) and r["measured_value"] is not None:
                rname = r["reagent_name"]
                dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC") else (1 if r["param_type"] == 3 else 2))
                val_str = f"{float(r['measured_value']):.{dec}f}"
            elif r["param_type"] == 2 and r["qualitative_result"]:
                val_str = r["qualitative_result"]
                
            pivot[key]["items"][r["reagent_name"]] = {
                "val": val_str,
                "is_accepted": r["is_accepted"],
                "westgard_flag": r["westgard_flag"]
            }
            
        self.table.setRowCount(0)
        sorted_keys = sorted(pivot.keys(), key=lambda x: (x[0], x[1]))
        
        for r_idx, key in enumerate(sorted_keys):
            self.table.insertRow(r_idx)
            dt_str = key[0].strftime("%Y/%m/%d %H:%M:%S")
            level_str = key[1]
            lot_str = pivot[key]["lot_number"]
            
            self.table.setItem(r_idx, 0, QTableWidgetItem(dt_str))
            self.table.setItem(r_idx, 1, QTableWidgetItem(lot_str))
            self.table.setItem(r_idx, 2, QTableWidgetItem(level_str))
            
            for c_idx, re in enumerate(self.reagents):
                col = 3 + c_idx
                item_data = pivot[key]["items"].get(re["reagent_name"], {})
                val_str = item_data.get("val", "")
                it = QTableWidgetItem(val_str)
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                
                if item_data.get("is_accepted") is False:
                    it.setForeground(Qt.GlobalColor.red)
                    flag = item_data.get("westgard_flag")
                    if flag:
                        it.setToolTip(f"異常: {flag}")
                        
                self.table.setItem(r_idx, col, it)


    def _print_report(self):
        if not self.current_data:
            QMessageBox.warning(self, "無資料", "目前表格沒有資料可以列印。")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"品管數據查詢.pdf", "PDF (*.pdf)")
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
        # Group by (lot_number, level) -> list of row data
        groups = defaultdict(list)
        
        for r in self.current_data:
            dt = r["result_date"]
            level = r["level_name"]
            lot = r["lot_number"] or "未設定"
            
            group_key = (lot, level)
            row_key = dt
            
            # Find if row already exists in this group
            row_data = next((item for item in groups[group_key] if item["dt"] == dt), None)
            if not row_data:
                row_data = {"dt": dt, "items": {}}
                groups[group_key].append(row_data)
                
            val_str = ""
            if r["param_type"] in (1, 3) and r["measured_value"] is not None:
                rname = r["reagent_name"]
                dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC") else (1 if r["param_type"] == 3 else 2))
                val_str = f"{float(r['measured_value']):.{dec}f}"
            elif r["param_type"] == 2 and r["qualitative_result"]:
                val_str = r["qualitative_result"]
                
            row_data["items"][r["reagent_name"]] = {"val": val_str, "is_accepted": r["is_accepted"]}
            
        # Get date range from UI
        d_from_str = self.date_from.date().toString("yyyy/MM/dd")
        d_to_str = self.date_to.date().toString("yyyy/MM/dd")
        
        html = """
        <html><head><style>
            body { font-family: sans-serif; font-size: 10pt; margin: 0; padding: 0; }
            h2 { text-align: center; margin-top: 0; margin-bottom: 10px; }
            h3 { color: #333; margin-top: 10px; margin-bottom: 5px; font-size: 11pt; }
            table { border-collapse: collapse; width: 100%; margin-left: auto; margin-right: auto; margin-bottom: 15px; font-size: 8pt; }
            th, td { border: 1px solid #aaa; padding: 4px; text-align: center; white-space: nowrap; }
            th { background-color: #f2f2f2; }
            .fail { color: red; }
        </style></head><body>
        <h2>品管數據查詢</h2>
        """
        
        for group_key in sorted(groups.keys()):
            lot, level = group_key
            html += f"<h3>批號：{lot} &nbsp;&nbsp;&nbsp; {level} &nbsp;&nbsp;&nbsp; 日期區間：{d_from_str} ~ {d_to_str}</h3>"
            html += "<table><thead><tr><th>時間</th>"
            for re in self.reagents:
                html += f"<th>{re['reagent_name']}</th>"
            html += "</tr></thead><tbody>"
            
            rows = sorted(groups[group_key], key=lambda x: x["dt"])
            for d in rows:
                time_str = d["dt"].strftime("%Y/%m/%d %H:%M:%S")
                html += f"<tr><td>{time_str}</td>"
                for re in self.reagents:
                    item_data = d["items"].get(re["reagent_name"], {})
                    v = item_data.get("val", "")
                    cls = "fail" if item_data.get("is_accepted") is False else ""
                    html += f"<td class='{cls}'>{v}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            
        html += "</body></html>"
        return html

    def on_page_show(self):
        pass
