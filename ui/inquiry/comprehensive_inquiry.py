import sys
from datetime import datetime, date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QStackedWidget, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt, QDate

from ui.base_page import BasePage, PAGE_STYLE, COLORS
from services.qc_service import MasterService
from services.inquiry_service import InquiryService

from ui.inquiry.raw_qc_inquiry import RawQCInquiryPage
from ui.inquiry.reagent_inquiry import ReagentInquiryPage
from ui.inquiry.qc_inquiry import QCInquiryPage
from ui.inquiry.report_inquiry import ReportInquiryPage
from ui.inquiry.anomaly_inquiry import AnomalyInquiryPage

class ComprehensiveInquiryPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("綜合查詢", "整合各項數據、報表與異常紀錄之查詢", user)
        self._build_ui()
        self._load_master_data()
        self._on_type_changed()

    def _build_ui(self):
        filter_layout = QVBoxLayout()
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("查詢種類："))
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["品管數據查詢", "試劑允收查詢", "品管液允收查詢", "品管報表", "異常紀錄查詢"])
        self.cmb_type.setMinimumWidth(150)
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        row1.addWidget(self.cmb_type)
        
        row1.addSpacing(20)
        row1.addWidget(QLabel("日期區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy/MM/dd")
        self.date_from.setMinimumWidth(120)
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy/MM/dd")
        self.date_to.setMinimumWidth(120)
        self.date_to.setDate(QDate.currentDate())
        
        row1.addWidget(self.date_from)
        row1.addWidget(QLabel(" ~ "))
        row1.addWidget(self.date_to)
        
        row1.addSpacing(20)
        
        self.lbl_dynamic = QLabel("選擇儀器：")
        row1.addWidget(self.lbl_dynamic)
        self.cmb_dynamic = QComboBox()
        self.cmb_dynamic.setMinimumWidth(120)
        self.cmb_dynamic.currentIndexChanged.connect(self._on_dynamic_changed)
        row1.addWidget(self.cmb_dynamic)
        
        row1.addSpacing(20)
        self.lbl_lot = QLabel("批號：")
        row1.addWidget(self.lbl_lot)
        self.cmb_lot = QComboBox()
        self.cmb_lot.setMinimumWidth(150)
        self.cmb_lot.addItem("全部")
        row1.addWidget(self.cmb_lot)
        
        row1.addStretch()
        filter_layout.addLayout(row1)
        
        row2 = QHBoxLayout()
        row2.addStretch()
        btn_query = QPushButton("🔍 查詢")
        btn_query.setObjectName("btn_primary")
        btn_query.setMinimumWidth(100)
        btn_query.clicked.connect(self._do_query)
        row2.addWidget(btn_query)
        
        self.btn_view = QPushButton("檢視")
        self.btn_view.setMinimumWidth(80)
        self.btn_view.clicked.connect(self._do_view)
        row2.addWidget(self.btn_view)
        
        # We handle printing via the subpages since they already have their own print methods.
        self.btn_print = QPushButton("列印 / 匯出 PDF")
        self.btn_print.setMinimumWidth(150)
        self.btn_print.clicked.connect(self._do_print)
        row2.addWidget(self.btn_print)
        row2.addStretch()
        filter_layout.addLayout(row2)
        
        self.content_layout.addLayout(filter_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ccc; margin-top: 10px; margin-bottom: 10px;")
        self.content_layout.addWidget(line)
        
        # Stacked Widget for subpages
        self.stack = QStackedWidget()
        
        # Instantiate subpages with hide_filters=True
        self.page_raw_qc = RawQCInquiryPage(self.user, is_subpage=True)
        self.page_reagent = ReagentInquiryPage(self.user, is_subpage=True)
        self.page_qc = QCInquiryPage(self.user, is_subpage=True)
        self.page_report = ReportInquiryPage(self.user, is_subpage=True)
        self.page_anomaly = AnomalyInquiryPage(self.user, is_subpage=True)
        
        for p in [self.page_raw_qc, self.page_reagent, self.page_qc, self.page_report, self.page_anomaly]:
            # hide their default title and subtitle using the header_widget we created
            if hasattr(p, 'header_widget'):
                p.header_widget.hide()
            self.stack.addWidget(p)
            
        self.content_layout.addWidget(self.stack, 1)

    def _load_master_data(self):
        self.instruments = MasterService.get_instruments()
        self.reagents = MasterService.get_reagents()
        
    def _on_type_changed(self):
        idx = self.cmb_type.currentIndex()
        self.stack.setCurrentIndex(idx)
        
        self.cmb_dynamic.blockSignals(True)
        self.cmb_lot.blockSignals(True)
        self.cmb_dynamic.clear()
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        
        if idx == 0 or idx == 3:  # Raw QC & QC Report
            self.lbl_dynamic.setText("選擇儀器：")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setVisible(True)
            self.cmb_lot.setVisible(True)
            self.btn_view.setVisible(False)
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
        elif idx == 1:  # Reagent Acceptance
            self.lbl_dynamic.setVisible(False)
            self.cmb_dynamic.setVisible(False)
            self.lbl_lot.setVisible(True)
            self.cmb_lot.setVisible(True)
            self.btn_view.setVisible(True)
                
        elif idx == 2:  # QC Acceptance
            self.lbl_dynamic.setVisible(False)
            self.cmb_dynamic.setVisible(False)
            self.lbl_lot.setVisible(False)
            self.cmb_lot.setVisible(False)
            self.btn_view.setVisible(True)
            
        elif idx == 4:  # Anomaly Records
            self.lbl_dynamic.setText("選擇儀器：")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setVisible(False)
            self.cmb_lot.setVisible(False)
            self.btn_view.setVisible(True)
            self.cmb_dynamic.addItem("全部儀器", None)
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
        self.cmb_dynamic.blockSignals(False)
        self.cmb_lot.blockSignals(False)
        self._on_dynamic_changed()

    def _on_dynamic_changed(self):
        idx = self.cmb_type.currentIndex()
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        
        if idx == 0 or idx == 3:  # Raw QC & QC Report
            inst = self.cmb_dynamic.currentData()
            if inst:
                # fetch QC batches for this instrument?
                # Using QCBatchService.get_batches() 
                from services.qc_service import QCBatchService
                batches = QCBatchService.get_all()
                # Simplified: just show all active/recent QC batches
                for b in batches:
                    self.cmb_lot.addItem(f"{b['lot_number']} ({b['level_name']})", b)
                    
        elif idx == 1:  # Reagent Acceptance
            from services.qc_service import ReagentBatchService
            batches = ReagentBatchService.get_all()
            seen = set()
            for b in batches:
                if b["lot_number"] not in seen:
                    seen.add(b["lot_number"])
                    self.cmb_lot.addItem(b["lot_number"], b)
                    
        self.cmb_lot.blockSignals(False)

    def _do_query(self):
        idx = self.cmb_type.currentIndex()
        d_from = self.date_from.date().toPyDate()
        d_to = self.date_to.date().toPyDate()
        
        if idx == 0:
            inst = self.cmb_dynamic.currentData()
            lot = self.cmb_lot.currentData()
            self.page_raw_qc.execute_query(d_from, d_to, inst, lot)
        elif idx == 1:
            lot = self.cmb_lot.currentData()
            self.page_reagent.execute_query(d_from, d_to, None, lot)
        elif idx == 2:
            self.page_qc.execute_query(d_from, d_to)
        elif idx == 3:
            inst = self.cmb_dynamic.currentData()
            lot = self.cmb_lot.currentData()
            self.page_report.execute_query(d_from, d_to, inst, lot)
        elif idx == 4:
            inst = self.cmb_dynamic.currentData()
            self.page_anomaly.execute_query(d_from, d_to, inst)

    def _do_view(self):
        idx = self.cmb_type.currentIndex()
        if idx == 1:
            self.page_reagent._on_view_clicked()
        elif idx == 2:
            self.page_qc._on_view_clicked()
        elif idx == 4:
            self.page_anomaly._on_view_clicked()

    def _do_print(self):
        idx = self.cmb_type.currentIndex()
        if idx == 0:
            self.page_raw_qc._print_report()
        elif idx == 1:
            self.page_reagent._print_report()
        elif idx == 2:
            self.page_qc._print_report()
        elif idx == 3:
            self.page_report._print_report()
        elif idx == 4:
            self.page_anomaly._print_report()
