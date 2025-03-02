import StorageSyncTest
import asyncio


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Processor.Analysis.Analysis as anl

obj = StorageSyncTest.StorageSyncTest()
asyncio.run(obj.main())
history = obj.history

fields = history.get_fields()


data = obj.history.get_data("BTCUSDT", "interval_3m")

indicator_ma = anl.IndicatorMA(data)
indicator_macd = anl.IndicatorMACD(data)

indicator_ma.run()
indicator_macd.run()

class SellStrategy1:
    def __init__(self, ma:anl.IndicatorMA, macd:anl.IndicatorMACD):
        self.ma = ma
        self.macd = macd
        self.dataset = self.ma.kline_datasets
        self.periods = self.ma.periods
        self.ma_type = "sma"
        
    def run(self):
        result = {}
        
        ma_1 = getattr(self.ma, f"{self.ma_type}_{self.periods[0]}")
        ma_2 = getattr(self.ma, f"{self.ma_type}_{self.periods[1]}")
        ma_3 = getattr(self.ma, f"{self.ma_type}_{self.periods[2]}")
        
        histogram = getattr(self.macd, f"{self.ins_macd.type_str}_histogram")
        signal_line = getattr(self.macd, f"{self.ins_macd.type_str}_signal")
        macd_line = getattr(self.macd, f"{self.ins_macd.type_str}_macd")