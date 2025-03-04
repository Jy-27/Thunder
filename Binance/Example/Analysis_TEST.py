import StorageSyncTest
import asyncio
import numpy as np


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace
import Workspace.Analysis.Indicator as indicator
import Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher as futures_mk_fetcher
import Workspace.Utils.BaseUtils as base_utils
from typing import Dict, List


mk_fetcher = futures_mk_fetcher.FuturesMarketFetcher()


mk_fetcher.fetch_klines_date

obj = StorageSyncTest.StorageSyncTest()
asyncio.run(obj.main())
history = obj.history

fields = history.get_fields()


data = obj.history.get_data("BTCUSDT", "interval_3m")

indicator_ma = indicator.MA
indicator_macd = indicator.MACD

indicator_ma.run()
indicator_macd.run()

class SellStrategy1:
    def __init__(self, ma:indicator.MA, macd:indicator.MACD, prices:np.ndarray, periods:List=[7, 25, 99]):
        self.ma = ma
        self.macd = macd
        self.dataset = dataset
        self.periods = periods
        
        self.ma_1 = None
        self.ma_2 = None
        self.ma_3 = None

        self.histogram = None
        self.signal_line = None
        self.macd_line = None
        
    def run(self):
        result = {}
        self.ma_1 = ma.sma(self.dataset, period=self.periods[0])
        self.ma_2 = ma.sma(self.dataset, period=self.periods[1])
        self.ma_3 = ma.sma(self.dataset, period=self.periods[2])
        
        self.line = self.macd.line(values=self.dataset)
        self.signal_line = self.macd.signal_line(values=self.dataset)
        self.macd_line = self.macd.histogram(values=self.dataset)
        


if __name__ == "__main__":
    obj = SellStrategy1(indicator_ma, indicator_macd)
    obj.run()
    
    split_array = np.array_split(obj.ma_3, 10)

    means = [np.mean(data) for data in split_array]
    
    # idx = 1
    # for data in means:
    #     if means[idx] < data:
    #         print(f" {len(means)} / {idx}")
    #         idx += 1