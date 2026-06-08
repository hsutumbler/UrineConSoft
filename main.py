# main.py — UrineConSoft 入口點

import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.connection import test_connection
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def check_and_update_db():
    from database.connection import DBContext
    try:
        with DBContext() as (_, cur):
            cur.execute("SHOW COLUMNS FROM qc_target_settings LIKE 'semi_target_min'")
            if not cur.fetchone():
                cur.execute("ALTER TABLE qc_target_settings ADD COLUMN semi_target_min VARCHAR(20) COMMENT '半定量範圍下限'")
                cur.execute("ALTER TABLE qc_target_settings ADD COLUMN semi_target_max VARCHAR(20) COMMENT '半定量範圍上限'")
    except Exception as e:
        print(f"DB Update Error: {e}")

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 初始化資料庫連線測試
    test_connection()
    check_and_update_db()
    
    # login_win = LoginWindow()
    # 
    # def on_login_success(user: dict):
    #     main_win = MainWindow(user)
    #     main_win.show()
    #     MainWindow._active_windows.append(main_win)
    #     
    # login_win.login_success.connect(on_login_success)
    # login_win.show()

    # 開發測試用：預設自動以 admin 登入
    admin_user = {
        'user_id': 1,
        'employee_id': 'admin',
        'name': '系統管理員',
        'role': 3,
        'role_label': '系統管理員'
    }
    main_win = MainWindow(admin_user)
    main_win.show()
    MainWindow._active_windows.append(main_win)
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
