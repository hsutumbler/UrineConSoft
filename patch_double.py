with open('ui/inquiry/report_inquiry.py', 'r') as f:
    code = f.read()

import re
code = code.replace("self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)", "self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)\n        self.table.itemDoubleClicked.connect(self._on_view_clicked)")

with open('ui/inquiry/report_inquiry.py', 'w') as f:
    f.write(code)
