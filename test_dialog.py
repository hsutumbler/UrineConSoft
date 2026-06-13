import sys, traceback
from PyQt6.QtWidgets import QApplication
from ui.inquiry.report_inquiry import ReportDetailDialog
from datetime import date
from services.inquiry_service import InquiryService

app = QApplication(sys.argv)
try:
    dlg = ReportDetailDialog(None, {}, date(2026, 5, 12), date(2026, 6, 11), "1", "UQC_0610_01", "77Urine")
    print("Success")
except Exception as e:
    with open("error.log", "w") as f:
        f.write(traceback.format_exc())
    print("Failed")
