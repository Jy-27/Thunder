import asyncio
import json
import aiohttp
import websockets
from typing import Dict

class ExecutionWebsocket:
    def __init__(self, api_key: str, market_base_url: str, websocket_base_url: str, endpoint: str):
        """
        사용자의 체결정보를 웹소켓으로 실시간 수신받는다.

        Alias: exe_ws

        Args:
            api_key (str): api key
            market_base_url (str): 마켓 url
            websocket_base_url (str): 웹소켓 url
            endpoint (str): endpoint url
        """
        self._api_key = api_key
        self.market_base_url = market_base_url
        self.websocket_base_url = websocket_base_url
        self.endpoint = endpoint
        self.listen_key = None
        self.headers = {"X-MBX-APIKEY": self._api_key}
        self.websocket_client = None
        self.session = None  # aiohttp 세션 추가

    async def create_listen_key(self):
        """👻 Listen Key를 최초 생성"""
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.market_base_url}{self.endpoint}", headers=self.headers) as response:
                if response.status == 200:
                    self.listen_key = (await response.json()).get("listenKey")
                else:
                    raise RuntimeError(f"Listen Key 생성 실패: {await response.text()}")

    async def renew_listen_key(self):
        """🔄 Listen Key 갱신 (30분마다 실행)"""
        while True:
            await asyncio.sleep(1800)  # 30분 대기
            async with aiohttp.ClientSession() as session:
                async with session.put(f"{self.market_base_url}{self.endpoint}", headers=self.headers) as response:
                    if response.status != 200:
                        print(f"Listen Key 갱신 실패: {await response.text()}")
                    else:
                        print("✅ Listen Key 갱신 완료")

    async def open_connection(self):
        """🔗 웹소켓 연결"""
        if not self.listen_key:
            await self.create_listen_key()

        websocket_url = f"{self.websocket_base_url}{self.listen_key}"
        self.websocket_client = await websockets.connect(websocket_url)
        # print("✅ 웹소켓 연결 완료:", websocket_url)

    async def close_connection(self):
        """⛓️‍💥 웹소켓 연결 해제"""
        if self.websocket_client:
            await self.websocket_client.close()
            self.websocket_client = None
            # print("🔌 웹소켓 연결 해제됨")

    async def receive_message(self) -> Dict:
        """📩 웹소켓 메시지 수신 (반복 실행)"""
        if self.websocket_client:
            message = await self.websocket_client.recv()
            return json.loads(message)  # JSON 데이터 변환
