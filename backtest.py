# 백테스팅을 위한 코드 // for loop 사용함.abs

import utils
import os
import pandas as pd
import numpy as np
from typing import List, Final

BASE_PATH: str = "/Users/nnn/Desktop/DataStore/KlineData"
FILES: List[str] = os.listdir(BASE_PATH)
INTERVALS: List[str] = ["3m", "5m", "15m", "30m"]
OHLCV_COLUMNS: Final[List[str]] = [
    "Open_Time",
    "Open",
    "High",
    "Low",
    "Close",
    "Volume",
    "Close_Time",
    "Quote_Asset_Volume",
    "Number_of_Trades",
    "Taker_Buy_Base Asset Volume",
    "Taker_Buy_Quote Asset Volume",
    "Ignore",
]

load_data = {}
for file in FILES:
    if file.endswith('.json'):
        path = os.path.join(BASE_PATH, file)
        print(path)
        symbol = file.split(".")[0].upper()
        load_data[symbol] = utils._load_json(path)

def preprocess_data(data: List):
    data_literals = utils._convert_nested_list_to_literals(data)
    return np.array(data_literals)

def moving_average(data, window_size: int, index: int=4):
    weights = np.ones(window_size) / window_size
    return np.convolve(data[:, index], weights, mode='valid')


# target_data = load_data.get("BTCUSDT").get(INTERVALS[1])
# target_data = preprocess_data(target_data)

# df_ = pd.DataFrame(target_data, columns=OHLCV_COLUMNS)

df_ = {}
for interval in INTERVALS:
    for file in FILES:
        symbol = file.split('.')[0].upper()
        get_data = load_data.get(symbol).get(interval)
        literals_data = preprocess_data(get_data)
        key = f"{symbol}_{interval}"
        df_[key] = pd.DataFrame(get_data, columns=OHLCV_COLUMNS)
        