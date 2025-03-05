import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Receiver.Futures.Public.KlineCycleFetcher import KlineCycleFetcher
from Workspace.Receiver.Futures.Public.KlineReceiverFecther import KlineReceiverWebsocket
from Workspace.Receiver.Futures.Public.StreamReceiverWebsocket import StreamReceiverWebsocket
from Workspace.Receiver.Futures.Private.ExecutionReceiverWebsocket import ExecutionReceiverWebsocket

class ReceiverManager:
    def __init__(self):
        self.queue_kline_fetcher = asyncio.Queue()
        self.queue_kline_ws = asyncio.Queue()
        self.queue_aggTrade_ws = asyncio.Queue()
        self.queue_depth_ws = asyncio.Queue()
        self.queue_execution_ws = asyncio.Queue()
        
        self.kline_cycle_fetcher = KlineCycleFetcher(self.queue_kline_fetcher)
        self.kline_receiver_ws = KlineReceiverWebsocket(self.queue_kline_ws)
        self.aggTrade_receive_ws = StreamReceiverWebsocket("aggTrade", self.queue_aggTrade_ws)
        self.depth_receive_ws = StreamReceiverWebsocket("depth", self.queue_depth_ws)
        self.execution_receiver_ws = ExecutionReceiverWebsocket(self.queue_execution_ws)
        
    async def _queue_kline_fetcher(self):
        while True:
            data = await self.queue_kline_fetcher.get()
            print(f" 1")
            self.queue_kline_fetcher.task_done()
            
    async def _queue_kline_ws(self):
        while True:
            data = await self.queue_kline_ws.get()
            print(f"   2")
            # print(data)
            self.queue_kline_ws.task_done()
            
    async def _queue_aggTrade_ws(self):
        while True:
            data = await self.queue_aggTrade_ws.get()
            print(f"     3")
            # print(data)
            self.queue_aggTrade_ws.task_done()
            
    async def _queue_depth_ws(self):
        while True:
            data = await self.queue_depth_ws.get()
            print(f"       4")
            # print(data)
            self.queue_depth_ws.task_done()
            
    async def _queue_execution_ws(self):
        while True:
            data = await self.queue_execution_ws.get()
            print(f"         5")
            # print(data)
            self.queue_execution_ws.task_done()
            
    async def start(self):
        tasks = [
            self.kline_cycle_fetcher.start(),
            self.kline_receiver_ws.start(),
            self.aggTrade_receive_ws.start(),
            self.depth_receive_ws.start(),
            self.execution_receiver_ws.start(),
            self._queue_kline_fetcher(),
            self._queue_kline_ws(),
            self._queue_aggTrade_ws(),
            self._queue_depth_ws(),
            self._queue_execution_ws()
        ]
        await asyncio.gather(*tasks)
    
if __name__ == "__main__":
    obj = ReceiverManager()
    asyncio.run(obj.start())