# Asyncio Loop 처리 집중화


import asyncio
import json
#nest injection
import Workspace.Processor.Receiver.KlineCycle as KlineCycle

#DependencyCreate
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket

#DepedencyInjection
from Workspace.DataStorage.NodeStorage import MainStorage, SubStorage
from Workspace.Processor.Receiver.KlineCycle import KlineCycle
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient

from abc import ABC, abstractclassmethod

class Loop(ABC):
    @abstractclassmethod
    async def run_market_websocket(self):
        pass
    
    @abstractclassmethod
    async def run_execution_websocket(self):
        pass
    
    @abstractclassmethod
    async def run_messing(self):
        pass

    @abstractclassmethod
    async def run_create_event(self):
        pass
    

class AsyncioLoop(Loop):
    def __init__(self, kline_cycle:KlineCycle, execution_ws: FuturesExecutionWebsocket, real_time:MainStorage, telegram:TelegramClient, event_to_wallet:asyncio.Event, event_to_start:asyncio.Event):
        #DependencyCreate
        self.ins_market_fetcher = FuturesMarketFetcher()
        self.ins_kline_cycle = kline_cycle

        # kline attr
        self.symbols = self.ins_kline_cycle.symbols
        self.intervals = self.ins_kline_cycle.intervals
        self.storage_history = self.ins_kline_cycle.storage

        self.ins_market_ws = FuturesMarketWebsocket(self.symbols)
        self.ins_execution_ws = execution_ws
        self.ins_telegram = telegram

        self.storage_real_time = real_time
        
        self.event_to_wallet = event_to_wallet
        self.event_to_start = event_to_start

    async def run_market_websocket(self):
        await self.ins_market_ws.open_connection(self.intervals)
        print(f"  🔗 Websocket(Market) Connect!!")
        while True:
            message = await self.ins_market_ws.receive_message()
            # print(f" TEST PRINT: {message}")
            
            kline_data = message["data"]["k"]
            symbol = kline_data["s"]
            interval = f"interval_{kline_data["i"]}"
            self.storage_real_time.set_data(symbol, interval, kline_data)
        await self.ins_market_ws.close_connection()
        print(f"  ⛓️‍💥 Websocket(Market) Disconnected!")

    async def run_execution_websocket(self):
        await self.ins_execution_ws.open_connection()
        print(f"  🔗 Websocket(Execution) Connect!!")
        while True:
            message = str(await self.ins_execution_ws.receive_message())
            self.ins_telegram.send_message(message)
            self.event_to_wallet.set()
        await self.ins_execution_ws.close_connection()
        print(f"  ⛓️‍💥 Websocket(Execution) Disconnected!")

    async def run_messing(self):
        print(f"  🚀 Telegram Messing Start!!")
        while True:
            target_symbol = self.symbols[0]
            target_interval = f"interval_{self.intervals[0]}"
            message = str(self.storage_real_time.get_data(target_symbol, target_interval))
            self.ins_telegram.send_message(message)
            await asyncio.sleep(10)

    async def run_create_event(self):
        print(f"  🚀 Event Signal Create satrt!")
        while True:
            await asyncio.sleep(20)
            self.event_to_wallet.set()
    

    async def start(self):
        task_1 = asyncio.create_task(self.ins_kline_cycle.start())
        task_2 = asyncio.create_task(self.run_market_websocket())
        task_3 = asyncio.create_task(self.run_create_event())
        task_4 = asyncio.create_task(self.run_messing())
        task_5 = asyncio.create_task(self.run_execution_websocket())

        print(f"  🚀 TASK START!!")
        await asyncio.gather(task_1, task_2, task_3, task_4, task_5)

if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    import Workspace.Services.PrivateAPI.Messaging.TelegramClient as telegram_client
    
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    path_binance_api = SystemConfig.Path.bianace
    path_telegram_api = SystemConfig.Path.telegram
    
    
    print(symbols)
    
    binance_api = base_utils.load_json(path_binance_api)
    teltegram_api = base_utils.load_json(path_telegram_api)

    convert_to_intervals = [f"interval_{i}" for i in intervals]
    sub_storage = SubStorage(convert_to_intervals)
    history = MainStorage(symbols, sub_storage)
    
    kline_cycle = KlineCycle(symbols, intervals, history)
    execution_ws = FuturesExecutionWebsocket(**binance_api)
    real_time = MainStorage(symbols, sub_storage)
    telegram_client = TelegramClient(**teltegram_api)
        
    event_1 = asyncio.Event()
    event_2 = asyncio.Event()
    
    obj = AsyncioLoop(kline_cycle, execution_ws, real_time, telegram_client, event_1, event_2)
    asyncio.run(obj.start())