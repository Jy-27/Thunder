
import numpy as np
import MarketDataFetcher
import asyncio
import nest_asyncio
import BinanceBackTest
import utils
import os
import pickle
import Analysis

nest_asyncio.apply()

symbols = ['BTCUSDT', 'ADAUSDT', 'XRPUSDT']
intervals = ['1m', '3m', '5m', '1h']

BBT = BinanceBackTest.DataManager(symbols=symbols,
                                  intervals=intervals,
                                  start_date='2024-1-1',# 00:00:00',
                                  end_date='2024-1-5')# 23:59:59')
path = os.path.join(os.path.dirname(os.getcwd()), 'DataStore/kline_data.json')
data = utils._load_json(file_path=path)
# kline_data = asyncio.run(BBT.generate_kline_interval_data(save=True))
kline_data = utils._convert_to_array(kline_data=data)
kline_data = BBT.generate_kline_closing_sync(kline_data=kline_data, save=True)
symbol_map, interval_map, data_c = utils._convert_to_container(kline_data)
BBT.get_indices_data(data_container=data_c, lookback_days=1)

obj_analysis = Analysis.AnalysisManager()


class analysis:
    def __init__(self):
        self.case_1 = []
        self.case_2 = []

    def clear_(self):
        self.case_1.clear()
        self.case_2.clear()
obj_dummy = analysis()

for idx, d in enumerate(data_c.get_data('map_1m')):
    for interval in intervals:
        maps_ = data_c.get_data(f'map_{interval}')[idx]
        # if interval == "5m":
        data = data_c.get_data(f'interval_{interval}')[maps_]
        
        obj_analysis.case_2_candle_length(kline_data_lv3=data)
        obj_analysis.case_3_continuous_trend_position(kline_data_lv3=data)
        obj_analysis.case_4_process_neg_counts(kline_data_lv3=data, col=7)
        obj_analysis.case_5_diff_neg_counts(kline_data_lv3=data, col1=1, col2=4)
        print(maps_[0])
    if idx==5504:
        break
    obj_analysis.reset_cases()
    utils._std_print(idx)
# print(obj_dummy)
        # if interval == '1h':
        #     obj_dummy.case_2.append(data.get_data(f'interval_{interval}')[maps_])
        # obj_dummy.case_1 + obj_dummy.case_2
        # obj_dummy.clear_()
        