# ui/main_window.py — UrineConSoft 主視窗

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame,
    QSpacerItem, QSizePolicy, QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from config import APP_NAME, DEFAULT_FONT
from services.auth_service import AuthService


NAV_GROUPS = [
    {
        "group": "品管作業",
        "items": [
            {"icon": "📈", "label": "品管圖（L-J）", "key": "qc_chart", "role_min": 1},
            {"icon": "📝", "label": "品管數據輸入",  "key": "qc_entry", "role_min": 1},
        ],
    },
    {
        "group": "批號管理",
        "items": [
            {"icon": "🧪", "label": "試劑批號管理",   "key": "reagent_batch", "role_min": 1},
            {"icon": "🧫", "label": "品管液批號管理", "key": "qc_batch",      "role_min": 1},
        ],
    },
    {
        "group": "資料查詢",
        "items": [
            {"icon": "🔍", "label": "綜合查詢", "key": "comprehensive_inquiry", "role_min": 1},
        ],
    },
    {
        "group": "系統設定",
        "items": [
            {"icon": "👤", "label": "使用者管理", "key": "users", "role_min": 3},
        ],
    },
]


class MainWindow(QMainWindow):
    _active_windows = []

    def __init__(self, user: dict):
        super().__init__()
        self.user = user
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1280, 800)
        self._page_map: dict[str, QWidget] = {}
        self._nav_btns: dict[str, QPushButton] = {}
        self._current_key: str = ""
        self._build_ui()
        self._apply_style()
        self._navigate_first()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        self.stack = QStackedWidget()
        self.stack.setObjectName("content_area")
        self._register_pages()
        layout.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(180)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_logo())
        layout.addWidget(self._build_user_info())
        layout.addWidget(self._make_divider())

        nav_wrap = QWidget()
        nav_wrap.setObjectName("nav_wrap")
        nav_layout = QVBoxLayout(nav_wrap)
        nav_layout.setContentsMargins(8, 12, 8, 12)
        nav_layout.setSpacing(0)

        for group in NAV_GROUPS:
            visible = [i for i in group["items"] if i["role_min"] <= self.user["role"]]
            if not visible:
                continue
            if not group["group"].startswith("_"):
                grp_lbl = QLabel(group["group"].upper())
                grp_lbl.setObjectName("nav_group_label")
                nav_layout.addWidget(grp_lbl)
            for item in visible:
                btn = QPushButton(f"  {item['icon']}  {item['label']}")
                btn.setObjectName("nav_btn")
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setFixedHeight(40)
                btn.setCheckable(True)
                btn.clicked.connect(lambda _, k=item["key"]: self._navigate(k))
                self._nav_btns[item["key"]] = btn
                nav_layout.addWidget(btn)
            nav_layout.addSpacing(8)

        nav_layout.addStretch()
        layout.addWidget(nav_wrap, 1)
        layout.addWidget(self._make_divider())
        layout.addWidget(self._build_logout_btn())
        return sidebar

    def _build_logo(self) -> QWidget:
        w = QWidget()
        w.setObjectName("logo_bar")
        w.setFixedHeight(68)
        layout = QHBoxLayout(w)
        layout.setContentsMargins(10, 0, 10, 0)
        icon = QLabel("🔬")
        icon.setObjectName("sidebar_logo_icon")
        name = QLabel("尿液品管系統")
        name.setObjectName("sidebar_logo_text")
        layout.addWidget(icon)
        layout.addSpacing(8)
        layout.addWidget(name)
        layout.addStretch()
        return w

    def _build_user_info(self) -> QWidget:
        w = QWidget()
        w.setObjectName("user_info_bar")
        layout = QHBoxLayout(w)
        layout.setContentsMargins(10, 12, 10, 12)
        layout.setSpacing(12)
        avatar = QLabel(self.user["name"][0])
        avatar.setObjectName("user_avatar")
        avatar.setFixedSize(36, 36)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right = QVBoxLayout()
        right.setSpacing(2)
        name_lbl = QLabel(self.user["name"])
        name_lbl.setObjectName("user_name_label")
        role_lbl = QLabel(self.user["role_label"])
        role_lbl.setObjectName("user_role_label")
        right.addWidget(name_lbl)
        right.addWidget(role_lbl)
        layout.addWidget(avatar)
        layout.addLayout(right)
        layout.addStretch()
        return w

    def _build_logout_btn(self) -> QPushButton:
        btn = QPushButton("  ⎋   登出")
        btn.setObjectName("logout_btn")
        btn.setFixedHeight(48)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(self._logout)
        return btn

    def _make_divider(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setObjectName("sidebar_divider")
        line.setFixedHeight(1)
        return line

    def _register_pages(self):
        from ui.qc.user_management   import UserManagementPage
        from ui.qc.reagent_batch     import ReagentBatchPage
        from ui.qc.qc_batch          import QCBatchPage
        from ui.qc.qc_data_entry     import QCDataEntryPage
        from ui.qc.lj_chart          import LJChartPage
        from ui.inquiry.comprehensive_inquiry import ComprehensiveInquiryPage

        page_classes = {
            "users":        (UserManagementPage,  True),
            "reagent_batch":(ReagentBatchPage,    True),
            "qc_batch":     (QCBatchPage,         True),
            "qc_entry":     (QCDataEntryPage,     True),
            "qc_chart":     (LJChartPage,         True),
            "comprehensive_inquiry": (ComprehensiveInquiryPage, True),
        }
        for key, (cls, pass_user) in page_classes.items():
            try:
                page = cls(self.user) if pass_user else cls()
            except TypeError:
                page = cls()
            self._page_map[key] = page
            self.stack.addWidget(page)

    def _navigate(self, key: str):
        if key not in self._page_map:
            return
        self._current_key = key
        self.stack.setCurrentWidget(self._page_map[key])
        for k, btn in self._nav_btns.items():
            btn.setChecked(k == key)
        page = self._page_map[key]
        if hasattr(page, "on_page_show"):
            page.on_page_show()

    def _navigate_first(self):
        self._navigate("qc_chart")

    def _logout(self):
        reply = QMessageBox.question(
            self, "確認登出", f"確定要登出嗎？\n使用者：{self.user['name']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            from ui.login_window import LoginWindow
            login_win = LoginWindow()

            def on_relogin(user: dict):
                new_win = MainWindow(user)
                new_win.show()
                MainWindow._active_windows.append(new_win)
                if login_win in MainWindow._active_windows:
                    MainWindow._active_windows.remove(login_win)

            login_win.login_success.connect(on_relogin)
            login_win.show()
            MainWindow._active_windows.append(login_win)
            if self in MainWindow._active_windows:
                MainWindow._active_windows.remove(self)
            from PyQt6.QtWidgets import QApplication
            QApplication.setQuitOnLastWindowClosed(False)
            self.close()
            QApplication.setQuitOnLastWindowClosed(True)

    def _apply_style(self):
        self.setStyleSheet(f"""
            * {{ font-family: {DEFAULT_FONT}; }}
            QMainWindow, #content_area {{ background: #FDFBF0; }}

            #sidebar {{
                background: #F5F0DC;
                border-right: 1px solid #E0D9C0;
            }}
            #logo_bar {{ background: #EDE8CC; }}
            #sidebar_logo_icon {{ font-size: 20px; }}
            #sidebar_logo_text {{
                color: #2D2A1E; font-size: 15px;
                font-weight: 700; letter-spacing: 1px;
            }}
            #user_info_bar {{ background: #F5F0DC; }}
            #user_avatar {{
                background: #9B7E23; color: #FFFFFF;
                border-radius: 18px; font-size: 14px; font-weight: 700;
            }}
            #user_name_label {{ color: #2D2A1E; font-size: 13px; font-weight: 600; }}
            #user_role_label {{ color: #6B6444; font-size: 11px; }}
            #sidebar_divider {{ background: #E0D9C0; border: none; }}

            #nav_wrap {{ background: #F5F0DC; }}
            #nav_group_label {{
                color: #B5A97A; font-size: 10px;
                font-weight: 700; letter-spacing: 2px;
                padding: 12px 4px 6px 4px;
            }}
            #nav_btn {{
                background: transparent; color: #6B6444;
                border: none; border-radius: 8px;
                text-align: left; padding: 0 10px;
                font-size: 13px; font-weight: 500;
            }}
            #nav_btn:hover {{ background: #EDE8CC; color: #2D2A1E; }}
            #nav_btn:checked {{
                background: #FFF8D6; color: #9B7E23; font-weight: 600;
            }}
            #logout_btn {{
                background: transparent; color: #6B6444;
                border: none; text-align: left;
                padding: 0 20px; font-size: 13px;
            }}
            #logout_btn:hover {{ background: #FFF5F5; color: #CC3333; }}
        """)
