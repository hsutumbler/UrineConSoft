with open("ui/inquiry/report_inquiry.py", "r", encoding="utf-8") as f:
    c = f.read()

# Remove the top button
c = c.replace('''        btn_print = QPushButton("列印")
        btn_print.setMinimumWidth(150)
        btn_print.clicked.connect(self._print_report)
        top.addWidget(btn_print)''', '')

# Add bottom buttons
new_bottom = '''        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_print = QPushButton("🖨️ 列印")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)'''

# We add it at the end of __init__
# find def _build_table_headers(self): and insert before it
import re
c = re.sub(r'(\n\s+def _load_data\(self\):)', new_bottom + r'\1', c)

with open("ui/inquiry/report_inquiry.py", "w", encoding="utf-8") as f:
    f.write(c)


# For anomaly_dialog.py
with open("ui/qc/anomaly_dialog.py", "r", encoding="utf-8") as f:
    c = f.read()

c = c.replace('''        else:
            btn_print = QPushButton("🖨️ 列印紀錄")
            btn_print.clicked.connect(self._print_record)
            
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_export)
            btn_layout.addWidget(btn_cancel)''',
'''        else:
            btn_print = QPushButton("🖨️ 列印")
            btn_print.setObjectName("btn_primary")
            btn_print.clicked.connect(self._print_record)
            
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_cancel)''')

with open("ui/qc/anomaly_dialog.py", "w", encoding="utf-8") as f:
    f.write(c)

