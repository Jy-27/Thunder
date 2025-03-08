from typing import Dict, List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.DataStorage.DataCollector.NodeStorage import MainStorage, SubStorage
from SystemConfig import Streaming

symbols = Streaming.symbols
intervals = Streaming.intervals

class DepthAnalysisStroage:
    def __init__(self):
        self.__sub_field = ["imbalance", "large_buy_orders_detected", "large_sell_orders_detected", "cumulative_delta_volume"]
        self.__sub_storage = SubStorage(self.__sub_field)
        self.storage = MainStorage(symbols, self.__sub_storage)

class KlineHistoryStorage:
    def __init__(self):
        self.__sub_field = [f"interval_{i}" for i in intervals]
        self.__sub_storage = SubStorage(self.__sub_field)
        self.stroage = MainStorage(symbols, self.__sub_storage)
        
class KlineRealTimeStorage:
    def __init__(self):
        self.__sub_field = [f"interval_{i}" for i in intervals]
        self.__sub_storage = SubStorage(self.__sub_field)
        self.stroage = MainStorage(symbols, self.__sub_storage)
    