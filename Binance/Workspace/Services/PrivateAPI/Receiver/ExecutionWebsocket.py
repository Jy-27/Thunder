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
        self.session = None

    async def init_setting(self):
        self.session = aiohttp.ClientSession()

    async def create_listen_key(self):
        """👻 Listen Key를 최초 생성"""
        async with self.session.post(f"{self.market_base_url}{self.endpoint}", headers=self.headers) as response:
            if response.status == 200:
                self.listen_key = (await response.json()).get("listenKey")
            else:
                raise RuntimeError(f"Listen Key 생성 실패: {await response.text()}")

    async def renew_listen_key(self):
        """🔄 Listen Key 갱신 (30분마다 실행)"""
        async with self.session.put(f"{self.market_base_url}{self.endpoint}", headers=self.headers) as response:
            if response.status != 200:
                print(f"Listen Key 갱신 실패: {await response.text()}")
            else:
                print("✅ Listen Key 갱신 완료")

    async def open_connection(self):
        """🔗 웹소켓 연결"""
        await self.init_setting()
        await self.create_listen_key()
        # await self.renew_listen_key()
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
        if self.session:
            await self.session.close()
            # print("🔌 웹소켓 연결 해제됨")

    async def receive_message(self) -> Dict:
        """📩 웹소켓 메시지 수신 (반복 실행)"""
        if self.websocket_client:
            message = await self.websocket_client.recv()
            return json.loads(message)  # JSON 데이터 변환

if __name__ == "__main__":
    import asyncio
    import os, sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    
    import SystemConfig
    import Workspace.DataStorage.PendingOrder as pending_order
    import Workspace.Utils.BaseUtils as base_utils
    
    import Workspace.Services.PrivateAPI.Trading.FuturesTradingClient as futures_tr_client
    
    import Workspace.DataStorage.ExecutionMessage as message_storage
    
    import Workspace.DataStorage.NodeStorage as storage
    api_path = SystemConfig.Path.bianace
    api_keys = base_utils.load_json(api_path)
    
    api = api_keys['apiKey']
    market_base_url = "https://fapi.binance.com"
    websocket_base_url = "wss://fstream.binance.com/ws/"
    endpoint = "/fapi/v1/listenKey"
    
    
    sub_fields = ["LIMIT", "TAKE_PROFIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"]
    # MARKET 도 있으나 미체결위주이므로 제외시킨다.
    sub_storage = storage.SubStorage(sub_fields)
    main_fields = ['BTCUSDT', 'ADAUSDT']
    main_storage = storage.MainStorage(main_fields, sub_storage)
    
    ins_client = futures_tr_client.FuturesTradingClient(**api_keys)
    pending_o = pending_order.PendingOrder(['ADAUSDT', 'XRPUSDT'], ins_client)
    
    last_message = message_storage.ExecutionMessage(main_fields)
    
    obj = ExecutionWebsocket(api, market_base_url, websocket_base_url, endpoint)
    async def run(count:int):
        print(f" ⏳ 연결 시도중")
        await obj.open_connection()
        print(f" 🔗 websocket 연결")
        for _ in range(count):
            data = await obj.receive_message()
            print(data)
            pending_o.update_order(data)
            last_message.set_data(data)
            
            
            print(f" 🖨️ data: \n{pending_o.storage}\n")
        
        print(f" 👍🏻 수신 완료")
        await obj.close_connection()
        print(f" ⛓️‍💥 websocket 연결 해제")
    
    asyncio.run(run(4))