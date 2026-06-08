with open("ui/qc/reagent_batch.py", "r") as f:
    content = f.read()

import re

# In AcceptanceDialog.__init__, we have:
#         self.table = QTableWidget(0, 7)
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

pattern = r"        self\.table\.horizontalHeader\(\)\.setSectionResizeMode\(QHeaderView\.ResizeMode\.Stretch\)"
replacement = """        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)"""

content = re.sub(pattern, replacement, content)

with open("ui/qc/reagent_batch.py", "w") as f:
    f.write(content)
