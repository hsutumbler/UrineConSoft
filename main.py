# main.py — UrineConSoft 入口點

import sys
import logger_setup  # Initialize logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from database.connection import test_connection
from ui.login_window import LoginWindow
from ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 初始化資料庫連線測試
    test_connection()
    
    login_win = LoginWindow()
    
    def on_login_success(user: dict):
        main_win = MainWindow(user)
        main_win.show()
        MainWindow._active_windows.append(main_win)
        
    login_win.login_success.connect(on_login_success)
    login_win.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
