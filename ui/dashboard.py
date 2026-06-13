# ui/dashboard.py — 儀表板

from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt
from ui.base_page import BasePage, COLORS
from services.qc_service import ReagentBatchService, QCBatchService, QCResultService
from database.connection import DBContext
from datetime import date


class DashboardPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("儀表板", "品管系統總覽", user)
        self._build()

    def _build(self):
        # 卡片列
        grid = QGridLayout()
        grid.setSpacing(16)

        self._card_reagent = self._make_card("試劑批號", "—", "🧪", COLORS["accent"])
        self._card_qc_l1   = self._make_card("品管液 Level 1", "—", "🧫", "#2A7A4A")
        self._card_qc_l2   = self._make_card("品管液 Level 2", "—", "🧫", "#1A5A8A")
        self._card_today   = self._make_card("今日品管筆數", "—", "📝", "#8B4E00")

        grid.addWidget(self._card_reagent, 0, 0)
        grid.addWidget(self._card_qc_l1,   0, 1)
        grid.addWidget(self._card_qc_l2,   0, 2)
        grid.addWidget(self._card_today,   0, 3)

        self.content_layout.addLayout(grid)

        # 說明文字
        info = QLabel(
            "歡迎使用 UrineConSoft 品管系統。\n"
            "請從左側導覽選擇功能：\n"
            "• 試劑批號管理 ── 更換 LabStrip 批號並執行允收\n"
            "• 品管液批號管理 ── 更換 Quantimetrix 批號並設定 TM/TSD\n"
            "• 品管數據輸入 ── 手動輸入或匯入儀器傳輸檔案\n"
            "• 品管圖 ── 查看 L-J chart"
        )
        info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px; line-height: 1.8;")
        info.setWordWrap(True)
        self.content_layout.addWidget(info)
        self.content_layout.addStretch()

    def _make_card(self, title: str, value: str, icon: str, color: str) -> QFrame:
        card = QFrame()
        card.setObjectName("section_card")
        card.setMinimumHeight(110)
        layout = QVBoxLayout(card)
        layout.setSpacing(8)

        top = QHBoxLayout()
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"font-size:24px; color:{color};")
        top.addWidget(icon_lbl)
        top.addStretch()
        layout.addLayout(top)

        val_lbl = QLabel(value)
        val_lbl.setStyleSheet(f"font-size:20px; font-weight:700; color:{color};")
        val_lbl.setObjectName(f"val_{title}")
        layout.addWidget(val_lbl)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size:12px; color:{COLORS['text_muted']};")
        layout.addWidget(t_lbl)

        return card

    def on_page_show(self):
        self._refresh()

    def _refresh(self):
        # 試劑批號
        rb = ReagentBatchService.get_active()
        lot = rb["lot_number"] if rb else "未設定"
        self._card_reagent.findChild(QLabel, "val_試劑批號").setText(lot)

        # 品管液批號
        active_qc = QCBatchService.get_active_batches()
        l1_lot = l2_lot = "未設定"
        for b in active_qc:
            if b["level_id"] in (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23):
                if b["level_name"] == "Level 1":
                    l1_lot = b["lot_number"]
            if b["level_name"] == "Level 2":
                l2_lot = b["lot_number"]
        self._card_qc_l1.findChild(QLabel, "val_品管液 Level 1").setText(l1_lot)
        self._card_qc_l2.findChild(QLabel, "val_品管液 Level 2").setText(l2_lot)

        # 今日筆數
        try:
            with DBContext() as (_, cur):
                cur.execute(
                    "SELECT COUNT(*) AS cnt FROM DailyQC WHERE DATE(iDate)=%s",
                    (date.today(),)
                )
                row = cur.fetchone()
                cnt = row["cnt"] if row else 0
        except Exception:
            cnt = 0
        self._card_today.findChild(QLabel, "val_今日品管筆數").setText(str(cnt))
