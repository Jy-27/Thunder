from typing import List, Dict, Optional, Any
import numpy as np
import asyncio
import os, sys
import pickle

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig
from Workspace.BackTest.Storage.StorageCollector import ClosingSyncStorage, IndicesStorage
from Workspace.BackTest.DataFactory import FactoryManager

class BacktestManager:
    def __init__(self, start_date:str, end_date:str, save:bool=True):
        self.symbol:List = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        self.storage_closing:Optional[ClosingSyncStorage] = None
        self.storage_indices:Optional[IndicesStorage] = None
        self.ins_data_factory = FactoryManager(start_date, end_date)
        
        self.enabled_save = save
    
    def storage_load(self):
        self.storage_closing, self.storage_indices = self.ins_data_factory.storage_load()
        
    async def data_fetcher(self):
        self.storage_closing, self.storage_indices = await self.ins_data_factory.start(self.enabled_save)

if __name__ == "__main__":
    start_date = "2025-01-01"
    end_date = "2025-01-31"
    instance = BacktestManager(start_date, end_date)
    # asyncio.run(instance.data_fetcher())
    instance.storage_load()
    
    # indices = instance.storage_indices.get_data("3m", 10)
    # data = instance.storage_closing.get_data("3m", indices)
    # print(data)
    
    
        