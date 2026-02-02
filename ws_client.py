import asyncio
import json
import logging
import websockets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def listen(ws_url: str, shop_table_id: str):
    """
    웹소켓 연결 및 메시지 수신
    """
    while True:
        try:
            logger.info("웹소켓 연결 시도...")
            async with websockets.connect(ws_url) as ws:
                logger.info("웹소켓 연결 성공")
                async for message in ws:
                    try:
                        data = json.loads(message)
                        # 여기서 메시지 처리
                        logger.info(f"수신: {data}")
                        # 예: 프린터로 전송 로직 추가 가능
                    except Exception as e:
                        logger.exception(f"메시지 처리 오류: {e}")

        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"웹소켓 연결 종료, 5초 후 재연결... ({e})")
            await asyncio.sleep(5)
        except Exception as e:
            logger.exception(f"웹소켓 오류: {e}")
            await asyncio.sleep(5)
