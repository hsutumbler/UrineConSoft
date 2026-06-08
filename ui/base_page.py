# ui/base_page.py — UrineConSoft UI 基礎（黃色調）

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit,
    QMessageBox, QSizePolicy, QStyledItemDelegate,
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QFont, QColor
from config import DEFAULT_FONT


class CenterDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignmentFlag.AlignCenter


# ── 設計 Token（黃色／米色調） ────────────────────────────────
COLORS = {
    "bg_base":     "#FDFBF0",   # 最底層（淡米黃）
    "bg_surface":  "#FFFEF7",   # 卡片（極淡黃白）
    "bg_input":    "#FFFFFF",
    "border":      "#E0D9C0",   # 米色邊框
    "border_focus":"#9B7E23",
    "text_primary":  "#2D2A1E",
    "text_secondary":"#6B6444",
    "text_muted":    "#B5A97A",
    "accent":        "#9B7E23",  # 深金黃
    "accent_hover":  "#7A6118",
    "accent_light":  "#FFF8D6",  # 淡選取背景
    "success":   "#28A745",
    "warning":   "#CC7700",
    "danger":    "#CC3333",
    "danger_bg": "#FFF5F5",
    "danger_border":"#FFBBBB",
    "table_bg":    "#FFFEF7",
    "table_alt":   "#FDFBEC",
    "table_head":  "#F5F0D8",
    "table_select":"#FFF8D6",
    "grid":        "#E8E0C0",
}

