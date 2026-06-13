with open('ui/inquiry/report_inquiry.py', 'r') as f:
    code = f.read()

new_view = """    def _on_view_clicked(self):
        print("View clicked!")
        selected = self.table.selectedItems()
        print(f"Selected items: {len(selected)}")
        if not selected:
            QMessageBox.warning(self, "提示", "請先選擇一個批號。")
            return
            
        row = selected[0].row()
        item = self.table.item(row, 0)
        print(f"Row: {row}, item: {item}")
        if not item: return
        
        b = item.data(Qt.ItemDataRole.UserRole)
        print(f"b: {b}")
        if not b: return
        
        try:
            dlg = ReportDetailDialog(self, self.user, self.d_from, self.d_to, b["instrument_id"], b["lot_number"], b["instrument_name"])
            print("Dialog instantiated")
            dlg.exec()
            print("Dialog closed")
        except Exception as e:
            print(f"Error showing dialog: {e}")
            import traceback
            traceback.print_exc()
"""

# Replace the original _on_view_clicked
import re
code = re.sub(r'    def _on_view_clicked\(self\):.*?        dlg\.exec\(\)', new_view, code, flags=re.DOTALL)

with open('ui/inquiry/report_inquiry.py', 'w') as f:
    f.write(code)
