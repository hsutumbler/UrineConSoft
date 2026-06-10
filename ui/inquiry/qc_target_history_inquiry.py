import json
from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QWidget, QFileDialog
)
from PyQt6.QtGui import QTextDocument, QPageLayout
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import Qt, QSizeF, QMarginsF
from ui.base_page import BasePage

class QCTargetHistoryDetailDialog(QDialog):
    def __init__(self, parent, form_id, dt_str, items):
        super().__init__(parent)
        self.form_id = form_id
        self.dt_str = dt_str
        self.items = items
        
        self.setWindowTitle(f"修改單明細 - {form_id} ({dt_str})")
        self.setMinimumSize(800, 400)
        self.setStyleSheet("QDialog { background-color: #FCFBF4; }")
        
        layout = QVBoxLayout(self)
        
        info = QLabel(f"儀器: {items[0]['instrument_name']} | 批號: {items[0]['lot_number']} | 修訂者: {items[0]['set_by_name']}")
        info.setStyleSheet("font-size: 14px; font-weight: bold; color: #008B8B;")
        layout.addWidget(info)
        
        reason = items[0].get("change_reason") or "未註記"
        lbl_reason = QLabel(f"變更原因: {reason}")
        lbl_reason.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        layout.addWidget(lbl_reason)
        
        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        table = self.table
        
        headers = ["項目", "Level", "變更前", "變更後"]
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(0)
        
        for row, item in enumerate(items):
            table.insertRow(row)
            
            is_semi = (item["param_type"] in (2, 3))
            
            def fmt_quant(tm, tsd, rname):
                if tm is None or tsd is None: return "無紀錄"
                dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC") else 2)
                return f"TM: {tm:.{dec}f}\nTSD: {tsd:.{dec}f}"
                
            def fmt_semi(s_min, s_max):
                if not s_min and not s_max: return "無紀錄"
                return f"{s_min} ~ {s_max}"
                
            if is_semi:
                orig_val = fmt_semi(item.get("prev_semi_min"), item.get("prev_semi_max"))
                new_val = fmt_semi(item.get("semi_target_min"), item.get("semi_target_max"))
            else:
                orig_val = fmt_quant(item.get("prev_tm"), item.get("prev_tsd"), item.get("reagent_name"))
                new_val = fmt_quant(item.get("tm"), item.get("tsd"), item.get("reagent_name"))
                
            if "無紀錄" in orig_val:
                orig_val = "無 (首次建立)"
                
            table.setItem(row, 0, QTableWidgetItem(item["reagent_name"]))
            table.setItem(row, 1, QTableWidgetItem(item["level_name"]))
            
            orig_item = QTableWidgetItem(orig_val)
            orig_item.setForeground(Qt.GlobalColor.darkGray)
            table.setItem(row, 2, orig_item)
            
            new_item = QTableWidgetItem(new_val)
            new_item.setForeground(Qt.GlobalColor.darkBlue)
            table.setItem(row, 3, new_item)
            
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(table)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        btn_close.setStyleSheet("padding: 5px 15px;")
        
        btn_print = QPushButton("🖨️ 列印")
        btn_print.clicked.connect(self._print_form)
        btn_print.setStyleSheet("padding: 5px 15px;")
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)

    def _print_form(self):
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"{self.form_id}.pdf", "PDF (*.pdf)")
        if not path: return
        
        rows_html = ""
        for i in range(self.table.rowCount()):
            param = self.table.item(i, 0).text()
            lvl = self.table.item(i, 1).text()
            old_val = self.table.item(i, 2).text().replace('\n', '<br>')
            new_val = self.table.item(i, 3).text().replace('\n', '<br>')
            
            rows_html += f"""
            <tr>
                <td style='border: 1px solid #000; padding: 6px; text-align: center;'>{param}</td>
                <td style='border: 1px solid #000; padding: 6px; text-align: center;'>{lvl}</td>
                <td style='border: 1px solid #000; padding: 6px; text-align: left; color: #666;'>{old_val}</td>
                <td style='border: 1px solid #000; padding: 6px; text-align: left; color: #00008B;'>{new_val}</td>
            </tr>
            """
            
        reason = self.items[0].get('change_reason') or '未註記'
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; font-size: 12px; line-height: 1.2; }}
                h2 {{ text-align: center; font-size: 16px; margin-bottom: 15px; }}
                .main-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; margin-bottom: 20px; }}
                .main-table th {{ border: 1px solid #000; background-color: #eee; padding: 8px; text-align: center; }}
                .info-row {{ margin-bottom: 2px; line-height: 1.2; }}
                .header-table {{ width: 100%; border: none; margin-bottom: 2px; border-collapse: collapse; }}
                .header-table td {{ border: none; padding: 2px 0; font-size: 12px; }}
                .signature-area {{ margin-top: 40px; font-size: 12px; text-align: right; padding-right: 50px; }}
            </style>
        </head>
        <body>
            <h2>品管範圍修改單</h2>
            <div class='info-row'><strong>單號：</strong>{self.form_id}</div>
            <table class="header-table">
                <tr>
                    <td width="45%"><strong>品管液批號：</strong>{self.items[0].get('lot_number', '')}</td>
                    <td width="10%"></td>
                    <td width="45%"><strong>穩定效期：</strong>{self.items[0].get('expiry_date', '')}</td>
                </tr>
                <tr>
                    <td width="45%"><strong>修改人員：</strong>{self.items[0].get('set_by_name', '')}</td>
                    <td width="10%"></td>
                    <td width="45%"><strong>修改時間：</strong>{self.dt_str}</td>
                </tr>
            </table>
            <div class='info-row'><strong>變更原因：</strong>{reason}</div>
            
            <table class="main-table">
                <thead>
                    <tr>
                        <th width="25%">項目</th>
                        <th width="15%">Level</th>
                        <th width="30%">變更前</th>
                        <th width="30%">變更後</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
            
            <div class="signature-area">
                <strong>組長：</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                <strong>技術主任：</strong>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
            </div>
        </body>
        </html>
        """
        
        doc = QTextDocument()
        doc.setHtml(html)
        doc.setDocumentMargin(20)
        
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功匯出至：\n{path}")


class QCTargetHistoryInquiryPage(BasePage):
    def __init__(self, user: dict, is_subpage=False):
        super().__init__("品管範圍修訂查詢", "查詢品管範圍設定與修訂紀錄", user)
        self.is_subpage = is_subpage
        self.current_data = []
        self.grouped_forms = []
        self._build()

    def _build(self):
        if not self.is_subpage:
            pass # Filters are handled by comprehensive_inquiry.py

        self.table = QTableWidget()
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.content_layout.addWidget(self.table)

    def execute_query(self, d_from, d_to, inst, lot):
        inst_id = inst["instrument_id"] if inst else None
        lot_num = lot["lot_number"] if lot else "全部"
        
        from services.inquiry_service import InquiryService
        self.current_data = InquiryService.get_qc_target_history(
            d_from, d_to, inst_id, lot_num
        )
        self._populate_table()

    def _populate_table(self):
        # Group raw data into Modification Forms
        groups = {}
        for item in self.current_data:
            is_semi = (item["param_type"] in (2, 3))
            is_changed = False
            if is_semi:
                orig_min = item.get("prev_semi_min")
                orig_max = item.get("prev_semi_max")
                new_min = item.get("semi_target_min")
                new_max = item.get("semi_target_max")
                if orig_min != new_min or orig_max != new_max:
                    is_changed = True
            else:
                orig_tm = item.get("prev_tm")
                orig_tsd = item.get("prev_tsd")
                new_tm = item.get("tm")
                new_tsd = item.get("tsd")
                if orig_tm != new_tm or orig_tsd != new_tsd:
                    is_changed = True

            if not is_changed:
                continue

            dt_str = item["set_at"].strftime("%Y-%m-%d %H:%M") if hasattr(item["set_at"], 'strftime') else str(item["set_at"])[:16]
            key = (dt_str, item["set_by_name"], item.get("change_reason", ""), item["instrument_name"], item["lot_number"])
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
            
        # Assign serial numbers chronologically (Ascending)
        sorted_keys_asc = sorted(groups.keys(), key=lambda x: x[0])
        month_counters = {}
        form_ids = {}
        
        for key in sorted_keys_asc:
            dt_str = key[0]
            ym_str = dt_str[:7].replace('-', '')
            if ym_str not in month_counters:
                month_counters[ym_str] = 1
            else:
                month_counters[ym_str] += 1
            form_ids[key] = f"REV-{ym_str}{month_counters[ym_str]:03d}"
            
        # Display latest first (Descending)
        sorted_keys_desc = sorted(groups.keys(), key=lambda x: x[0], reverse=True)
        self.grouped_forms = []
        
        for key in sorted_keys_desc:
            dt_str, set_by, reason, inst_name, lot = key
            form_id = form_ids[key]
            self.grouped_forms.append({
                "form_id": form_id,
                "dt_str": dt_str,
                "instrument_name": inst_name,
                "lot_number": lot,
                "change_reason": reason,
                "set_by_name": set_by,
                "items": groups[key],
                "item_count": len(groups[key])
            })

        headers = ["修改單號", "修訂時間", "儀器名稱", "批號", "異動項目數", "變更原因", "修訂者"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(0)
        
        for row, form in enumerate(self.grouped_forms):
            self.table.insertRow(row)
            
            self.table.setItem(row, 0, QTableWidgetItem(form["form_id"]))
            self.table.setItem(row, 1, QTableWidgetItem(form["dt_str"]))
            self.table.setItem(row, 2, QTableWidgetItem(form["instrument_name"]))
            self.table.setItem(row, 3, QTableWidgetItem(form["lot_number"]))
            
            count_item = QTableWidgetItem(f"共 {form['item_count']} 項")
            count_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 4, count_item)
            
            reason = form["change_reason"] or "未註記"
            self.table.setItem(row, 5, QTableWidgetItem(reason))
            self.table.setItem(row, 6, QTableWidgetItem(form["set_by_name"]))
            
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.table.cellDoubleClicked.connect(self._on_double_click)

    def _on_view_clicked(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇一筆資料")
            return
        row = selected[0].row()
        self._on_double_click(row, 0)

    def _on_double_click(self, row, col):
        form = self.grouped_forms[row]
        self._show_detail(form)

    def _show_detail(self, form):
        dlg = QCTargetHistoryDetailDialog(self, form["form_id"], form["dt_str"], form["items"])
        dlg.exec()

    def _print_report(self):
        if self.table.rowCount() == 0:
            QMessageBox.warning(self, "錯誤", "目前無資料可列印")
            return
            
        path, _ = QFileDialog.getSaveFileName(self, "匯出 PDF", f"品管範圍修訂查詢_{self.user['user_id']}.pdf", "PDF (*.pdf)")
        if not path: return
        
        rows_html = ""
        for r in range(self.table.rowCount()):
            form_id = self.table.item(r, 0).text()
            dt_str = self.table.item(r, 1).text()
            inst = self.table.item(r, 2).text()
            lot = self.table.item(r, 3).text()
            cnt = self.table.item(r, 4).text()
            reason = self.table.item(r, 5).text()
            modifier = self.table.item(r, 6).text()
            
            rows_html += f"""
            <tr>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{form_id}</td>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{dt_str}</td>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{inst}</td>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{lot}</td>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{cnt}</td>
                <td style='border: 1px solid #000; padding: 4px;'>{reason}</td>
                <td style='border: 1px solid #000; padding: 4px; text-align: center;'>{modifier}</td>
            </tr>
            """
            
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: sans-serif; font-size: 12px; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 20px; border: 1px solid #000; }}
                th {{ border: 1px solid #000; background-color: #eee; padding: 6px; text-align: center; font-size: 12px; }}
                td {{ font-size: 12px; border: 1px solid #000; }}
                h2 {{ text-align: center; font-size: 16px; margin-bottom: 5px; }}
            </style>
        </head>
        <body>
            <h2>品管範圍修訂紀錄表</h2>
            <table>
                <thead>
                    <tr>
                        <th width="18%">修改單號</th>
                        <th width="18%">修訂時間</th>
                        <th width="8%">儀器名稱</th>
                        <th width="12%">批號</th>
                        <th width="8%">異動項目</th>
                        <th width="26%">變更原因</th>
                        <th width="10%">修訂者</th>
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
        doc.setDocumentMargin(10)
        
        printer = QPrinter(QPrinter.PrinterMode.ScreenResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        printer.setPageMargins(QMarginsF(8, 10, 8, 10), QPageLayout.Unit.Millimeter)
        
        doc.print(printer)
        QMessageBox.information(self, "匯出成功", f"PDF 已成功匯出至：\n{path}")
