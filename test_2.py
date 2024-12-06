import numpy as np
import MarketDataFetcher
import asyncio
import nest_asyncio
import BinanceBackTest
import utils
import os

nest_asyncio.apply()


symbols = ['BTCUSDT', 'ADAUSDT', 'XRPUSDT']
intervals = ['1m', '3m', '5m', '1h']

BBT = BinanceBackTest.DataManager(symbols=symbols,
                                  intervals=intervals,
                                  start_date='2024-8-1 00:00:00',
                                  end_date='2024-11-03 23:59:59')
# asyncio.run(BBT.read_data_run(download_if_missing=True))


# range_length_data, kline_data, indices_data, closing_sync_data = asyncio.run(BBT.read_data_run(download_if_missing=False))

path = os.path.join(os.path.dirname(os.getcwd()), 'DataStore/kline_data.json')
kline_data = utils._load_json(file_path=path)
dummy = BBT.convert_kline_data_array(kline_data=kline_data)

dummy_list = []

for symbol, kline_data_symbol in kline_data.items():
    interval_dummy = []
    for interval, kline_data_interval in kline_data_symbol.items():
        interval_dummy.append(kline_data_interval)
    dummy_list.append(interval_dummy)

max_length = max(len(sublist) for sublist in dummy_list)

# 패딩 처리
padded_data = np.array([
    [[0, 0, 0,0,0,0,0,0,0,0,0, 0]] * (max_length - len(sublist)) + sublist if len(sublist) < max_length else sublist[:max_length]
    for sublist in dummy_list
])

print(padded_data)


# # === START

# symbol = 'BTCUSDT'
# target_interval = '3m'

# symbols = list(kline_data.keys())
# interval = list(kline_data[symbols[0]].keys())

# result = {}

# # convert_data = self.convert_kline_data_array(kline_data=kline_data)

# """
# 데이터 생성 순서 (arange 순서.)
# No >> IDX >> INTERVAL >> SYMBOL

# No[ IDX [ INterval [ Symbol[ ]]]]


# No : Range
# IDX : 1분 데이터

# """
# empty_data = []
# for i in dummy[symbol][target_interval]:
#     open_timestamp = i[0]
#     close_timestamp = i[6]
#     condition = np.where((
#         dummy[symbol]['1m'][:,0]>=open_timestamp)&
#     (dummy[symbol]['1m'][:,6]<=close_timestamp))[0]
#     for n in condition:
#         if n == condition[-1]:
#             empty_data.append(i)
#             continue
#         if n == condition[0]:
#             new_data = [
#                 open_timestamp,
#                 dummy[symbol]['1m'][n][1],
#                 dummy[symbol]['1m'][n][2],
#                 dummy[symbol]['1m'][n][3],
#                 dummy[symbol]['1m'][n][4],
#                 dummy[symbol]['1m'][n][5],
#                 close_timestamp,
#                 dummy[symbol]['1m'][n][7],
#                 dummy[symbol]['1m'][n][8],
#                 dummy[symbol]['1m'][n][9],
#                 dummy[symbol]['1m'][n][10],
#                 0,
#             ]
#         else:
#             new_data = [
#                 open_timestamp,
#                 dummy[symbol]['1m'][n][1],
#                 max(dummy[symbol]['1m'][n][2], empty_data[-1][2]),
#                 min(dummy[symbol]['1m'][n][3], empty_data[-1][3]),
#                 dummy[symbol]['1m'][n][4],
#                 dummy[symbol]['1m'][n][5] + empty_data[-1][5],
#                 close_timestamp,
#                 dummy[symbol]['1m'][n][7] + empty_data[-1][7],
#                 dummy[symbol]['1m'][n][8] + empty_data[-1][8],
#                 dummy[symbol]['1m'][n][9] + empty_data[-1][9],
#                 dummy[symbol]['1m'][n][10] + empty_data[-1][10],
#                 0,
#             ]
#         empty_data.append(new_data)