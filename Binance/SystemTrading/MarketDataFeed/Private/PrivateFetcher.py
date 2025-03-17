import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig
import Workspace.Utils.BaseUtils as base_utils
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient

symbols = SystemConfig.Streaming.symbols

path_api = SystemConfig.Path.bianace
api = base_utils.load_json(path_api)
ins_futures_tr_client = FuturesTradingClient(**api)

class PrivateFetcher:
    def __init__(self,
                 queue_account_balance: asyncio.Queue,
                 queue_order_status: asyncio.Queue,
                 queue_order_details: asyncio.Queue,
                 event_start_signal: asyncio.Event,
                 event_loop_start: asyncio.Event):
        self.queue_account_balance = queue_account_balance
        self.queue_order_status = queue_order_status
        self.queue_order_details = queue_order_details
        self.event_start_signal = event_start_signal
        self.event_loop_start = event_loop_start

    async def fetch_account_balance(self):
        data = await ins_futures_tr_client.fetch_account_balance()
        await self.queue_account_balance.put(data)
        return data

    async def fetch_order_status(self, symbol: str):
        data = await ins_futures_tr_client.fetch_order_status(symbol)
        await self.queue_order_status.put(data)
        return data

    async def fetch_all_order_statuses(self):
        tasks = [asyncio.create_task(self.fetch_order_status(symbol)) for symbol in symbols]
        await asyncio.gather(*tasks)

    async def start(self):
        print(f"  🚀 PrivateFetcher 시작.")
        while not self.event_loop_start.is_set():
            await self.event_start_signal.wait()
            await self.fetch_account_balance()
            await self.fetch_all_order_statuses()
            self.event_start_signal.clear()

if __name__ == "__main__":
    queues = []
    for _ in range(3):
        queues.append(asyncio.Queue())
    queues = tuple(queues)
    event_1 = asyncio.Event()
    event_2 = asyncio.Event()
    
    
    obj = PrivateFetcher(*queues, event_1, event_2)
    data = asyncio.run(obj.fetch_all_order_statuses())#("BTCUSDT"))#, 623593178246))