PAGE_STYLE = f"""
    QWidget {{
        background: {COLORS['bg_base']};
        color: {COLORS['text_primary']};
        font-family: {DEFAULT_FONT};
        font-size: 13px;
    }}

    #page_title {{
        color: {COLORS['text_primary']};
        font-size: 22px;
        font-weight: 700;
    }}
    #page_subtitle {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
    }}
    #header_divider {{
        background: {COLORS['border']};
        max-height: 1px;
        border: none;
    }}

    #section_card {{
        background: {COLORS['bg_surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
        padding: 20px;
    }}

    QLabel {{
        color: {COLORS['text_secondary']};
        font-size: 13px;
        background: transparent;
    }}

    QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QSpinBox, QDoubleSpinBox, QTextEdit {{
        background: {COLORS['bg_input']};
        border: 1.5px solid {COLORS['border']};
        border-radius: 8px;
        color: {COLORS['text_primary']};
        font-size: 13px;
        padding: 8px 12px;
        min-height: 32px;
        selection-background-color: {COLORS['accent_light']};
    }}
    QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDateTimeEdit:focus,
    QSpinBox:focus, QDoubleSpinBox:focus, QTextEdit:focus {{
        border-color: {COLORS['border_focus']};
    }}

    QComboBox::drop-down, QDateEdit::drop-down, QDateTimeEdit::drop-down {{
        border: none;
        width: 32px;
        background: {COLORS['bg_base']};
        border-left: 1px solid {COLORS['border']};
        border-top-right-radius: 8px;
        border-bottom-right-radius: 8px;
    }}
    QComboBox {{ combobox-popup: 0; }}
    QComboBox QListView {{
        background-color: #FFFFFF;
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
    }}
    QComboBox QAbstractItemView::item {{
        min-height: 36px;
        padding-left: 10px;
        color: {COLORS['text_primary']};
    }}
    QComboBox QAbstractItemView::item:selected {{
        background-color: {COLORS['accent_light']};
        color: {COLORS['accent']};
    }}

    QSpinBox::up-button, QSpinBox::down-button,
    QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
        background: {COLORS['border']};
        border: none;
        width: 18px;
        border-radius: 3px;
    }}

    QPushButton {{
        background: {COLORS['bg_surface']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 13px;
        font-weight: 500;
        min-height: 34px;
    }}
    QPushButton:hover {{
        background: {COLORS['accent_light']};
        color: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}
    QPushButton:pressed {{ background: #F0E8C0; }}
    QPushButton:disabled {{
        color: {COLORS['text_muted']};
        border-color: {COLORS['border']};
    }}

    QPushButton#btn_primary {{
        background: {COLORS['accent']};
        color: #FFFFFF;
        border: none;
        font-weight: 600;
    }}
    QPushButton#btn_primary:hover {{ background: {COLORS['accent_hover']}; }}

    QPushButton#btn_danger {{
        background: {COLORS['danger_bg']};
        color: {COLORS['danger']};
        border: 1px solid {COLORS['danger_border']};
    }}
    QPushButton#btn_danger:hover {{
        background: #FEE2E2;
        color: #991111;
    }}

    QPushButton#btn_success {{
        background: #E8F5E9;
        color: {COLORS['success']};
        border: 1px solid #A5D6A7;
    }}
    QPushButton#btn_success:hover {{ background: #C8E6C9; }}

    QTableWidget {{
        background: {COLORS['table_bg']};
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        gridline-color: {COLORS['grid']};
        color: {COLORS['text_primary']};
        font-size: 13px;
        outline: none;
    }}
    QTableWidget::item {{ padding: 10px 14px; border: none; }}
    QTableWidget::item:selected {{
        background: {COLORS['table_select']};
        color: {COLORS['accent']};
    }}
    QTableWidget::item:alternate {{ background: {COLORS['table_alt']}; }}

    QHeaderView::section {{
        background: {COLORS['table_head']};
        color: {COLORS['text_primary']};
        border: none;
        border-right: 1px solid {COLORS['grid']};
        border-bottom: 1px solid {COLORS['grid']};
        padding: 10px 14px;
        font-size: 13px;
        font-weight: 700;
    }}

    QScrollBar:vertical {{
        background: {COLORS['bg_surface']};
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {COLORS['text_muted']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: {COLORS['bg_surface']};
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLORS['text_muted']};
        border-radius: 3px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QDialog {{
        background: {COLORS['bg_surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 12px;
    }}
    QMessageBox {{ background: {COLORS['bg_surface']}; }}

    QCheckBox {{ color: {COLORS['text_secondary']}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px;
        border-radius: 4px;
        border: 1.5px solid {COLORS['border']};
        background: {COLORS['bg_input']};
    }}
    QCheckBox::indicator:checked {{
        background: {COLORS['accent']};
        border-color: {COLORS['accent']};
    }}

    QGroupBox {{
        border: 1px solid {COLORS['border']};
        border-radius: 10px;
        margin-top: 14px;
        padding: 12px;
        color: {COLORS['text_secondary']};
        font-size: 12px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 8px;
        color: {COLORS['text_primary']};
    }}

    QTabWidget::pane {{
        border: 1px solid {COLORS['border']};
        border-radius: 0 8px 8px 8px;
        background: {COLORS['bg_surface']};
    }}
    QTabBar::tab {{
        background: {COLORS['bg_base']};
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['border']};
        border-bottom: none;
        padding: 8px 18px;
        border-radius: 6px 6px 0 0;
        font-size: 13px;
    }}
    QTabBar::tab:selected {{
        background: {COLORS['bg_surface']};
        color: {COLORS['accent']};
        font-weight: 600;
        border-bottom: 1px solid {COLORS['bg_surface']};
    }}
    QTabBar::tab:hover {{ background: {COLORS['accent_light']}; }}
"""


