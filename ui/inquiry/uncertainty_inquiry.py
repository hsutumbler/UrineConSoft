from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QDateEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
from ui.base_page import PAGE_STYLE
from services.inquiry_service import InquiryService
from services.qc_service import MasterService

class UncertaintyInquiryPage(QWidget):
    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setStyleSheet(PAGE_STYLE)
        self._build_ui()
        self._load_instruments()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        header = QVBoxLayout()
        title = QLabel("量測不確定度評估")
        title.setObjectName("page_title")
        subtitle = QLabel("計算定量項目的偏差 (Bias) 與量測不確定度 (U)")
        subtitle.setObjectName("page_subtitle")
        header.addWidget(title)
        header.addWidget(subtitle)
        layout.addLayout(header)

        # Filters
        filter_bar = QHBoxLayout()
        
        filter_bar.addWidget(QLabel("儀器："))
        self.cmb_inst = QComboBox()
        self.cmb_inst.currentIndexChanged.connect(self._load_data)
        filter_bar.addWidget(self.cmb_inst)
        
        filter_bar.addSpacing(20)
        
        filter_bar.addWidget(QLabel("評估區間："))
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-6))
        self.date_from.dateChanged.connect(self._load_data)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self._load_data)
        
        filter_bar.addWidget(self.date_from)
        filter_bar.addWidget(QLabel(" ~ "))
        filter_bar.addWidget(self.date_to)
        
        filter_bar.addSpacing(20)
        filter_bar.addWidget(QLabel("批號："))
        self.cmb_lot = QComboBox()
        self.cmb_lot.addItem("全部")
        self.cmb_lot.currentIndexChanged.connect(self._load_data)
        filter_bar.addWidget(self.cmb_lot)
        
        filter_bar.addStretch()
        
        layout.addLayout(filter_bar)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "參數", "Level", "批號", "N", "Mean", "CV%", "Target Mean", "Bias%", "TEa%", "U (k=2)", "評估結果"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

    def _load_instruments(self):
        self.cmb_inst.blockSignals(True)
        self.cmb_inst.clear()
        insts = MasterService.get_instruments()
        for i in insts:
            self.cmb_inst.addItem(i["instrument_name"], i["instrument_id"])
        self.cmb_inst.blockSignals(False)
        self._load_lots()
        self._load_data()

    def _load_lots(self):
        from services.qc_service import QCBatchService
        self.cmb_lot.blockSignals(True)
        self.cmb_lot.clear()
        self.cmb_lot.addItem("全部")
        batches = QCBatchService.get_all()
        seen = set()
        for b in batches:
            if b["lot_number"] not in seen:
                seen.add(b["lot_number"])
                self.cmb_lot.addItem(b["lot_number"])
        self.cmb_lot.blockSignals(False)

    def _load_data(self):
        inst_id = self.cmb_inst.currentData()
        if not inst_id:
            self.table.setRowCount(0)
            return
            
        from_d = self.date_from.date().toPyDate()
        to_d = self.date_to.date().toPyDate()
        lot = self.cmb_lot.currentText()
        
        records = InquiryService.get_measurement_uncertainty(from_d, to_d, inst_id, lot)
        
        self.table.setRowCount(0)
        for r, rec in enumerate(records):
            self.table.insertRow(r)
            
            param = rec["reagent_name"]
            lvl = rec["level_name"]
            lot = rec["lot_number"]
            n = str(rec["n"])
            rname = rec["reagent_name"]
            dec = 3 if rname == "SG" else (1 if rname in ("RBC", "WBC") else 2)
            
            mean = f"{rec['mean']:.{dec}f}"
            cv = f"{rec['cv']:.2f}"
            
            tm = f"{rec['tm']:.{dec}f}" if rec["tm"] is not None else "未設定"
            bias = f"{rec['bias_pct']:.2f}" if rec["bias_pct"] is not None else "—"
            tea = f"{rec['tea']:.2f}" if rec["tea"] is not None else "未設定"
            
            u_exp = f"{rec['u_expanded']:.2f}" if rec["u_expanded"] is not None else "—"
            
            eval_result = "—"
            if rec["u_expanded"] is not None and rec["tea"] is not None:
                if rec["u_expanded"] <= rec["tea"]:
                    eval_result = "✅ 符合 (U ≤ TEa)"
                else:
                    eval_result = "❌ 不符合"

            vals = [param, lvl, lot, n, mean, cv, tm, bias, tea, u_exp, eval_result]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(v)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 10 and "❌" in eval_result:
                    item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(r, c, item)

    def on_page_show(self):
        self._load_instruments()
