import sys
from PyQt6.QtWidgets import QApplication
from ui.inquiry.comprehensive_inquiry import ComprehensiveInquiryPage

app = QApplication(sys.argv)
page = ComprehensiveInquiryPage({})
print("Is raw_qc header_widget hidden?", page.page_raw_qc.header_widget.isHidden())
