import asyncio
import nest_asyncio
import numpy as np

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher as futures_mk_fetcher
import Workspace.DataStorage.NodeStorage as storage
import Workspace.Analysis.Indicator as indicator
import SystemConfig

nest_asyncio.apply()

symbols = SystemConfig.Streaming.symbols
intervals = SystemConfig.Streaming.intervals
convert_to_intervals = [f"interval_{i}" for i in intervals]
limit = 1000

sub_storage = storage.SubStorage(convert_to_intervals)
main_storage = storage.MainStorage(symbols, sub_storage)

obj = futures_mk_fetcher.FuturesMarketFetcher()

for symbol in symbols:
    for interval in intervals:
        fetcher_data = obj.fetch_klines_limit(symbol, interval, limit)
        conver_to_interval = f"interval_{interval}"
        main_storage.set_data(symbol, conver_to_interval, fetcher_data)
        
get_data = main_storage.get_data("BTCUSDT", "interval_3m")
conver_to_array = np.array(get_data, float)
prices = conver_to_array[:, 4]

sma = {}
ema = {}
wma = {}
rsi = {}
periods = [7, 25, 99]
for period in periods:
    sma[period] = indicator.MA.sma(values=prices, period=period)
    ema[period] = indicator.MA.ema(values=prices, period=period)
    wma[period] = indicator.MA.wma(values=prices, period=period)
    rsi[period] = indicator.RSI.wilder(values=prices, window=period)    
