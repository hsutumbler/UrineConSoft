with open('ui/inquiry/report_inquiry.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

new_print = """    def _print_report(self):
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
        
        html = f\"\"\"
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; }}
                @page {{ margin: 10mm; }}
                .title {{ font-size: 16pt; text-align: center; font-weight: bold; margin-bottom: 5px; }}
                .doc-id {{ font-size: 10pt; text-align: right; margin-bottom: 5px; }}
                .info {{ font-size: 11pt; margin-bottom: 10px; line-height: 1.2; }}
                .section-title {{ font-size: 12pt; font-weight: bold; margin-top: 15px; margin-bottom: 5px; text-align: left; }}
                .data-table {{ font-size: 10pt; margin-bottom: 10px; border-collapse: collapse; width: 100%; }}
                .data-table th, .data-table td {{ text-align: center; padding: 2px; border: 1px solid black; }}
                .data-table th {{ background-color: #f2f2f2; }}
                .footer {{ font-size: 10pt; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <div class="title">{title}</div>
            <div class="doc-id">文件編號：{doc_id}</div>
            <div class="info">
                組別：{group}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;統計日期：{stat_date}&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;品管液批號：{self.lot_number}
            </div>
        \"\"\"
        
        if self.table_qual.rowCount() > 0:
            html += '<div class="section-title">定性 / 半定量</div>'
            html += '<table class="data-table"><thead><tr>'
            cols = self.table_qual.columnCount()
            for c in range(cols):
                html += f"<th>{self.table_qual.horizontalHeaderItem(c).text()}</th>"
            html += "</tr></thead><tbody>"
            for r in range(self.table_qual.rowCount()):
                html += "<tr>"
                for c in range(cols):
                    item = self.table_qual.item(r, c)
                    val = item.text() if item else ""
                    color = "color: red;" if "不合格" in val else ""
                    html += f"<td style='{color}'>{val}</td>"
                html += "</tr>"
            html += "</tbody></table>"

        if self.table_quant.rowCount() > 0:
            html += '<div class="section-title">定量</div>'
            html += '<table class="data-table"><thead><tr>'
            cols = self.table_quant.columnCount()
            for c in range(cols):
                html += f"<th>{self.table_quant.horizontalHeaderItem(c).text()}</th>"
            html += "</tr></thead><tbody>"
            for r in range(self.table_quant.rowCount()):
                html += "<tr>"
                for c in range(cols):
                    item = self.table_quant.item(r, c)
                    val = item.text() if item else ""
                    color = "color: red;" if "不合格" in val else ""
                    html += f"<td style='{color}'>{val}</td>"
                html += "</tr>"
            html += "</tbody></table>"
            
        html += f'<div class="footer">列印日期：{print_date}</div>'
        if self.table_quant.rowCount() > 0:
            html += '<div class="footer">備註：TM=Target Mean, AM=Actual Mean, TSD=Target SD, ASD=Actual SD</div>'
            
        html += "</body></html>"
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"品管報表_{self.lot_number}.pdf", "PDF (*.pdf)")
        if not path: return
        
        doc = QTextDocument()
        doc.setHtml(html)
        
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功儲存至:\\n{path}")
"""

code = re.sub(r'    def _print_report\(self\):.*?(?=\n\nclass ReportInquiryPage)', new_print, code, flags=re.DOTALL)

with open('ui/inquiry/report_inquiry.py', 'w', encoding='utf-8') as f:
    f.write(code)