class BasePage(QWidget):
    """所有功能頁面的基礎類別。"""

    def __init__(self, title: str, subtitle: str = "", user: dict = None):
        super().__init__()
        self.user = user or {}
        self.setStyleSheet(PAGE_STYLE)
        self._build_base(title, subtitle)

    def showEvent(self, event):
        super().showEvent(event)
        from PyQt6.QtWidgets import QComboBox
        for combo in self.findChildren(QComboBox):
            view = combo.view()
            if view:
                view.window().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
                view.window().setWindowFlags(
                    view.window().windowFlags() |
                    Qt.WindowType.FramelessWindowHint |
                    Qt.WindowType.NoDropShadowWindowHint
                )

    def _build_base(self, title: str, subtitle: str):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(0)

        self.header_widget = QWidget()
        h_layout = QVBoxLayout(self.header_widget)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(0)

        header = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        lbl_title = QLabel(title)
        lbl_title.setObjectName("page_title")
        title_col.addWidget(lbl_title)
        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setObjectName("page_subtitle")
            title_col.addWidget(lbl_sub)
        header.addLayout(title_col)
        header.addStretch()
        h_layout.addLayout(header)
        h_layout.addSpacing(20)

        divider = QFrame()
        divider.setObjectName("header_divider")
        divider.setFrameShape(QFrame.Shape.HLine)
        h_layout.addWidget(divider)
        h_layout.addSpacing(24)

        layout.addWidget(self.header_widget)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(16)
        layout.addLayout(self.content_layout)

    @staticmethod
    def make_table(headers: list[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        t.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        t.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        t.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(True)
        t.setWordWrap(False)
        t.verticalHeader().setDefaultSectionSize(42)
        t.setItemDelegate(CenterDelegate(t))
        return t

    @staticmethod
    def fill_table(table: QTableWidget, rows: list[list]):
        table.setRowCount(0)
        for r, row_data in enumerate(rows):
            table.insertRow(r)
            for c, val in enumerate(row_data):
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(r, c, item)

    def confirm(self, title: str, message: str, default_yes=False) -> bool:
        dlg = QMessageBox(self.window())
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Icon.Question)
        dlg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        dlg.setDefaultButton(
            QMessageBox.StandardButton.Yes if default_yes else QMessageBox.StandardButton.No
        )
        dlg.setStyleSheet(PAGE_STYLE)
        return dlg.exec() == QMessageBox.StandardButton.Yes

    def alert(self, title: str, message: str):
        dlg = QMessageBox(self.window())
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Icon.Information)
        dlg.setStyleSheet(PAGE_STYLE)
        dlg.exec()

    def warn(self, title: str, message: str):
        dlg = QMessageBox(self.window())
        dlg.setWindowTitle(title)
        dlg.setText(message)
        dlg.setIcon(QMessageBox.Icon.Warning)
        dlg.setStyleSheet(PAGE_STYLE)
        dlg.exec()

    @staticmethod
    def make_badge(text: str, color: str = "gold") -> QLabel:
        lbl = QLabel(text)
        palette = {
            "gold":  "color:#7A5C00; background:#FFF3C4;",
            "green": "color:#155724; background:#D4EDDA;",
            "red":   "color:#721C24; background:#F8D7DA;",
            "grey":  "color:#555555; background:#EEEEEE;",
        }
        style = palette.get(color, palette["gold"])
        lbl.setStyleSheet(
            f"{style} border-radius:4px; padding:2px 8px; "
            f"font-size:11px; font-weight:600;"
        )
        lbl.setFixedHeight(20)
        return lbl

    @staticmethod
    def make_table_btn(label: str, style: str = "default") -> QPushButton:
        btn = QPushButton(label)
        btn.setFixedSize(64, 26)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if style == "primary":
            btn.setObjectName("btn_primary")
            btn.setStyleSheet("""
                QPushButton#btn_primary {
                    background: #9B7E23; color: #FFFFFF;
                    font-size: 12px; padding: 0; margin: 0;
                    min-height: 0; max-height: 26px;
                    border-radius: 4px; border: none;
                }
                QPushButton#btn_primary:hover { background: #7A6118; }
            """)
        elif style == "danger":
            btn.setObjectName("btn_danger")
            btn.setStyleSheet("""
                QPushButton#btn_danger {
                    background: #FFF5F5; color: #CC3333;
                    font-size: 12px; padding: 0; margin: 0;
                    min-height: 0; max-height: 26px;
                    border-radius: 4px; border: 1px solid #FFBBBB;
                }
                QPushButton#btn_danger:hover { background: #FEE2E2; }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    font-size: 12px; padding: 0; margin: 0;
                    min-height: 0; max-height: 26px; border-radius: 4px;
                }
            """)
        return btn
