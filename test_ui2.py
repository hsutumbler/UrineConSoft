import sys
from PyQt6.QtWidgets import QApplication
from ui.inquiry.comprehensive_inquiry import ComprehensiveInquiryPage

app = QApplication(sys.argv)
page = ComprehensiveInquiryPage({})
page.show()

# Print out children to see if the filter buttons exist
def dump(widget, level=0):
    indent = "  " * level
    name = widget.objectName() or str(type(widget))
    print(f"{indent}{name}")
    for c in widget.children():
        if hasattr(c, 'children'):
            dump(c, level + 1)

print("--- Dump of Comprehensive Inquiry ---")
# Just check if we can find multiple "🔍 查詢" buttons
from PyQt6.QtWidgets import QPushButton
btns = page.findChildren(QPushButton)
for b in btns:
    print("Button:", b.text(), "Parent:", type(b.parent()))

