import asyncio
import json
import logging
import websockets
import httpx


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PRINT_SERVER_URL = "http://127.0.0.1:5050/print"

http_client = httpx.AsyncClient(timeout=3)

async def listen(ws_url: str, shop_table_id: int):
    """
        웹소켓 연결 및 메시지 수신
        shop_table_id가 일치하는 경우만 프린트 서버로 전달
    """
    while True:
        try:
            logger.info("웹소켓 연결 시도...")
            async with websockets.connect(ws_url) as ws:
                logger.info("웹소켓 연결 성공")

                async for message in ws:
                    try:
                        data = json.loads(message)
                    except Exception:
                        logger.exception("메시지 JSON 파싱 실패")
                        continue

                    meta = data.get("meta", {})
                    msg = data.get("message")

                    if not msg:
                        logger.debug("메시지 본문 없음 → 무시")
                        continue

                    # 테이블 필터링
                    if meta.get("shop_table_id") != shop_table_id:
                        logger.debug("shop_table_id 불일치 → 무시")
                        continue

                    # 프린트 서버로 비동기 전송
                    asyncio.create_task(
                        send_to_print_server(meta, msg)
                    )

        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"웹소켓 연결 종료, 5초 후 재연결... ({e})")
            await asyncio.sleep(5)

        except Exception as e:
            logger.exception(f"웹소켓 오류: {e}")
            await asyncio.sleep(5)

async def send_to_print_server(meta: dict, message: str):
    connection_type = meta.get("connection_type")
    locale = meta.get("locale")
    if not connection_type or not locale:
        logger.warning("meta 정보 부족 → 프린트 요청 생략")
        return
    payload = {
        "connection_type": connection_type,
        "locale": locale,
        "message": message,
    }

    if connection_type == "network":
        payload.update({
            "network_ip": meta.get("network_ip"),
            "network_port": meta.get("network_port"),
        })

    elif connection_type == "serial":
        payload.update({
            "serial_port": meta.get("serial_port"),
            "baud_rate": meta.get("baud_rate"),
        })

    else:
        logger.warning(f"알 수 없는 connection_type: {connection_type}")
        return

    try:
        await http_client.post(
            PRINT_SERVER_URL,
            json=payload
        )
        logger.info("프린트 서버 전송 완료")

    except httpx.ConnectError:
        logger.warning(
            "프린트 서버(127.0.0.1:5050)에 연결할 수 없습니다. "
            "서버 실행 여부를 확인하세요."
        )

    except httpx.RequestError as e:
        logger.warning(f"프린트 요청 실패: {e}")

    except Exception as e:
        logger.exception(f"알 수 없는 프린트 오류: {e}")