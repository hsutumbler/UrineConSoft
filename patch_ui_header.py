import re

with open("ui/qc/reagent_batch.py", "r") as f:
    content = f.read()

# Replace table initialization
table_init_old = """        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels([
            "項目", 
            "Level 1 現有", "Level 1 新進", "Level 1 範圍", 
            "Level 2 現有", "Level 2 新進", "Level 2 範圍"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget { font-size: 14px; } QHeaderView::section { font-weight: bold; }")"""

table_init_new = """        self.table = QTableWidget(0, 7)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setStyleSheet("QTableWidget { font-size: 12px; }")"""

content = content.replace(table_init_old, table_init_new)

# Replace table update logic
update_old = """        reagents = MasterService.get_reagents()
        self.table.setRowCount(0)
        
        self._snapshot_data = {"""

update_new = """        reagents = MasterService.get_reagents()
        self.table.setRowCount(0)
        
        # 建立兩層式的 Header (Row 0 & Row 1)
        self.table.insertRow(0)
        
        h0_0 = QTableWidgetItem("項目")
        h0_0.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_0.setBackground(QColor("#f0f0f0"))
        h0_0.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 0, h0_0)
        self.table.setSpan(0, 0, 2, 1)
        
        h0_1 = QTableWidgetItem("Level 1")
        h0_1.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_1.setBackground(QColor("#f0f0f0"))
        h0_1.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 1, h0_1)
        self.table.setSpan(0, 1, 1, 3)
        
        h0_4 = QTableWidgetItem("Level 2")
        h0_4.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        h0_4.setBackground(QColor("#f0f0f0"))
        h0_4.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.table.setItem(0, 4, h0_4)
        self.table.setSpan(0, 4, 1, 3)
        
        self.table.insertRow(1)
        sub_headers = ["現有", "新進", "合格範圍", "現有", "新進", "合格範圍"]
        for i, h in enumerate(sub_headers):
            it = QTableWidgetItem(h)
            it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            it.setBackground(QColor("#f0f0f0"))
            it.setFont(QFont("Arial", 12, QFont.Weight.Bold))
            self.table.setItem(1, i + 1, it)
        
        row_idx = 2
        
        self._snapshot_data = {"""

content = content.replace(update_old, update_new)

# Replace the row insertion
row_ins_old = """            self.table.insertRow(r)
            
            vals = [
                reagent["reagent_label"],
                a_l1, n_l1, t_l1,
                a_l2, n_l2, t_l2
            ]"""

row_ins_new = """            self.table.insertRow(row_idx)
            
            vals = [
                reagent["reagent_name"],
                a_l1, n_l1, t_l1,
                a_l2, n_l2, t_l2
            ]"""

content = content.replace(row_ins_old, row_ins_new)

# Replace table.setItem index
item_old = """                self.table.setItem(r, c, item)"""
item_new = """                self.table.setItem(row_idx, c, item)
            row_idx += 1"""

content = content.replace(item_old, item_new)

with open("ui/qc/reagent_batch.py", "w") as f:
    f.write(content)
