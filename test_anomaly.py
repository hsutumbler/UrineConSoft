import sys
import datetime
from PyQt6.QtWidgets import QApplication
from ui.inquiry.comprehensive_inquiry import ComprehensiveInquiryPage

app = QApplication(sys.argv)
page = ComprehensiveInquiryPage({})

d_from = datetime.date(2026, 5, 1)
d_to = datetime.date(2026, 6, 8)
# Simulate selecting Anomaly Records (idx 4)
page.cmb_type.setCurrentIndex(4)
# Simulate clicking query
page._do_query()

print("Anomaly table row count:", page.page_anomaly.table.rowCount())
