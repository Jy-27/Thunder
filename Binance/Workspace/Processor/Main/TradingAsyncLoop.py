# Asyncio Loop 처리 집중화


import asyncio
import json
import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils
from SystemConfig import container


from Workspace.DataStorage.NodeStorage import MainStorage, SubStorage
from Workspace.Processor.Receiver.KlineCycle import KlineCycle
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import (
    FuturesExecutionWebsocket,
)
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient
from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet
from Workspace.DataStorage.ExecutionMessage import ExecutionMessage

class TradingAsyncLoop:
    def __init__(self):
        self.ins_kline_cycle = KlineCycle()

        self.pending_order = PendingOrder()
        self.wallet = wallet(10)
        self.exe_message = container.execution_message

        # kline attr
        self.symbols = self.ins_kline_cycle.symbols
        self.intervals = self.ins_kline_cycle.intervals
        self.storage_history = self.ins_kline_cycle.storage

        self.ins_market_ws = container.futures_market_ws
        self.ins_execution_ws = container.futures_execution_ws

        self.storage_real_time = container.storage_real_data
        self.queue = asyncio.Queue()

    async def run_market_websocket(self):
        await self.ins_market_ws.open_kline_connection(self.intervals)
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
    
    k_cycle = KlineCycle()
    pending_order = PendingOrder(SystemConfig.Streaming.symbols,
                                 container.futures_trading_client)
    wallet = Wallet(5, container.futures_trading_client)
    
    obj = TradingAsyncLoop()
    os.system("clear")
    asyncio.run(obj.start())
