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
from Workspace.Receiver.Futures.Receiver import ReceiverStorageManager

intervals = SystemConfig.Streaming.intervals
conver_to_intervals = [f"interval_{i}" for i in intervals]
symbols = SystemConfig.Streaming.symbols

sub_storage = SubStorage(conver_to_intervals)

aggTrade_ = aggTradeStorage()
history_ = MainStorage(symbols, sub_storage)
real_time_ = MainStorage(symbols, sub_storage)

path = SystemConfig.Path.bianace
api = base_utils.load_json(path)
tr_client = FuturesTradingClient(**api)

pending_ = PendingOrder(tr_client)
wallet_ = Wallet(tr_client)
depth_ = DepthStorage()
execution_ = ExecutionStorage()

obj = ReceiverStorageManager(wallet_, pending_, history_, real_time_, aggTrade_, depth_, execution_)

class Multiprocessing:
    def __init__(self):
        self.receive_storage_manager = obj,
        self.storage_history:MainStorage = obj.storage_history,
        self.storage_aggTrade:aggTradeStorage = obj.stroage_aggTrade,
        self.storage_depth:DepthStorage = obj.storeage_depth,
        self.time_sleep:int = 30

        self.symbols = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        
        # self.storage_history = storage_history
        # self.storage_aggTrade = storage_aggTrade
        # self.storage_depth = storage_depth
        
        self.time_sleep = 10
        
    def process_task(self, symbol):
        """ 심볼별 데이터를 가져와서 처리하는 함수 """
        history_data = self.storage_history.to_dict(symbol)
        maker_data = self.storage_aggTrade.get_all_data(symbol, "maker")
        taker_data = self.storage_aggTrade.get_all_data(symbol, "taker")
        depth_data = self.storage_depth.get_all_data(symbol)

        return dummy_calculate(history_data, maker_data, taker_data, depth_data)

    def test(self, history, maker_data, taker_data, depth_data):
        return True

    def run(self):
        with concurrent.futures.ProcessPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(self.process_task, self.symbols))
        return results
    async def start(self):
        await obj.start()

if __name__ == "__main__":
    obj = Multiprocessing()
    asyncio.run(obj.start())