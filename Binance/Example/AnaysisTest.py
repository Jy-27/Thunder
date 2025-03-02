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
    def __init__(self, ma:indicator_ma, macd):
        self.ma = ma
        self.macd = macd
        self.dataset = self.ma.dataset