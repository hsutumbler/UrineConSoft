with open("ui/qc/reagent_batch.py", "r") as f:
    content = f.read()

import re
# The broken part is in `_load`:
#             for c, v in enumerate(vals):
#                 item = QTableWidgetItem(v)
#                 item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
#                 if c == 0:
#                     item.setData(Qt.ItemDataRole.UserRole, b)
#                 self.table.setItem(row_idx, c, item)
#             row_idx += 1

pattern = r"""            for c, v in enumerate\(vals\):
                item = QTableWidgetItem\(v\)
                item\.setTextAlignment\(Qt\.AlignmentFlag\.AlignCenter\)
                if c == 0:
                    item\.setData\(Qt\.ItemDataRole\.UserRole, b\)
                self\.table\.setItem\(row_idx, c, item\)
            row_idx \+= 1"""

replacement = """            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, b)
                self.table.setItem(r, c, item)"""

content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

with open("ui/qc/reagent_batch.py", "w") as f:
    f.write(content)
