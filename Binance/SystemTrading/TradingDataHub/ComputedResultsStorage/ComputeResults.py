import asyncio
from typing import Optional, Any

import sys, os
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
from Workspace.DataStorage.StorageOverwrite import StorageOverwrite
from SystemConfig import Streaming
from Workspace.DataStorage.StorageRecorder import StorageRecorder

symbols = tuple(Streaming.symbols)
recorder_storage = StorageRecorder()

queues = []
for _ in range(2):
    queues.append(asyncio.Queue())
event = asyncio.Event()

class CalculatorResults(StorageOverwrite):
    def __init__(self, ):
        super().__init__(base_type=recorder_storage)

    def get_fields_tree(self):
        result = {}
        for slot in self.__class__.__slots__:
            result[slot] = getattr(self, slot).get_fields()
        return result
    
    def get_data(self, main_field:str, sub_field:str):
        return getattr(self, main_field).get_data(sub_field)

if __name__ == "__main__":
    import numpy as np
    dummy_data = [1,1,2,3,1,4,1,2,4,5,5,10]
    dummy_array = np.array(dummy_data, float)
    sma = "sma"
    wma = "wma"
    ema = "ema"
    
    instance = CalculatorResults()
    instance.BTCUSDT.set_data(sma, dummy_array)
    instance.BTCUSDT.set_data(wma, dummy_array)
    instance.BTCUSDT.set_data(ema, dummy_array)
    print(instance.get_fields_tree())