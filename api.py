import requests
from requests.exceptions import ConnectionError, Timeout, RequestException

def validate_pos(config):
    domain = "kr.coleslaw.co.kr" if config["country"] == "kr" else "jp.coleslaw.co.kr"

    url = (
        f"https://{domain}/api/shop/{config['shop_id']}/pos/{config['shop_table_id']}/"
    )

    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            return True, res.json()
        if res.status_code == 400:
            return False, res.json().get("message", "POS_NOT_FOUND")
        if 500 <= res.status_code < 600:
            return False, "SERVER_ERROR"
        
        return False, f"HTTP_{res.status_code}"
            
    except Timeout:
        return False, "TIMEOUT"

    except ConnectionError:
        # 인터넷 안됨 / DNS 실패 / 서버 다운
        return False, "NETWORK_UNREACHABLE"

    except RequestException as e:
        # requests 내부 기타 에러
        return False, "REQUEST_FAILED"

    except Exception:
        # 진짜 예상 못한 에러
        return False, "UNKNOWN_ERROR"