# ui/login_window.py — UrineConSoft 登入視窗

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal
from services.auth_service import AuthService
from config import APP_NAME, APP_VERSION, DEFAULT_FONT


class LoginWindow(QDialog):
    login_success = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setFixedSize(440, 540)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self._drag_pos = None
        self._build_ui()
        self._apply_style()
        self.input_id.setFocus()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)

        card = QFrame()
        card.setObjectName("login_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(44, 44, 44, 44)
        layout.setSpacing(0)

        # 品牌區
        icon_label = QLabel("🔬")
        icon_label.setObjectName("brand_icon")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel(APP_NAME)
        title.setObjectName("brand_title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle = QLabel("鏡檢組品管系統")
        subtitle.setObjectName("brand_subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addSpacing(10)
        layout.addWidget(title)
        layout.addSpacing(4)
        layout.addWidget(subtitle)
        layout.addSpacing(20)

        # 連線狀態
        status_row = QHBoxLayout()
        status_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_row.setSpacing(6)
        self.indicator = QLabel()
        self.indicator.setFixedSize(10, 10)
        self.indicator.setStyleSheet("border-radius:5px; background:#CC3333;")
        self.lbl_conn = QLabel("偵測中...")
        self.lbl_conn.setStyleSheet(f"font-size:12px; color:#6B6444; font-family:{DEFAULT_FONT};")
        self.btn_reconnect = QPushButton("連線伺服器")
        self.btn_reconnect.setObjectName("btn_reconnect")
        self.btn_reconnect.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_reconnect.setFlat(True)
        self.btn_reconnect.setStyleSheet(f"""
            QPushButton#btn_reconnect {{
                color: #9B7E23; font-size:12px; font-weight:bold;
                border:none; background:transparent; padding:0 4px;
                font-family:{DEFAULT_FONT};
            }}
            QPushButton#btn_reconnect:hover {{ color:#7A6118; text-decoration:underline; }}
        """)
        status_row.addWidget(self.indicator)
        status_row.addWidget(self.lbl_conn)
        status_row.addWidget(self.btn_reconnect)
        layout.addLayout(status_row)
        layout.addSpacing(20)

        # 工號
        lbl_id = QLabel("帳號")
        lbl_id.setObjectName("input_label")
        self.input_id = _StyledInput("請輸入帳號", False)
        layout.addWidget(lbl_id)
        layout.addSpacing(6)
        layout.addWidget(self.input_id)
        layout.addSpacing(18)

        # 密碼
        lbl_pw = QLabel("密碼")
        lbl_pw.setObjectName("input_label")
        self.input_pw = _StyledInput("請輸入密碼", True)
        layout.addWidget(lbl_pw)
        layout.addSpacing(6)
        layout.addWidget(self.input_pw)
        layout.addSpacing(28)

        # 登入按鈕
        self.btn_login = QPushButton("登　入")
        self.btn_login.setObjectName("btn_login")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setFixedHeight(46)
        layout.addWidget(self.btn_login)
        layout.addSpacing(14)

        # 狀態訊息
        self.lbl_status = QLabel("")
        self.lbl_status.setObjectName("status_label")
        self.lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_status.setFixedHeight(20)
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        ver = QLabel(f"v{APP_VERSION}")
        ver.setObjectName("version_label")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ver)

        outer.addWidget(card)

        self.btn_login.clicked.connect(self._do_login)
        self.input_pw.returnPressed.connect(self._do_login)
        self.input_id.returnPressed.connect(lambda: self.input_pw.setFocus())
        self.btn_reconnect.clicked.connect(self._check_db)
        self._check_db()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QDialog {{ background: #FDFBF0; }}
            #login_card {{
                background: #FFFEF7;
                border-radius: 12px;
                border: 1px solid #E0D9C0;
            }}
            #brand_icon {{ font-size: 36px; }}
            #brand_title {{
                color: #2D2A1E; font-size: 20px; font-weight: 700;
                font-family: {DEFAULT_FONT}; letter-spacing: 2px;
            }}
            #brand_subtitle {{
                color: #6B6444; font-size: 12px;
                font-family: {DEFAULT_FONT};
            }}
            #input_label {{
                color: #2D2A1E; font-size: 14px; font-weight: 700;
                font-family: {DEFAULT_FONT};
            }}
            #btn_login {{
                background: #9B7E23; color: #FFFFFF;
                border: none; border-radius: 8px;
                font-size: 15px; font-weight: 700;
                font-family: {DEFAULT_FONT}; letter-spacing: 6px;
            }}
            #btn_login:hover {{ background: #7A6118; }}
            #btn_login:disabled {{ background: #C8BC8A; }}
            #status_label {{
                color: #CC3333; font-size: 12px;
                font-family: {DEFAULT_FONT};
            }}
            #version_label {{ color: #B5A97A; font-size: 11px; }}
        """)

    def _check_db(self):
        self.lbl_conn.setText("連線中...")
        self.btn_reconnect.setEnabled(False)
        from PyQt6.QtCore import QCoreApplication
        QCoreApplication.processEvents()
        from database.connection import test_connection
        ok = test_connection()
        self.btn_reconnect.setEnabled(True)
        if ok:
            self.indicator.setStyleSheet("border-radius:5px; background:#28A745;")
            self.lbl_conn.setText("已連接資料庫")
            self.lbl_conn.setStyleSheet(f"font-size:12px; color:#28A745; font-weight:bold; font-family:{DEFAULT_FONT};")
        else:
            self.indicator.setStyleSheet("border-radius:5px; background:#CC3333;")
            self.lbl_conn.setText("未連接資料庫")
            self.lbl_conn.setStyleSheet(f"font-size:12px; color:#CC3333; font-weight:bold; font-family:{DEFAULT_FONT};")

    def _do_login(self):
        emp_id = self.input_id.text().strip()
        password = self.input_pw.text()
        if not emp_id or not password:
            self.lbl_status.setText("請輸入帳號與密碼")
            return
        self.btn_login.setEnabled(False)
        self.btn_login.setText("驗 證 中 …")
        from database.connection import DatabasePool
        if DatabasePool._offline_mode and not (emp_id == "admin" and password == "0"):
            self.lbl_status.setText("離線模式：僅限系統管理員登入")
            self._reset_btn()
            return
        try:
            user = AuthService.login(emp_id, password)
        except Exception as e:
            self.lbl_status.setText(f"連線錯誤：{e}")
            self._reset_btn()
            return
        if user is None:
            self.lbl_status.setText("帳號或密碼錯誤")
            self.input_pw.clear()
            self._reset_btn()
            return
        self.login_success.emit(user)
        self.accept()

    def _reset_btn(self):
        self.btn_login.setEnabled(True)
        self.btn_login.setText("登　入")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class _StyledInput(QLineEdit):
    def __init__(self, placeholder: str, is_password: bool):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedHeight(46)
        if is_password:
            self.setEchoMode(QLineEdit.EchoMode.Password)
        self.setStyleSheet(f"""
            QLineEdit {{
                background: #FDFBF0; border: 1.5px solid #E0D9C0;
                border-radius: 8px; color: #2D2A1E;
                font-size: 14px; padding: 0 16px;
                font-family: {DEFAULT_FONT};
            }}
            QLineEdit:focus {{
                border-color: #9B7E23; background: #FFFEF7;
            }}
        """)
