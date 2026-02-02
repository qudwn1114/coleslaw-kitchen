import sys, os
from threading import Thread
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon

from config import load_config, get_ws_url, CONFIG_PATH
from config_window import ConfigWindow
from api import validate_pos
from ws_client import listen

ICON_PATH = "kitchen.ico"

def start_ws(config):
    ws_url = get_ws_url(config)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen(ws_url, config["shop_table_id"]))

def open_config_window():
    """최초 실행 또는 오류 시 config 입력"""
    app = QApplication.instance() or QApplication([])

    while True:
        win = ConfigWindow()
        if win.exec() != win.DialogCode.Accepted:
            sys.exit(0)  # 저장 안 하면 종료

        config = load_config()
        ok, result = validate_pos(config)
        if ok:
            return config

        QMessageBox.critical(
            None,
            "POS Authentication Failed",
            f"Cannot start the application.\nReason: {result}"
        )
        # 루프 반복 → 다시 입력 유도

def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    app = QApplication([])

    # -----------------------------
    # config 로드 및 검증
    # -----------------------------
    config = load_config()
    if not config:
        config = open_config_window()
    else:
        ok, result = validate_pos(config)
        if not ok:
            QMessageBox.critical(
                None,
                "POS Authentication Failed",
                f"Cannot start the application.\nReason: {result}"
            )
            config = open_config_window()

    # -----------------------------
    # 웹소켓 시작
    # -----------------------------
    ws_thread = Thread(target=start_ws, args=(config,), daemon=True)
    ws_thread.start()

    # -----------------------------
    # 트레이 아이콘
    # -----------------------------
    tray = QSystemTrayIcon(QIcon(resource_path(ICON_PATH)), app)
    tray.setToolTip("Coleslaw Kitchen")

    def reset_app():
        if CONFIG_PATH.exists():
            CONFIG_PATH.unlink()  # config 삭제

        QMessageBox.information(
            None,
            "Reset Complete",
            "Configuration has been reset.\nPlease restart the application."
        )
        QApplication.quit()       # 프로그램 종료

   # 트레이 메뉴
    menu = QMenu()
    reset_action = menu.addAction("Reset")
    exit_action = menu.addAction("Exit")
    tray.setContextMenu(menu)
    tray.show()

    # 메뉴 연결
    reset_action.triggered.connect(reset_app)
    exit_action.triggered.connect(lambda: app.quit())

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
