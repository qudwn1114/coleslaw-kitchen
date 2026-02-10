import sys, os, socket
from threading import Thread
import pystray
from PIL import Image
from PyQt6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QAction
import winreg

from config import load_config, get_ws_url, CONFIG_PATH
from config_window import ConfigWindow
from api import validate_pos
from ws_client import listen

APP_NAME = "ColeslawKitchen"
PORT = 5051  # 중복 실행 방지용 포트

# -----------------------------
# 중복 실행 체크
# -----------------------------
def check_already_running():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", PORT))
        s.listen(1)
        return s  # 소켓 유지
    except OSError:
        return None

# -----------------------------
# 웹소켓 시작 함수
# -----------------------------
def start_ws(config):
    ws_url = get_ws_url(config)
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(listen(ws_url, config["shop_table_id"]))

# -----------------------------
# 설정 창
# -----------------------------
def open_config_window(initial_config=None):
    """최초 실행 또는 오류 시 config 입력"""
    app = QApplication.instance() or QApplication([])

    config = initial_config

    while True:
        win = ConfigWindow(config)
        if win.exec() != win.DialogCode.Accepted:
            sys.exit(0)  # 저장 안 하면 종료

        config = load_config()
        ok, result = validate_pos(config)
        if ok:
            return config

        QMessageBox.critical(
            None,
            "POS Authentication Failed",
            f"Cannot start the application.\nResponse Message: {result}"
        )
        # 루프 반복 → 다시 입력 유도


def add_to_startup(exe_path=None):
    if exe_path is None:
        exe_path = sys.executable
    key = winreg.HKEY_CURRENT_USER
    reg_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        registry_key = winreg.OpenKey(key, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(registry_key, APP_NAME, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(registry_key)
        return True
    except Exception as e:
        print(f"등록 실패: {e}")
        return False

def remove_from_startup():
    key = winreg.HKEY_CURRENT_USER
    reg_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        registry_key = winreg.OpenKey(key, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(registry_key, APP_NAME)
        winreg.CloseKey(registry_key)
        return True
    except Exception as e:
        print(f"제거 실패: {e}")
        return False

def is_in_startup():
    key = winreg.HKEY_CURRENT_USER
    reg_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    try:
        registry_key = winreg.OpenKey(key, reg_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(registry_key, APP_NAME)
        winreg.CloseKey(registry_key)
        return value == sys.executable
    except FileNotFoundError:
        return False

def cleanup_old_startup_entry():
    key = winreg.HKEY_CURRENT_USER
    reg_path = r"Software\\Microsoft\\Windows\\CurrentVersion\\Run"
    current_path = sys.executable
    try:
        registry_key = winreg.OpenKey(key, reg_path, 0, winreg.KEY_READ)
        registered_path, _ = winreg.QueryValueEx(registry_key, APP_NAME)
        winreg.CloseKey(registry_key)
        if registered_path != current_path:
            print(f"[⚠️] 등록된 경로가 현재 실행 경로와 다릅니다. 기존 경로 제거: {registered_path}")
            remove_from_startup()
    except FileNotFoundError:
        pass

# -----------------------------
# exe용 경로 처리
# -----------------------------
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


def create_tray(config):
    icon = Image.open(resource_path("kitchen.ico"))

    def on_exit(icon, item):
        icon.stop()
        sys.exit(0)

    def on_reset(icon, item):
        def reset_thread():
            import ctypes
            if CONFIG_PATH.exists():
                CONFIG_PATH.unlink()
            ctypes.windll.user32.MessageBoxW(0, "Configuration reset.\nPlease restart the application.", "Reset Complete", 0)
            icon.stop()
            sys.exit(0)
        
        t = Thread(target=reset_thread, daemon=True)
        t.start()


    def on_toggle_startup(icon, item):
        if is_in_startup():
            remove_from_startup()
        else:
            add_to_startup()

    startup_item = pystray.MenuItem(
        "Run at Startup",
        on_toggle_startup,
        checked=lambda item: is_in_startup()  # 동적 평가
    )

    menu = pystray.Menu(
        pystray.MenuItem("Reset", on_reset),
        startup_item,
        pystray.MenuItem("Exit", on_exit)
    )

    tray_icon = pystray.Icon("ColeslawKitchen", icon, "Coleslaw Kitchen Socket Server", menu)
    tray_icon.run()

# -----------------------------
# 메인 함수
# -----------------------------
def main():
    lock_socket = check_already_running()
    if lock_socket is None:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, "Socket Server is already running.", "Coleslaw Kitchen", 0)
        sys.exit(0)

    config = load_config()
    if not config:
        config = open_config_window()
    else:
        ok, result = validate_pos(config)
        if not ok:
            config = open_config_window(config)

    ws_thread = Thread(target=start_ws, args=(config,), daemon=True)
    ws_thread.start()

    create_tray(config)

if __name__ == "__main__":
    main()
