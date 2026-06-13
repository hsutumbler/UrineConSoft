with open('ui/inquiry/report_inquiry.py', 'r') as f:
    code = f.read()

import re
new_view = """    def _on_view_clicked(self):
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
            dlg = ReportDetailDialog(self, self.user, self.d_from, self.d_to, b["instrument_id"], b["lot_number"], b["instrument_name"])
            dlg.exec()
        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            QMessageBox.critical(self, "發生錯誤", f"開啟報表檢視時發生錯誤:\\n{err_msg}")
"""
code = re.sub(r'    def _on_view_clicked\(self\):.*?        self\._on_view_clicked\(\)', new_view + "\n\n    def _print_report(self):\n        self._on_view_clicked()", code, flags=re.DOTALL)

with open('ui/inquiry/report_inquiry.py', 'w') as f:
    f.write(code)
