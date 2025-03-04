# Asyncio Loop 처리 집중화


import asyncio
import json
#nest injection
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Processor.Receiver.KlineCycle as KlineCycle
import Workspace.Utils.TradingUtils as tr_utils

#DependencyCreate
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket

#DepedencyInjection
from Workspace.DataStorage.NodeStorage import MainStorage, SubStorage
from Workspace.Processor.Receiver.KlineCycle import KlineCycle
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient

from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet
from Workspace.DataStorage.ExecutionMessage import ExecutionMessage

class TradingAsyncLoop:
    def __init__(self, kline_cycle:KlineCycle, execution_ws: FuturesExecutionWebsocket, real_time:MainStorage, pending_order:PendingOrder, wallet:Wallet, exe_message:ExecutionMessage):#, event_to_wallet:asyncio.Event):
        #DependencyCreate
        self.ins_kline_cycle = kline_cycle

        self.pending_order = pending_order
        self.wallet = wallet
        self.exe_message = exe_message

        # kline attr
        self.symbols = self.ins_kline_cycle.symbols
        self.intervals = self.ins_kline_cycle.intervals
        self.storage_history = self.ins_kline_cycle.storage

        self.ins_market_ws = FuturesMarketWebsocket(self.symbols)
        self.ins_execution_ws = execution_ws

        self.storage_real_time = real_time
        self.queue = asyncio.Queue()

    async def run_market_websocket(self):
        await self.ins_market_ws.open_connection(self.intervals)
        print(f"  🔗 Websocket(Market) Connect!!")
        while True:
            message = await self.ins_market_ws.receive_message()
            symbol, interval = tr_utils.Extractor.format_websocket(message)
            convert_to_interval = f"interval_{interval}"
            kline_data = tr_utils.Extractor.format_kline_data(message)
            self.storage_real_time.set_data(symbol, convert_to_interval, kline_data)
        await self.ins_market_ws.close_connection()
        print(f"  ⛓️‍💥 Websocket(Market) Disconnected!")

    async def run_execution_websocket(self):
        await self.ins_execution_ws.open_connection()
        print(f"  🔗 Websocket(Execution) Connect!!")
        while True:
            message = str(await self.ins_execution_ws.receive_message())
            await self.queue.put(message)
        await self.ins_execution_ws.close_connection()
        print(f"  ⛓️‍💥 Websocket(Execution) Disconnected!")

    async def run_update(self):
        print("  🔄 Data Sync start")
        while True:
            message = await self.queue.get()
            await self.wallet.update_balance()
            self.pending_order.update_order(message)
            self.exe_message.set_data(message)
    
    async def start(self):
        task_1 = asyncio.create_task(self.ins_kline_cycle.start())
        task_2 = asyncio.create_task(self.run_market_websocket())
        task_3 = asyncio.create_task(self.run_execution_websocket())
        task_4 = asyncio.create_task(self.run_update())

        await asyncio.gather(task_1, task_2, task_3, task_4)

if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    import Workspace.Services.PrivateAPI.Messaging.TelegramClient as telegram_client
    import Workspace.Services.PrivateAPI.Trading.FuturesTradingClient as futures_tr_client
    import os
    from Workspace.Processor.Wallet.Wallet import Wallet
    from Workspace.DataStorage.ExecutionMessage import ExecutionMessage

    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    path_binance_api = SystemConfig.Path.bianace
    path_telegram_api = SystemConfig.Path.telegram
        
    binance_api = base_utils.load_json(path_binance_api)
    teltegram_api = base_utils.load_json(path_telegram_api)

    convert_to_intervals = [f"interval_{i}" for i in intervals]
    sub_storage = SubStorage(convert_to_intervals)
    history = MainStorage(symbols, sub_storage)
    
    kline_cycle = KlineCycle(symbols, intervals, history)
    execution_ws = FuturesExecutionWebsocket(**binance_api)
    real_time = MainStorage(symbols, sub_storage)
    telegram_client = TelegramClient(**teltegram_api)
    
    path = SystemConfig.Path.bianace
    api = base_utils.load_json(path)
    tr_client = futures_tr_client.FuturesTradingClient(**api)
    pending = PendingOrder(symbols, tr_client)
    wallet_ = Wallet(5, tr_client)
    exe_message = ExecutionMessage(symbols)
    
    obj = TradingAsyncLoop(kline_cycle, execution_ws, real_time, pending, wallet_, exe_message)
    os.system("clear")
    asyncio.run(obj.start())