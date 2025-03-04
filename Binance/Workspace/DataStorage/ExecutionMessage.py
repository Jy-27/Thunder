from typing import Dict, List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.DataStorage.NodeStorage import MainStorage, SubStorage

class ExecutionMessage:
    """
    Execution Websoket Last Message를 저장한다.
    저장된 데이터를 활용하여 현재 포지션 정보를 획득한다.
    레버리지 정보는 알 수 없다.
    """
    def __init__(self, symbols:List):
        self.symbols = symbols
        self.event_types = ["TRADE_LITE", "ORDER_TRADE_UPDATE", "ACCOUNT_UPDATE", ]
        self.storage = MainStorage(symbols, SubStorage(self.event_types))
    
    def set_data(self, message:Dict):
        data_type = message["e"]
        if data_type == "TRADE_LITE":
            symbol = message["s"]
        elif data_type == "ORDER_TRADE_UPDATE":
            symbol = message["o"]["s"]
        elif data_type == "ACCOUNT_UPDATE":
            symbol = message['a']['P'][0]['s']
        self.storage.set_data(symbol, data_type, message)
        
    def get_data(self, symbol:str, event_type:str):
        return self.storage.get_data(symbol, event_type)
    
    def clear(self, symbol:str):
        self.storage.clear_all(symbol)
    
    def to_dict(self):
        return self.storage.to_dict()