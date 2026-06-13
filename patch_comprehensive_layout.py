with open("ui/inquiry/comprehensive_inquiry.py", "r", encoding="utf-8") as f:
    c = f.read()

import re

old_block = """        # Query Button
        btn_query = QPushButton("查  詢")
        btn_query.setProperty("class", "grid_btn_primary")
        btn_query.clicked.connect(self._do_query)
        main_hbox.addWidget(btn_query)
        
        # Right Buttons
        right_vbox = QVBoxLayout()
        right_vbox.setSpacing(4)
        right_vbox.setContentsMargins(0, 0, 0, 0)
        
        self.btn_view = QPushButton("檢  視")
        self.btn_view.setProperty("class", "grid_btn")
        self.btn_view.clicked.connect(self._do_view)
        
        self.btn_print = QPushButton("列印 / 匯出 PDF")
        self.btn_print.setProperty("class", "grid_btn")
        self.btn_print.clicked.connect(self._do_print)
        
        self.btn_export_csv = QPushButton("匯出 CSV")
        self.btn_export_csv.setProperty("class", "grid_btn")
        self.btn_export_csv.clicked.connect(self._do_export_csv)
        
        right_vbox.addWidget(self.btn_view)
        right_vbox.addWidget(self.btn_print)
        right_vbox.addWidget(self.btn_export_csv)
        
        main_hbox.addLayout(right_vbox)"""

new_block = """        # Right Buttons
        right_hbox = QHBoxLayout()
        right_hbox.setSpacing(4)
        right_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.btn_query = QPushButton("查  詢")
        self.btn_query.setProperty("class", "grid_btn_primary")
        self.btn_query.clicked.connect(self._do_query)
        
        self.btn_view = QPushButton("檢  視")
        self.btn_view.setProperty("class", "grid_btn_primary")
        self.btn_view.clicked.connect(self._do_view)
        
        self.btn_print = QPushButton("列印 / 匯出 PDF")
        self.btn_print.setProperty("class", "grid_btn_primary")
        self.btn_print.clicked.connect(self._do_print)
        
        self.btn_export_csv = QPushButton("匯出 CSV")
        self.btn_export_csv.setProperty("class", "grid_btn_primary")
        self.btn_export_csv.clicked.connect(self._do_export_csv)
        
        right_hbox.addWidget(self.btn_query)
        right_hbox.addWidget(self.btn_view)
        right_hbox.addWidget(self.btn_print)
        right_hbox.addWidget(self.btn_export_csv)
        
        main_hbox.addLayout(right_hbox)"""

if old_block in c:
    c = c.replace(old_block, new_block)
else:
    print("Warning: old_block not found!")

with open("ui/inquiry/comprehensive_inquiry.py", "w", encoding="utf-8") as f:
    f.write(c)
