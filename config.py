import json
import os
from pathlib import Path

APP_DIR = Path(os.getenv("LOCALAPPDATA")) / "ColeslawKitchen"
CONFIG_PATH = APP_DIR / "settings.json"

APP_DIR.mkdir(parents=True, exist_ok=True)


def load_config():
    if not CONFIG_PATH.exists():
        return None
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_ws_url(config):
    domain = "kr.coleslaw.co.kr" if config["country"] == "kr" else "jp.coleslaw.co.kr"
    return f"wss://{domain}/ws/shop/{config['shop_id']}/order/"
