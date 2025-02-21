import asyncio
import aiohttp
from typing import List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

# 힌트용
from multiprocessing import Queue as mp_q
from Workspace.DataStorage.DataStorage import SymbolStorage as storage
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket as futures_mk_ws
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket as futures_exe_ws
from Workspace.DataStorage.StorageManager import SyncStorage
from Workspace.Processor.Order.Futures.RealTradingProcessor import Orders
from Workspace.Processor.Wallet.WelletManager import Wallet

class AsyncioWorks:
    def __init__(
        self,

        event_history_analysis: mp_q,
        event_anlysis_order: mp_q,
        event_monitor_order:mp_q,
        event_wallet_monitor:mp_q,

        storage_real_time: storage,
        storage_history:storage,

        ins_market_ws: futures_mk_ws,
        ins_execution_ws: futures_exe_ws,
        ins_wallet: Wallet
    ):
        self.event_ws_execution_to_wallet = asyncio.Queue()
        self.event_order_to_wallet = asyncio.Queue()

        self.event_history_to_analysis:mp_q

        self.event_mp_history_analysis = event_history_analysis
        self.event_mp_anlysis_order = event_anlysis_order
        self.event_mp_monitor_order = event_monitor_order
        self.event_mp_wallet_monitor = event_wallet_monitor

        self.storage_real_time = storage_real_time
        self.storage_history = storage_history

        self.ins_market_ws = ins_market_ws
        self.ins_execution_ex = ins_execution_ws
        self.ins_wallet = ins_wallet

        self.symbols = self.ins_market_ws.symbols
        self.stream = self.ins_market_ws.interval_streams

        self.ins_sync_storage = SyncStorage(self.symbols, self.storage_history)

        self.loop = asyncio.get_running_loop()
        
    async def run_market_websocket(self):
        """
        🚀 Market Websocket 데이터를 무기한 수신한다.
        수신한 데이터는 실시간 저장소에 symbol별 최근 데이터를 저장한다.
        """
        print(f"  🚀 웹소켓(거래 내역) 시작")
        while True:
            data = await self.ins_market_ws.receive_data()
            kline_data = data['k']
            symbol = kline_data['s']
            interval = kline_data['i']
            self.storage_real_time.update_data(symbol, *(interval, data))
    
    async def run_execute_websocket(self):
        """
        🚀 Executtion Websocket 데이터를 이벤트 발생시에 수신한다.
        수신된 데이터는 지갑 저장소로 queue 발송하여 업데이트 시그널로 활용한다.
        """
        await self.ins_execution_ex.open_connection()
        print(f"  🔗 웹소켓(체결 내역) 연결완료")
        while True:
            # await asyncio.sleep(0)
            data = await self.ins_execution_ex.receive_message()
            # await asyncio.sleep(0)
            await self.event_order_to_wallet.put(data)

    async def run_wallet_update(self):
        """
        🔄 Order 주문 발생시 월렛 정보를 업데이트한다.
        """
        print(f"  🚀 wallet 업데이트 시작.")
        while True:
            data = await self.event_order_to_wallet.get()
            await self.ins_wallet.update_balance()
            await self.event_order_to_wallet.task_done()

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

    async def run_history_storage_update(self):
        """
        🚀 주기적으로 kline data를 업데이트한 후 분석함수에 시작 신호를 보낸다.
        """
        print(f"  🚀 history storage 반복 업데이트 시작.")
        while True:
            await asyncio.sleep(20)
            self.ins_sync_storage.data_sync(self.storage_history, self.storage_real_time)
            self.event_history_to_analysis.put(True)

    async def run_open_order(self):
        print(f"  🚀 매수 주문 감시 시작.")
        while True:
            """
            분석 신호의 결과에 따라 주문을 생성한다.
            
            
            Nones:
                Limit 거래시 현재 값보다 높은 가격에 하락 배팅 현재 값보다 낮은 가격에 상승 배팅 가능하다.
            """

            
            
            anlysis_data = self.loop.run_in_executor(None, self.event_mp_anlysis_order.get)
            
            ## get_params << 하나 만들어서 생성할 것. 검토 결과는 Orders의 매개변수값에 맞출 것.
            
            params = {"symbol":'BTCUSDT', "type":"LIMT"}
            
            order_type = params['type']
            
            Orders.set_leverage(**params)
            Orders.set_margin_type(**params)
            send_order = {"MARKET":Orders.open_market_position(**params),
                          "LIMIT":Orders.open_limit_order(**params)}.get(order_type, None)
            # None이 아닐경우 sent_order값을 OrderLog에 저장할 것. 추가 분석 시작.
    
    async def run_close_order(self):
        print(f"  🚀 매도 주문 감시 시작")
        while True:
            """
            모니터링 함수로부터 종료 신호를 받으면,
            포지션을 종료하고
            종료신호를 wallet에 보낸다.    
            """
            monitor_data = self.loop.run_in_executor(None, self.event_mp_monitor_order.get)
            
            ## get_params << 하나 만들어서 생성할 것. 검토 결과는 Orders의 매개변수값에 맞출 것.
            
            params = {"symbol":'BTCUSDT', 'account_balance':1000}
            Orders.close_position(**params)
            
            self.event_order_to_wallet.put(message)
            ...

    async def run_status_message(self):
        print(f"  🚀 상태 메시지 발신 시작.")
        while True:
            """
            주기적으로 월렛정보, 거래정보 등 기타 트렌드 를 정리해서 발송한다.
            """
            ...
    
    async def start(self):
        """
        전체를 실행시킨다.
        """
        ...

if __name__ == "__main__":
    import Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket as futures_wse
    import Workspace.DataStorage.DataStorage as storage
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    
    import os, sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    
    api_path = SystemConfig.Path.bianace
    api_key = base_utils.load_json(api_path)
    api = api_key['apiKey']
    
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    async def main():
        storage_real_time = storage.SymbolStorage(storage.IntervalStorage)
        storage_history = storage.SymbolStorage(storage.IntervalStorage)
        print(api)
        futures_ws_exe = futures_wse.FuturesExcutionWebsocket(api)
        futures_ws_receiver = futures_ws.FuturesWebsocketReceiver(symbols)
        await futures_ws_receiver.setup_kline_stream(intervals)

        # print(True)
        # storage_real_time = storage.SymbolStorage(storage.IntervalStorage)
        # history_stroage = storage.SymbolStorage(storage.IntervalStorage)
        
        dummy = AsyncioWorks(symbols, intervals, storage_real_time, storage_history, futures_ws_receiver, futures_ws_exe)
        
        p1 = asyncio.create_task(dummy.run_trading_websocket())
        p2 = asyncio.create_task(dummy.run_excute_websocket())
        p3 = asyncio.create_task(dummy._run_update_listen_key())
        await asyncio.gather(p1, p2, p3)
    asyncio.run(main())