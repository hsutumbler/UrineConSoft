def replace_file(filepath, replacements):
    with open(filepath, 'r', encoding='utf-8') as f:
        c = f.read()
    for old, new in replacements:
        c = c.replace(old, new)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(c)

# 1. reagent_batch.py (ReagentBatchAcceptanceDialog read_only section)
r1 = [
    (
        '        btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")\n        btn_print.clicked.connect(self._print_pdf)\n        \n        if self.read_only:\n            btn_close = QPushButton("關閉")\n            btn_close.clicked.connect(self.accept)\n            btn_layout.addWidget(btn_print)\n            btn_layout.addStretch()\n            btn_layout.addWidget(btn_close)',
        '''        if self.read_only:
            btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
            btn_print.setObjectName("btn_primary")
            btn_print.clicked.connect(self._print_pdf)
            btn_close = QPushButton("關閉")
            btn_close.clicked.connect(self.accept)
            btn_layout.addStretch()
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_close)'''
    )
]
replace_file("ui/qc/reagent_batch.py", r1)

# 2. qc_batch.py (QC Batch target history dialog?)
# Wait, qc_batch.py has two sections we might need to fix:
# _load_data in QCBatchAcceptanceDialog (read_only section) and TargetHistoryDialog
r2 = [
    (
        '''        if self.read_only:
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setStyleSheet("background-color: #FFF3E0; color: #E65100; border: 1px solid #FFCC80; border-radius: 4px; padding: 8px 24px; font-weight: bold;")
            btn_export.clicked.connect(self._export_pdf)
            btn_row.addWidget(btn_export)

            btn_close = QPushButton("關閉")
            btn_close.setStyleSheet("background-color: #E6F7FF; color: #0056B3; border: 1px solid #91D5FF; border-radius: 4px; padding: 8px 24px; font-weight: bold;")
            btn_close.clicked.connect(self.accept)
            btn_row.addWidget(btn_close)''',
        '''        if self.read_only:
            btn_export = QPushButton("🖨️ 列印 / 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            btn_close = QPushButton("關閉")
            btn_close.clicked.connect(self.accept)
            
            btn_row.addWidget(btn_export)
            btn_row.addWidget(btn_close)'''
    )
]
replace_file("ui/qc/qc_batch.py", r2)

# 3. report_inquiry.py
r3 = [
    (
        '''        btn_layout = QHBoxLayout()
        btn_print = QPushButton("列印 / 匯出 PDF")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_close)
        btn_layout.addWidget(btn_print)''',
        '''        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_print = QPushButton("🖨️ 列印 / 匯出 PDF")
        btn_print.setObjectName("btn_primary")
        btn_print.clicked.connect(self._print_report)
        
        btn_close = QPushButton("關閉")
        btn_close.clicked.connect(self.accept)
        
        btn_layout.addWidget(btn_print)
        btn_layout.addWidget(btn_close)'''
    )
]
replace_file("ui/inquiry/report_inquiry.py", r3)

# 4. anomaly_dialog.py (AnomalyRecordDialog read_only section)
r4 = [
    (
        '''        else:
            btn_print = QPushButton("🖨️ 列印紀錄")
            btn_print.clicked.connect(self._print_record)
            
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_export)''',
        '''        else:
            btn_print = QPushButton("🖨️ 列印紀錄")
            btn_print.clicked.connect(self._print_record)
            
            btn_export = QPushButton("💾 匯出 PDF")
            btn_export.setObjectName("btn_primary")
            btn_export.clicked.connect(self._export_pdf)
            
            # Since cancel/close is already on the left, we need to re-arrange:
            # wait, btn_cancel is already added to btn_layout
            btn_layout.addWidget(btn_print)
            btn_layout.addWidget(btn_export)'''
    )
]
# Wait, AnomalyRecordDialog adds stretch and cancel first!
# Let's see how anomaly_dialog.py builds buttons.
# btn_layout = QHBoxLayout()
# btn_layout.addStretch()
# btn_layout.addWidget(btn_cancel)
# if not is_readonly: btn_layout.addWidget(btn_save)
# else: btn_layout.addWidget(btn_print); btn_layout.addWidget(btn_export)
# So it's Stretch -> Close -> Print -> Export! We need Stretch -> Print -> Export -> Close!
