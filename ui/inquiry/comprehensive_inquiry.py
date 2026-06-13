import sys
from datetime import datetime, date

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QDateEdit, QPushButton, QStackedWidget, QMessageBox, QFrame, QGridLayout
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
from ui.inquiry.qc_target_history_inquiry import QCTargetHistoryInquiryPage

class ComprehensiveInquiryPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("綜合查詢", "整合各項數據、報表與異常紀錄之查詢", user)
        self._build_ui()
        self._load_master_data()
        self._on_type_changed()

    def _build_ui(self):
        # Traditional Dashboard Grid Style Filter
        grid_container = QFrame()
        grid_container.setObjectName("grid_bg")
        grid_container.setStyleSheet("""
            QFrame#grid_bg {
                background-color: #FDFBEC;
                border: 1px solid #E0D9C0;
                border-radius: 8px;
                padding: 10px;
                margin-bottom: 10px;
            }
            QLabel[class="grid_label"] {
                background-color: transparent;
                color: #6B6444;
                font-weight: bold;
                font-size: 13px;
                padding: 4px 10px;
            }
            QWidget#grid_inner {
                background-color: transparent;
            }
            QWidget[class="date_cell"] {
                background-color: transparent;
                border: none;
            }
            QPushButton[class="grid_btn_primary"] {
                background-color: #FFFFFF;
                border: 1.5px solid #E0D9C0;
                border-radius: 8px;
                font-size: 14px;
                color: #6B6444;
                font-weight: bold;
                min-width: 75px;
                min-height: 56px;
            }
            QPushButton[class="grid_btn_primary"]:hover { 
                background-color: #FFF8D6; 
                border-color: #9B7E23;
                color: #9B7E23;
            }
            QPushButton[class="grid_btn_primary"]:pressed { 
                background-color: #F0E8C0; 
            }
        """)

        main_hbox = QHBoxLayout(grid_container)
        main_hbox.setContentsMargins(5, 5, 5, 5)
        main_hbox.setSpacing(10)
        
        left_grid_widget = QWidget()
        left_grid_widget.setObjectName("grid_inner")
        self.left_grid = QGridLayout(left_grid_widget)
        self.left_grid.setSpacing(2)
        self.left_grid.setContentsMargins(0, 0, 0, 0)
        
        # Row 0
        lbl_type = QLabel("報表類別")
        lbl_type.setProperty("class", "grid_label")
        lbl_type.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.cmb_type = QComboBox()
        self.cmb_type.addItems(["品管數據查詢", "試劑允收查詢", "品管液允收查詢", "品管報表", "異常紀錄查詢", "品管範圍修訂查詢"])
        
        lbl_date = QLabel("日期區間")
        lbl_date.setProperty("class", "grid_label")
        lbl_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        date_cell = QWidget()
        date_cell.setProperty("class", "date_cell")
        date_lay = QHBoxLayout(date_cell)
        date_lay.setContentsMargins(2, 0, 2, 0)
        date_lay.setSpacing(2)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDisplayFormat("yyyy/MM/dd")
        self.date_from.setDate(QDate.currentDate().addDays(-30))
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDisplayFormat("yyyy/MM/dd")
        self.date_to.setDate(QDate.currentDate())
        
        date_lay.addWidget(self.date_from)
        date_lay.addWidget(QLabel("~"))
        date_lay.addWidget(self.date_to)
        
        self.left_grid.addWidget(lbl_type, 0, 0)
        self.left_grid.addWidget(self.cmb_type, 0, 1)
        self.left_grid.addWidget(lbl_date, 0, 2)
        self.left_grid.addWidget(date_cell, 0, 3)
        
        # Row 1 items
        self.lbl_dynamic = QLabel("選擇儀器")
        self.lbl_dynamic.setProperty("class", "grid_label")
        self.lbl_dynamic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cmb_dynamic = QComboBox()
        
        self.lbl_lot = QLabel("批號")
        self.lbl_lot.setProperty("class", "grid_label")
        self.lbl_lot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cmb_lot = QComboBox()
        self.cmb_lot.addItem("全部")
        
        self.left_grid.addWidget(self.lbl_dynamic, 1, 0)
        self.left_grid.addWidget(self.cmb_dynamic, 1, 1)
        self.left_grid.addWidget(self.lbl_lot, 1, 2)
        self.left_grid.addWidget(self.cmb_lot, 1, 3)
        
        self.left_grid.setColumnStretch(1, 1)
        self.left_grid.setColumnStretch(3, 1)
        
        main_hbox.addWidget(left_grid_widget)
        
        # Right Buttons
        right_hbox = QHBoxLayout()
        right_hbox.setSpacing(4)
        right_hbox.setContentsMargins(0, 0, 0, 0)
        
        self.btn_query = QPushButton("🔍 查 詢")
        self.btn_query.setProperty("class", "grid_btn_primary")
        self.btn_query.clicked.connect(self._do_query)
        
        self.btn_view = QPushButton("👁️ 檢 視")
        self.btn_view.setProperty("class", "grid_btn_primary")
        self.btn_view.clicked.connect(self._do_view)
        
        self.btn_print = QPushButton("🖨️ 列 印")
        self.btn_print.setProperty("class", "grid_btn_primary")
        self.btn_print.clicked.connect(self._do_print)
        
        self.btn_export_csv = QPushButton("📊 匯出 CSV")
        self.btn_export_csv.setProperty("class", "grid_btn_primary")
        self.btn_export_csv.clicked.connect(self._do_export_csv)
        
        right_hbox.addWidget(self.btn_query)
        right_hbox.addWidget(self.btn_view)
        right_hbox.addWidget(self.btn_print)
        right_hbox.addWidget(self.btn_export_csv)
        
        main_hbox.addLayout(right_hbox)
        main_hbox.addStretch()
        
        self.content_layout.addWidget(grid_container)
        
        # Wire up type changed after elements are created
        self.cmb_type.currentIndexChanged.connect(self._on_type_changed)
        self.date_from.dateChanged.connect(self._on_dynamic_changed)
        self.date_to.dateChanged.connect(self._on_dynamic_changed)
        
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #ccc; margin-top: 5px; margin-bottom: 5px;")
        self.content_layout.addWidget(line)
        
        # Stacked Widget for subpages
        self.stack = QStackedWidget()
        
        # Instantiate subpages with hide_filters=True
        self.page_raw_qc = RawQCInquiryPage(self.user, is_subpage=True)
        self.page_reagent = ReagentInquiryPage(self.user, is_subpage=True)
        self.page_qc = QCInquiryPage(self.user, is_subpage=True)
        self.page_report = ReportInquiryPage(self.user, is_subpage=True)
        self.page_anomaly = AnomalyInquiryPage(self.user, is_subpage=True)
        self.page_target_history = QCTargetHistoryInquiryPage(self.user, is_subpage=True)
        
        for p in [self.page_raw_qc, self.page_reagent, self.page_qc, self.page_report, self.page_anomaly, self.page_target_history]:
            # hide their default title and subtitle using the header_widget we created
            if hasattr(p, 'header_widget'):
                p.header_widget.hide()
            
            # Remove double padding inherited from BasePage
            p.layout().setContentsMargins(0, 0, 0, 0)
            if hasattr(p, 'content_layout'):
                p.content_layout.setContentsMargins(0, 0, 0, 0)
                
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
        
        if idx == 0:  # Raw QC
            self.btn_export_csv.setVisible(True)
            self.lbl_dynamic.setText("儀器名稱")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setText("品管批號")
            self.lbl_lot.setVisible(True)
            self.cmb_lot.setVisible(True)
            self.btn_view.setVisible(False)
            self.btn_print.setVisible(True)
            
            self.left_grid.addWidget(self.lbl_dynamic, 1, 0)
            self.left_grid.addWidget(self.cmb_dynamic, 1, 1)
            self.left_grid.addWidget(self.lbl_lot, 1, 2)
            self.left_grid.addWidget(self.cmb_lot, 1, 3)
            
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
        elif idx == 3:  # QC Report
            self.lbl_dynamic.setText("儀器名稱")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setVisible(False)
            self.cmb_lot.setVisible(False)
            self.btn_view.setVisible(True)
            self.btn_print.setVisible(False)
            
            self.left_grid.addWidget(self.lbl_dynamic, 1, 0)
            self.left_grid.addWidget(self.cmb_dynamic, 1, 1)
            
            self.cmb_dynamic.addItem("全部儀器", None)
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
                
            self.btn_export_csv.setVisible(False)
        elif idx == 1:  # Reagent Acceptance
            self.lbl_dynamic.setVisible(False)
            self.cmb_dynamic.setVisible(False)
            self.lbl_lot.setText("試劑名稱")
            self.lbl_lot.setVisible(True)
            self.cmb_lot.setVisible(True)
            self.btn_view.setVisible(True)
            self.btn_print.setVisible(True)
            
            # Move lot to the left to fill space
            self.left_grid.addWidget(self.lbl_lot, 1, 0)
            self.left_grid.addWidget(self.cmb_lot, 1, 1)
                
            self.btn_export_csv.setVisible(False)
        elif idx == 2:  # QC Acceptance
            self.lbl_dynamic.setVisible(False)
            self.cmb_dynamic.setVisible(False)
            self.lbl_lot.setVisible(False)
            self.cmb_lot.setVisible(False)
            self.btn_view.setVisible(True)
            self.btn_print.setVisible(True)
            
            self.btn_export_csv.setVisible(False)
        elif idx == 4:  # Anomaly Records
            self.lbl_dynamic.setText("儀器名稱")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setVisible(False)
            self.cmb_lot.setVisible(False)
            self.btn_view.setVisible(True)
            self.btn_print.setVisible(True)
            self.cmb_dynamic.addItem("全部儀器", None)
            
            self.left_grid.addWidget(self.lbl_dynamic, 1, 0)
            self.left_grid.addWidget(self.cmb_dynamic, 1, 1)
            
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
            self.btn_export_csv.setVisible(False)
        elif idx == 5:  # QC Target History
            self.lbl_dynamic.setText("儀器名稱")
            self.lbl_dynamic.setVisible(True)
            self.cmb_dynamic.setVisible(True)
            self.lbl_lot.setText("品管批號")
            self.lbl_lot.setVisible(True)
            self.cmb_lot.setVisible(True)
            self.btn_view.setVisible(True)
            self.btn_print.setVisible(True)
            
            self.left_grid.addWidget(self.lbl_dynamic, 1, 0)
            self.left_grid.addWidget(self.cmb_dynamic, 1, 1)
            self.left_grid.addWidget(self.lbl_lot, 1, 2)
            self.left_grid.addWidget(self.cmb_lot, 1, 3)
            
            for inst in self.instruments:
                self.cmb_dynamic.addItem(inst["instrument_name"], inst)
                
            self.btn_export_csv.setVisible(False)

        self.cmb_dynamic.blockSignals(False)
        self.cmb_lot.blockSignals(False)
        self._on_dynamic_changed()

    def _on_dynamic_changed(self):
        idx = self.cmb_type.currentIndex()
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        
        if idx in (0, 5):  # Raw QC, QC Target History
            inst = self.cmb_dynamic.currentData()
            if inst:
                from services.qc_service import QCBatchService
                from datetime import date
                batches = QCBatchService.get_all()
                d_from = self.date_from.date().toPyDate()
                d_to = self.date_to.date().toPyDate()
                
                seen_lots = set()
                for b in batches:
                    b_start = b["open_date"]
                    if not b_start:
                        b_start = b["created_at"].date() if b.get("created_at") else date.min
                    elif hasattr(b_start, 'date'):
                        b_start = b_start.date()
                        
                    b_end = b["expiry_date"]
                    if b_end and hasattr(b_end, 'date'):
                        b_end = b_end.date()
                    elif not b_end:
                        b_end = date.max
                    
                    if b_start <= d_to and b_end >= d_from:
                        for sub in b.get("sub_lots", []):
                            lot_str = f"{b['lot_number']} ({sub['level_name']})"
                            if lot_str not in seen_lots:
                                seen_lots.add(lot_str)
                                combined = dict(b)
                                combined.update(sub)
                                self.cmb_lot.addItem(lot_str, combined)
                    
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
            self.btn_export_csv.setVisible(False)
        elif idx == 2:
            self.page_qc.execute_query(d_from, d_to)
            self.btn_export_csv.setVisible(False)
        elif idx == 3:
            inst = self.cmb_dynamic.currentData()
            self.page_report.execute_query(d_from, d_to, inst, None)
            self.btn_export_csv.setVisible(False)
        elif idx == 4:
            inst = self.cmb_dynamic.currentData()
            self.page_anomaly.execute_query(d_from, d_to, inst)
            self.btn_export_csv.setVisible(False)
        elif idx == 5:
            inst = self.cmb_dynamic.currentData()
            lot = self.cmb_lot.currentData()
            self.page_target_history.execute_query(d_from, d_to, inst, lot)
            self.btn_export_csv.setVisible(False)

    def _do_view(self):
        idx = self.cmb_type.currentIndex()
        if idx == 1:
            self.page_reagent._on_view_clicked()
        elif idx == 2:
            self.page_qc._on_view_clicked()
            self.btn_export_csv.setVisible(False)
        elif idx == 3:
            self.page_report._on_view_clicked()
            self.btn_export_csv.setVisible(False)
        elif idx == 4:
            self.page_anomaly._on_view_clicked()
            self.btn_export_csv.setVisible(False)
        elif idx == 5:
            self.page_target_history._on_view_clicked()
            self.btn_export_csv.setVisible(False)

    def _do_export_csv(self):
        idx = self.cmb_type.currentIndex()
        if idx == 0:
            self.page_raw_qc._export_csv()

    def _do_print(self):
        idx = self.cmb_type.currentIndex()
        if idx == 0:
            self.page_raw_qc._print_report()
        elif idx == 1:
            self.page_reagent._print_report()
            self.btn_export_csv.setVisible(False)
        elif idx == 2:
            self.page_qc._print_report()
            self.btn_export_csv.setVisible(False)
        elif idx == 3:
            self.page_report._print_report()
            self.btn_export_csv.setVisible(False)
        elif idx == 4:
            self.page_anomaly._print_report()
            self.btn_export_csv.setVisible(False)
        elif idx == 5:
            self.page_target_history._print_report()
