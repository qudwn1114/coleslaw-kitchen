import requests


def validate_pos(config):
    domain = "kr.coleslaw.co.kr" if config["country"] == "kr" else "jp.coleslaw.co.kr"

    url = (
        f"https://{domain}/api/shop/{config['shop_id']}/pos/{config['shop_table_id']}/"
    )

    try:
        res = requests.get(url, timeout=5)
        if res.status_code != 200:
            return False, res.json().get("message", "INVALID")
        
        return True, res.json()

    except Exception:
        return False, "SERVER_UNREACHABLE"
