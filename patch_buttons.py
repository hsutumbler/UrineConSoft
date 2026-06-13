import re

# 1. reagent_batch.py
with open("ui/qc/reagent_batch.py", "r", encoding="utf-8") as f:
    c = f.read()
c = re.sub(
    r'btn_print = QPushButton\("🖨️ 列印 / 匯出 PDF"\)\n\s+btn_print\.clicked\.connect\(self\._print_pdf\)\n\s+if self\.read_only:\n\s+btn_close = QPushButton\("關閉"\)\n\s+btn_close\.clicked\.connect\(self\.accept\)\n\s+btn_layout\.addWidget\(btn_print\)\n\s+btn_layout\.addStretch\(\)\n\s+btn_layout\.addWidget\(btn_close\)',
    r'''if self.read_only:
            btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
            btn_print.setObjectName("btn_primary")
            btn_print.clicked.connect(self._print_pdf)
            btn_close = QPushButton("關閉")
            btn_close.clicked.connect(self.accept)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_close)''',
    c
)
with open("ui/qc/reagent_batch.py", "w", encoding="utf-8") as f:
    f.write(c)

# 2. qc_batch.py
with open("ui/qc/qc_batch.py", "r", encoding="utf-8") as f:
    c = f.read()
c = re.sub(
    r'btn_export = QPushButton\("💾 匯出 PDF"\)\n\s+btn_export\.setStyleSheet\(".*?"\)\n\s+btn_export\.clicked\.connect\(self\._export_pdf\)\n\s+btn_row\.addWidget\(btn_export\)\n\n\s+btn_close = QPushButton\("關閉"\)\n\s+btn_close\.setStyleSheet\(".*?"\)\n\s+btn_close\.clicked\.connect\(self\.accept\)\n\s+btn_row\.addWidget\(btn_close\)',
    r'''btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
            btn_print.setObjectName("btn_primary")
            btn_print.clicked.connect(self._export_pdf)
            btn_close = QPushButton("關閉")
            btn_close.clicked.connect(self.accept)
            btn_row.addWidget(btn_print)
            btn_row.addWidget(btn_close)''',
    c
)
with open("ui/qc/qc_batch.py", "w", encoding="utf-8") as f:
    f.write(c)

# 3. report_inquiry.py
with open("ui/inquiry/report_inquiry.py", "r", encoding="utf-8") as f:
    c = f.read()
c = re.sub(
    r'btn_print = QPushButton\("列印 / 匯出 PDF"\)\n\s+btn_print\.setObjectName\("btn_primary"\)\n\s+btn_print\.clicked\.connect\(self\._print_report\)\n\n\s+btn_close = QPushButton\("關閉"\)\n\s+btn_close\.clicked\.connect\(self\.accept\)\n\s+btn_layout\.addWidget\(btn_close\)\n\s+btn_layout\.addWidget\(btn_print\)',
    r'''btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)

        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)''',
    c
)
with open("ui/inquiry/report_inquiry.py", "w", encoding="utf-8") as f:
    f.write(c)

# 4. anomaly_dialog.py
with open("ui/qc/anomaly_dialog.py", "r", encoding="utf-8") as f:
    c = f.read()
c = re.sub(
    r'btn_print = QPushButton\("🖨️ 列印紀錄"\)\n\s+btn_print\.clicked\.connect\(self\._print_record\)\n\s+btn_export = QPushButton\("💾 匯出 PDF"\)\n\s+btn_export\.setObjectName\("btn_primary"\)\n\s+btn_export\.clicked\.connect\(self\._export_pdf\)\n\s+btn_layout\.addWidget\(btn_print\)\n\s+btn_layout\.addWidget\(btn_export\)',
    r'''btn_print = QPushButton("🖨️ 列印紀錄")
            btn_print.clicked.connect(self._print_record)
            
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_export)''',
    c
)
with open("ui/qc/anomaly_dialog.py", "w", encoding="utf-8") as f:
    f.write(c)

# 5. target_history.py
with open("ui/target/target_history.py", "r", encoding="utf-8") as f:
    c = f.read()
c = re.sub(
    r'btn_print = QPushButton\("🖨️ 列印"\)\n\s+btn_print\.clicked\.connect\(self\._print_report\)\n\s+btn_close = QPushButton\("關閉"\)\n\s+btn_close\.clicked\.connect\(self\.accept\)\n\s+btn_layout\.addStretch\(\)\n\s+btn_layout\.addWidget\(btn_print\)\n\s+btn_layout\.addWidget\(btn_close\)',
    r'''btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)''',
    c
)
with open("ui/target/target_history.py", "w", encoding="utf-8") as f:
    f.write(c)
