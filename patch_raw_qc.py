with open('ui/inquiry/raw_qc_inquiry.py', 'r', encoding='utf-8') as f:
    code = f.read()

export_code = """
    def _export_csv(self):
        if not hasattr(self, 'current_data') or not self.current_data:
            QMessageBox.warning(self, "無資料", "沒有可匯出的資料。")
            return
            
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        path, _ = QFileDialog.getSaveFileName(self, "匯出 CSV", "品管數據.csv", "CSV (*.csv)")
        if not path: return
        
        try:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # Header
                headers = []
                for c in range(self.table.columnCount()):
                    headers.append(self.table.horizontalHeaderItem(c).text())
                writer.writerow(headers)
                
                # Data
                for r in range(self.table.rowCount()):
                    row_data = []
                    for c in range(self.table.columnCount()):
                        item = self.table.item(r, c)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
                    
            QMessageBox.information(self, "成功", f"CSV 已成功匯出至：\\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "錯誤", f"匯出失敗：{str(e)}")
"""

code = code.replace("    def _print_report(self):", export_code + "\n    def _print_report(self):")

with open('ui/inquiry/raw_qc_inquiry.py', 'w', encoding='utf-8') as f:
    f.write(code)
