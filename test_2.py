import utils
import numpy as np

data = utils._load_json(file_path='/Users/cjupit/Documents/GitHub/DataStore/kline_data.json')

all_ = []

map_symbol = {}
map_interval = {}

symbols_out = [
    "XRPUSDT",
    "ADAUSDT",
    "NOTUSDT",
    "SANDUSDT",
    "ARKMUSDT",
    "SOLUSDT",
    "DOGEUSDT",
]



for idx_s, (symbol, kline_data_symbol) in enumerate(data.items()):
    if symbol in symbols_out:
        continue
    map_symbol[symbol] = idx_s
    for idx_i, (interval, kline_data_interval) in enumerate(kline_data_symbol.items()):
        map_interval[interval] = idx_i
        all_.append(kline_data_interval)

max_length = max(len(row) for row in all_)

# 패딩된 2D 배열 생성
padded_array = np.array([
    np.pad(row, (0, max_length - len(row)), constant_values=0) for row in all_
])