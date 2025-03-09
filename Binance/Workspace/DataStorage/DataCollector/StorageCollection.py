from typing import Dict, List
from collections import deque

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.DataStorage.DataCollector.NodeStorage import MainStorage, SubStorage
from SystemConfig import Streaming

symbols = Streaming.symbols
intervals = Streaming.intervals

class DepthAnalysisStroage:
    def __init__(self):
        self.__sub_fields = ["imbalance", "large_buy_orders_detected", "large_sell_orders_detected", "cumulative_delta_volume"]
        self.__sub_storage = SubStorage(self.__sub_fields)
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
class OrderbookStorage:
    def __init__(self, maxlen:int=300):
        """
        Streaming.symbols 리스트를 기반으로 속성을 생성하고,
        각 속성을 deque(maxlen=100)으로 초기화.
        """
        for symbol in Streaming.symbols:
            setattr(self, symbol, deque(maxlen=maxlen))  # ✅ 올바른 deque 초기화

    def add_data(self, attr_name:str, data):
        """
        데이터를 저장한다.

        Args:
            attr_name (str): symbol
            data (_type_): weboskcet orderbook data
        """
        getattr(self, attr_name).append(data)

    def get_data(self, attr_name:str) -> List:
        """
        데이터를 불러온다.

        Args:
            attr_name (str): symbol

        Returns:
            List: websocket orderbook data
        """
        return list(getattr(self, attr_name))
    
    def clear(self, attr_name:str):
        """
        데이터를 비운다.

        Args:
            attr_name (str): symbol
        """
        getattr(self, attr_name).clear()

