import asyncio
import multiprocessing
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.DataStorage.DataCollector.NodeStorage import MainStorage, SubStorage
from Workspace.DataStorage.DataCollector.aggTradeStorage import aggTradeStorage
from Workspace.DataStorage.DataCollector.DepthStorage import DepthStorage
import SystemConfig
import Workspace.Utils.BaseUtils as base_utils
from Workspace.DataStorage.DataCollector.aggTradeStorage import aggTradeStorage
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient
from Workspace.DataStorage.DataCollector.ExecutionStorage import ExecutionStorage
from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet
from Workspace.Receiver.Futures.Receiver_den import ReceiverStorageManager

intervals = SystemConfig.Streaming.intervals
conver_to_intervals = [f"interval_{i}" for i in intervals]
symbols = SystemConfig.Streaming.symbols

receiver_storage_manager = ReceiverStorageManager()

class Multiprocessing:
    def __init__(self):
        self.receive_storage_manager = receiver_storage_manager
        self.storage_history:MainStorage = self.receive_storage_manager.storage_history
        self.storage_aggTrade:aggTradeStorage = self.receive_storage_manager.stroage_aggTrade
        self.storage_depth:DepthStorage = self.receive_storage_manager.storeage_depth
        self.time_sleep:int = 30

        self.symbols = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        self.conver_to_intervals = [f"interval_{i}"for i in self.intervals]

        self.queue_mp = multiprocessing.Queue()
        
        self.time_sleep = 10

    def process_task(self, symbol):
        """ 심볼별 데이터를 가져와서 처리하는 함수 """
        history_data = self.storage_history.to_dict(symbol)
        maker_data = self.storage_aggTrade.get_all_data(symbol, "maker")
        taker_data = self.storage_aggTrade.get_all_data(symbol, "taker")
        depth_data = self.storage_depth.get_all_data(symbol)

        return dummy_calculate(history_data, maker_data, taker_data, depth_data)

    def test(self, history, maker_data, taker_data, depth_data):
        return history

    def run(self):
        processes = [multiprocessing.Process(target=self.process_wrapper, args=(symbol, queue)) for symbol in self.symbols]
        for p in processes:
            p.start()
        results = []
        for _ in processes:
            results.append(self.queue_mp.get())
        for p in process:
            p.join()
        return results

    async def start(self):
        await self.receive_storage_manager.start()

if __name__ == "__main__":
    obj = Multiprocessing()
    asyncio.run(obj.start())
    obj.run()