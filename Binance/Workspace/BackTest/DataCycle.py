import numpy as np
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.BackTest.DataFactory import FactoryManager
from Workspace.BackTest.Storage.StorageCollector import ClosingSyncStorage, IndicesStorage

class DataCycler:
    def __init__(self,
                 storage_closing_sync_data:ClosingSyncStorage,
                 storage_indices:IndicesStorage):
        self.storage_closing_sync_data = storage_closing_sync_data
        self.storage_indices = storage_indices
        
    def get_data(self, interval:str, iter_no:int):
        indices = self.storage_indices.get_data(interval, iter_no)
        return self.storage_closing_sync_data.get_data(interval, indices)
    
if __name__ == "__main__":
    from Workspace.BackTest.DataFactory import FactoryManager
    import asyncio
    import Workspace.Utils.BaseUtils as base_utils
    import time
    from Workspace.Analysis.Indicator import *
    
    
    
    start_date = "2024-02-24"
    end_date = "2025-03-13"
    
    instance_factory = FactoryManager(start_date, end_date)
    asyncio.run(instance_factory.start(is_save=True))
    # instance_factory.storage_load()
    
    instance_data_cycle = DataCycler(instance_factory.storage_closing,
                                     instance_factory.storage_indices)
    
    # data_emtpy = False
    # idx = 0
    
    # start_time = time.time()
    
    # while not data_emtpy:
    #     try:
    #         data = {}
    #         for i in instance_factory.intervals:
    #             data[i] = {}
    #             if i == "1m":
    #                 sync_data = instance_data_cycle.get_data(i, idx)
    #                 end_timestamp = sync_data[-1][0]
    #                 end_date = base_utils.convert_to_datetime(end_timestamp)
    #                 data[i]["7"] = MA.sma(sync_data[:, 4], 7)
    #                 data[i]["25"] = MA.sma(sync_data[:, 4], 25)
    #                 data[i]["99"] = MA.sma(sync_data[:, 4], 99)
    #         idx += 1
    #     except:
    #         print(f"  👍 데이터 순환 완료")
    #         data_emtpy = True
    
    # end_time = time.time()
    
    # print(f" 소요시간: {end_time - start_time:,.2f}sec")
    
    print(f" 전체 작업 종료")
                    
    
    