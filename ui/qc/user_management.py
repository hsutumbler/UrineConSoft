# ui/qc/user_management.py — 使用者管理

from PyQt6.QtWidgets import (
    QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QDialog, QFormLayout, QComboBox,
    QCheckBox, QMessageBox, QTableWidgetItem,
)
from PyQt6.QtCore import Qt
from ui.base_page import BasePage, PAGE_STYLE
from services.auth_service import AuthService, ROLE_LABELS


class UserManagementPage(BasePage):
    def __init__(self, user: dict):
        super().__init__("使用者管理", "新增、修改使用者帳號與權限", user)
        self._build()

    def _build(self):
        toolbar = QHBoxLayout()
        btn_add = QPushButton("＋ 新增使用者")
        btn_add.setObjectName("btn_primary")
        btn_add.clicked.connect(self._add_user)

        self.btn_edit = QPushButton("✏️ 修改")
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_selected)

        self.btn_chpw = QPushButton("🔑 修改密碼")
        self.btn_chpw.setEnabled(False)
        self.btn_chpw.clicked.connect(self._change_password)

        btn_refresh = QPushButton("🔄 重新整理")
        btn_refresh.clicked.connect(self._load)

        toolbar.addWidget(btn_add)
        toolbar.addWidget(self.btn_edit)
        toolbar.addWidget(self.btn_chpw)
        toolbar.addWidget(btn_refresh)
        toolbar.addStretch()
        self.content_layout.addLayout(toolbar)

        self.table = self.make_table(["帳號", "姓名", "角色", "狀態"])
        self.table.itemSelectionChanged.connect(self._on_selection)
        self.table.cellDoubleClicked.connect(lambda r, c: self._edit_selected())
        self.content_layout.addWidget(self.table)
        self._load()

    def _load(self):
        users = AuthService.get_all_users()
        self.table.setRowCount(0)
        for r, u in enumerate(users):
            self.table.insertRow(r)
            vals = [
                u["employee_id"], u["name"],
                ROLE_LABELS.get(u["role"], "?"),
                "啟用" if u["is_active"] else "停用",
            ]
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if c == 0:
                    item.setData(Qt.ItemDataRole.UserRole, u)
                self.table.setItem(r, c, item)
        self._on_selection()

    def _on_selection(self):
        has = len(self.table.selectedItems()) > 0
        self.btn_edit.setEnabled(has)
        self.btn_chpw.setEnabled(has)

    def _get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            item = self.table.item(row, 0)
            if item:
                return item.data(Qt.ItemDataRole.UserRole)
        return None

    def _add_user(self):
        dlg = UserDialog(self)
        if dlg.exec():
            d = dlg.get_data()
            try:
                AuthService.create_user(d["employee_id"], d["name"], d["password"], d["role"])
                self._load()
            except Exception as e:
                self.warn("新增失敗", str(e))

    def _edit_selected(self):
        u = self._get_selected()
        if not u:
            return
        dlg = UserDialog(self, u)
        if dlg.exec():
            d = dlg.get_data()
            AuthService.update_user(u["user_id"], d["name"], d["role"], d["is_active"])
            self._load()

    def _change_password(self):
        u = self._get_selected()
        if not u:
            return
        dlg = ChangePasswordDialog(self, u["name"])
        if dlg.exec():
            AuthService.change_password(u["user_id"], dlg.get_password())
            self.alert("成功", "密碼已修改。")

    def on_page_show(self):
        self._load()


class UserDialog(QDialog):
    def __init__(self, parent, user: dict = None):
        super().__init__(parent)
        self.is_edit = user is not None
        self.setWindowTitle("使用者資料")
        self.setFixedWidth(380)
        self.setStyleSheet(PAGE_STYLE)
        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.f_id   = QLineEdit(user["employee_id"] if user else "")
        self.f_id.setEnabled(not self.is_edit)
        self.f_name = QLineEdit(user["name"] if user else "")
        self.f_pw   = QLineEdit()
        self.f_pw.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_pw.setPlaceholderText("留空則不修改" if self.is_edit else "必填")

        self.f_role = QComboBox()
        for k, v in ROLE_LABELS.items():
            self.f_role.addItem(v, k)
        if user:
            idx = self.f_role.findData(user["role"])
            if idx >= 0:
                self.f_role.setCurrentIndex(idx)

        self.f_active = QCheckBox("帳號啟用")
        self.f_active.setChecked(user["is_active"] if user else True)

        form.addRow("帳號 *", self.f_id)
        form.addRow("姓名 *", self.f_name)
        form.addRow("密碼",   self.f_pw)
        form.addRow("角色 *", self.f_role)
        form.addRow("",       self.f_active)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("儲存")
        btn_ok.setObjectName("btn_primary")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self._validate)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        form.addRow(btn_row)

    def _validate(self):
        if not self.f_id.text().strip() or not self.f_name.text().strip():
            QMessageBox.warning(self, "驗證", "帳號與姓名為必填")
            return
        if not self.is_edit and not self.f_pw.text():
            QMessageBox.warning(self, "驗證", "新增使用者時密碼為必填")
            return
        self.accept()

    def get_data(self) -> dict:
        return {
            "employee_id": self.f_id.text().strip(),
            "name":        self.f_name.text().strip(),
            "password":    self.f_pw.text(),
            "role":        self.f_role.currentData(),
            "is_active":   self.f_active.isChecked(),
        }


class ChangePasswordDialog(QDialog):
    def __init__(self, parent, user_name: str):
        super().__init__(parent)
        self.setWindowTitle(f"修改密碼 — {user_name}")
        self.setFixedWidth(340)
        self.setStyleSheet(PAGE_STYLE)
        form = QFormLayout(self)
        form.setSpacing(12)
        form.setContentsMargins(24, 24, 24, 24)

        self.f_pw1 = QLineEdit()
        self.f_pw1.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_pw2 = QLineEdit()
        self.f_pw2.setEchoMode(QLineEdit.EchoMode.Password)
        self.f_pw2.setPlaceholderText("請再輸入一次")

        form.addRow("新密碼 *",   self.f_pw1)
        form.addRow("確認密碼 *", self.f_pw2)

        btn_row = QHBoxLayout()
        btn_ok = QPushButton("確認")
        btn_ok.setObjectName("btn_primary")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self._validate)
        btn_cancel.clicked.connect(self.reject)
        btn_row.addWidget(btn_ok)
        btn_row.addWidget(btn_cancel)
        form.addRow(btn_row)

    def _validate(self):
        if not self.f_pw1.text():
            QMessageBox.warning(self, "驗證", "請輸入新密碼")
            return
        if self.f_pw1.text() != self.f_pw2.text():
            QMessageBox.warning(self, "驗證", "兩次密碼不一致")
            return
        self.accept()

    def get_password(self) -> str:
        return self.f_pw1.text()
