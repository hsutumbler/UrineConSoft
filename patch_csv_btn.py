with open('ui/inquiry/comprehensive_inquiry.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re

# Add button
btn_code = """        self.btn_print = QPushButton("列印 / 匯出 PDF")
        self.btn_print.setProperty("class", "grid_btn")
        self.btn_print.clicked.connect(self._do_print)
        
        self.btn_export_csv = QPushButton("匯出 CSV")
        self.btn_export_csv.setProperty("class", "grid_btn")
        self.btn_export_csv.clicked.connect(self._do_export_csv)"""
code = code.replace('        self.btn_print = QPushButton("列印 / 匯出 PDF")\n        self.btn_print.setProperty("class", "grid_btn")\n        self.btn_print.clicked.connect(self._do_print)', btn_code)

code = code.replace('        right_vbox.addWidget(self.btn_print)', '        right_vbox.addWidget(self.btn_print)\n        right_vbox.addWidget(self.btn_export_csv)')

# Toggle visibility
# 0: Raw QC (show)
code = code.replace('        if idx == 0:  # Raw QC\n', '        if idx == 0:  # Raw QC\n            self.btn_export_csv.setVisible(True)\n')
# 1, 2, 3, 4, 5: Hide
for i in range(1, 6):
    code = re.sub(rf'(        elif idx == {i}:.*?)(?=\n        el|\n\n)', rf'\1\n            self.btn_export_csv.setVisible(False)', code, flags=re.DOTALL)

# Add _do_export_csv
do_export = """    def _do_export_csv(self):
        idx = self.cmb_type.currentIndex()
        if idx == 0:
            self.page_raw_qc._export_csv()
"""
code = code.replace('    def _do_print(self):', do_export + '\n    def _do_print(self):')

with open('ui/inquiry/comprehensive_inquiry.py', 'w', encoding='utf-8') as f:
    f.write(code)
