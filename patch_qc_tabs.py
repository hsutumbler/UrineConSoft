with open("ui/qc/qc_batch.py", "r") as f:
    content = f.read()

# Replace QScrollArea with QTabWidget in QCAcceptanceDialog init
old_init = """        # Scroll area for tables
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)"""

new_init = """        # Tab Widget for tables
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)"""

content = content.replace(old_init, new_init)

# Replace the layout clearing in _refresh_stats
old_refresh = """    def _refresh_stats(self):
        # clear previous UI
        while self.scroll_layout.count():
            item = self.scroll_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()"""

new_refresh = """    def _refresh_stats(self):
        # clear previous tabs
        self.tabs.clear()"""

content = content.replace(old_refresh, new_refresh)

# Replace the adding of groups to scroll_layout with tabs
old_qual = """        l_qual.addWidget(t_qual)
        self.scroll_layout.addWidget(grp_qual)"""
new_qual = """        l_qual.addWidget(t_qual)
        
        qual_tab = QWidget()
        qual_layout = QVBoxLayout(qual_tab)
        qual_layout.setContentsMargins(12, 12, 12, 12)
        qual_layout.addWidget(grp_qual)
        self.tabs.addTab(qual_tab, "定性 / 半定量")"""
content = content.replace(old_qual, new_qual)

old_quant = """        l_quant.addWidget(t_quant)
        self.scroll_layout.addWidget(grp_quant)"""
new_quant = """        l_quant.addWidget(t_quant)
        
        quant_tab = QWidget()
        quant_layout = QVBoxLayout(quant_tab)
        quant_layout.setContentsMargins(12, 12, 12, 12)
        quant_layout.addWidget(grp_quant)
        self.tabs.addTab(quant_tab, "定量 / 目標值設定")"""
content = content.replace(old_quant, new_quant)

with open("ui/qc/qc_batch.py", "w") as f:
    f.write(content)
