import asyncio
import aiohttp
from typing import List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

# 힌트용
from multiprocessing import Queue as mp_q
from Workspace.DataStorage.NodeStorage import MainStorage as storage
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket as futures_mk_ws
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket as futures_exe_ws
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient as futures_tr_client
from Workspace.Processor.Wallet.Wallet import Wallet
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient
from Workspace.Processor.Order.PendingOrder import PendingOrder
class AsyncioWorks:
    def __init__(
        self,
        storage_real_time: storage,
        storage_history:storage,

        stream:List,
        
        ins_market_ws: futures_mk_ws,
        ins_execution_ws: futures_exe_ws,
        ins_wallet: Wallet,
        ins_futures_tr_client:futures_tr_client,
        ins_telegram_client:TelegramClient,
        ins_pending_order:PendingOrder
    ):
        # self.queue_ws_execution_to_wallet = asyncio.Queue()
        self.queue_ws_execution_to_real_storage = asyncio.Queue()
        self.queue_ws_excution_to_pending_order = asyncio.Queue()
        self.evnet_to_wallet = asyncio.Event()

        self.storage_real_time = storage_real_time
        self.storage_history = storage_history

        self.ins_market_ws = ins_market_ws
        self.ins_execution_ex = ins_execution_ws
        self.ins_wallet = ins_wallet
        self.ins_futures_tr_client = ins_futures_tr_client
        self.ins_telegram_client = ins_telegram_client
        self.ins_pending_order = ins_pending_order

        self.symbols = self.ins_market_ws.symbols
        self.stream = stream

    # 개별동작
    async def run_update_listen_key(self):
        """
        🚀 listen key를 지정 시간단위로 갱신한다.
        해당 함수 미동작시 체결내역 웹소켓 수신 불가.
        """
        print(f"  🚀 listen key 반복 업데이트 시작.")
        while True:
            await asyncio.sleep(1800)
            await self.ins_execution_ex.renew_listen_key()
            print(f"  🔄 listen key 업데이트 완료")

    async def run_execute_websocket(self):
        """
        🚀 Executtion Websocket 데이터를 이벤트 발생시에 수신한다.
        수신된 데이터는 지갑 저장소로 queue 발송하여 업데이트 시그널로 활용한다.
        """
        await self.ins_execution_ex.open_connection()
        print(f"  🔗 웹소켓(체결 내역) 연결완료")
        while True:
            # await asyncio.sleep(0)
            ws_message = await self.ins_execution_ex.receive_message()
            print(ws_message)
            await self.evnet_to_wallet.set()
            await self.queue_ws_excution_to_pending_order.put(ws_message)

    async def run_market_websocket(self):
        """
        🚀 Market Websocket 데이터를 무기한 수신한다.
        수신한 데이터는 실시간 저장소에 symbol별 최근 데이터를 저장한다.
        """
        print(f"  🚀 웹소켓(거래 내역) 시작")
        await self.ins_market_ws.setup_kline_stream(self.stream)
        while True:
            ws_message = await self.ins_market_ws.receive_data()
            # print(ws_message)
            await self.queue_ws_execution_to_real_storage.put(ws_message)
            
    async def run_real_storage_update(self):
        """
        🚀 Market Websocket 수신 데이터를 이용하여 실시간 저장소를 업데이트한다.
        """
        print(f"  🚀 실시간 저장소 업데이트 시작.")
        while True:
            ws_message = await self.queue_ws_execution_to_real_storage.get()
            kline_data = data['k']
            symbol = kline_data['s']
            interval = kline_data['i']
            self.storage_real_time.set_data(symbol, interval, ws_message)
            await self.queue_ws_execution_to_real_storage.task_done()

    async def run_pending_order(self):
        while True:
            ws_message = await self.queue_ws_excution_to_pending_order.get()
            self.ins_pending_order.update_order(ws_message)
            self.queue_ws_excution_to_pending_order.task_done()

    async def run_wallet_update(self):
        """
        🚀 asyncio.event를 이용하여 월렛을 업데이트한다.
        잦은 api호출을 피하기 위하여 메모리에 wallet 정보를 업데이트한다.
        """
        while True:
            await self.evnet_to_wallet.wait()
            await self.ins_wallet.update_balance()
            await self.evnet_to_wallet.clear()        

    async def run_status_message(self):
        print(f"  🚀 상태 메시지 발신 시작.")
        while True:
            """
            주기적으로 월렛정보, 거래정보 등 기타 트렌드 를 정리해서 발송한다.
            """
            self.ins_telegram_client.send_message(self.ins_wallet)
            await asyncio.sleep(10)

    async def start(self):
        t1 = asyncio.create_task(self.run_update_listen_key())
        t2 = asyncio.create_task(self.run_execute_websocket())
        t3 = asyncio.create_task(self.run_market_websocket())
        t4 = asyncio.create_task(self.run_real_storage_update())
        t5 = asyncio.create_task(self.run_pending_order())
        t6 = asyncio.create_task(self.run_wallet_update())
        t7 = asyncio.create_task(self.run_status_message())

        await asyncio.gather(t1, t2, t3, t4, t5, t6, t7)

if __name__ == "__main__":
    import Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket as futures_exe_ws
    import Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket as futures_mk_ws
    import Workspace.Processor.Order.PendingOrder as pending_order
    import Workspace.DataStorage.DataStorage as storage
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    
    import os, sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    
    ### storage
    main_fields = SystemConfig.Streaming.symbols
    sub_fields = SystemConfig.Streaming.intervals
    
    sub_storage = storage.SubStorage(sub_fields)
    stroage_history = storage.MainStroage(main_fields, sub_storage)
    storage_real_time = storage.MainStroage(main_fields, sub_storage)
    
    ### API 
    binance_api_path = SystemConfig.Path.bianace
    telegram_api_path = SystemConfig.Path.telegram
    
    binance_api_key = base_utils.load_json(binance_api_path)
    telegram_api_key = base_utils.load_json(telegram_api_path)
    
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ### ins
    futures_mk_ws = futures_mk_ws.FuturesMarketWebsocket(main_fields)
    futures_exe_ws = futures_exe_ws.FuturesExecutionWebsocket(**binance_api_key)
    futures_tr_client_ = futures_tr_client(**binance_api_key)
    wallet = Wallet(5, futures_tr_client_)
    telegram = TelegramClient(**telegram_api_key)
    pending_o = pending_order.PendingOrder(symbols, futures_tr_client_)
    ### start
    
    obj = AsyncioWorks(storage_real_time,
                    stroage_history,
                    intervals,
                    futures_mk_ws,
                    futures_exe_ws,
                    wallet,
                    futures_tr_client_,
                    telegram,
                    pending_o)

    asyncio.run(obj.start())