# 백테스팅을 위한 코드 // for loop 사용함.abs
import pandas as pd
import mplfinance as mpf  # type: ignore
import utils
import os
import numpy as np
import talib as ta  # type: ignore

import datetime
from typing import List, Final, Optional, Any, Dict, Union


class BackTestManager:
    def __init__(self):
        self.INTERVALS: List[str] = ["3m", "5m", "15m", "30m"]
        self.BASE_PATH: str = "/Users/nnn/Desktop/DataStore/KlineData"
        self.OHLCV_COLUMNS: Final[List[str]] = [
            "Open_Time",  # 0
            "Open",  # 1
            "High",  # 2
            "Low",  # 3
            "Close",  # 4
            "Volume",  # 5
            "Close_Time",  # 6
            "Quote_Asset_Volume",  # 7
            "Number_of_Trades",  # 8
            "Taker_Buy_Base Asset Volume",  # 9
            "Taker_Buy_Quote Asset Volume",  # 10
            "Ignore",  # 11
        ]

        self.order_history:Dict[list[Dict[str, Union[Any]]]] = []
        
        self.initial_capital = 20
        self.trade_amount_per_trade = 6
        self.fee = 0.05
        
        self.high_low_price = {}

    def load_all_json_files(
        self, directory_path: str
    ) -> Optional[Union[str, Dict[str, Any]]]:
        # 디렉토리 내 파일 목록을 가져옴
        try:
            file_list = os.listdir(directory_path)
        except FileNotFoundError:
            return f"Invalid folder path - {directory_path}"

        # JSON 파일 필터링
        json_files = [file for file in file_list if file.endswith(".json")]
        if not json_files:
            return "No JSON files found in the directory."

        # 결과를 저장할 딕셔너리 초기화
        data_by_symbol = {}

        for file_name in json_files:
            symbol = file_name.split(".")[
                0
            ].upper()  # 파일명에서 심볼 추출 및 대문자로 변환
            file_path = os.path.join(directory_path, file_name)

            try:
                data_by_symbol[symbol] = utils._load_json(
                    file_path
                )  # JSON 파일을 로드하여 심볼에 매핑
            except Exception as e:
                return f"An error occurred while loading {file_name}: {str(e)}"

        return data_by_symbol

    def generate_order_signal(
        self,
        position_type: str,
        order_category: str,
        asset_symbol: str,
        market_data: list,
    ) -> Dict[str, Any]:
        try:
            open_timestamp = utils._convert_to_datetime(date=market_data[0])
            close_timestamp = utils._convert_to_datetime(date=market_data[6])
        except Exception as e:
            raise ValueError(f"Error converting timestamps: {e}")

        price_at_close = float(market_data[4])

        # 신호 데이터를 딕셔너리에 정리하여 반환
        order_signal = {
            "symbol": asset_symbol,
            "open_time": open_timestamp,
            "close_time": close_timestamp,
            "order_type": order_category,
            "position_type": position_type,
            "price": price_at_close,
        }
        return order_signal

    def stoploss(self, symbol:str, curreunt_price: float):
        loss_percent = 0.02
        stop_loss = 0.75
        order_history = self.order_history.get(symbol)
        entry_price = order_history[-1].get('price')
        
        start_price = entry_price * (1 - loss_percent)
        cals = (stop_loss * (curreunt_price))
        
        

main_path = "/Users/nnn/Desktop/DataStore/KlineData"
data = BackTestManager().load_all_json_files(main_path)


# print('데이터 로딩 완료')

# print('데이터 형태 변형')
# def preprocess_data(data: List):
#     data_literals = utils._convert_nested_list_to_literals(data)
#     return np.array(data_literals)
# print('데이터 형태 변형 완료')

# print('numpy 이동평균선 연산')
# def moving_average(data, window_size: int, index: int=4):
#     weights = np.ones(window_size) / window_size
#     return np.convolve(data[:, index], weights, mode='valid')
# print('numpy 이동평균선 연산 완료')


# # 바이낸스 데이터 (예시 데이터)
# data = load_data.get('BTCUSDT').get('5m')

# INDEX_LEN = len(data)
# STEP_CHECK = 5

# signal_data = []#long(True) & short1(False), 연속1

# n = 0

# for nested_data in data:
#     open_ = float(nested_data[1])
#     high_ = nested_data[2]
#     low_ = nested_data[3]
#     close_ = float(nested_data[4])
#     volume_ = nested_data[5]
#     value_ = nested_data[7]
#     trades_count = nested_data[8]
#     marekt_buy_volume = nested_data[9]
#     market_buy_value = nested_data[10]

#     position = open_ < close_
#     consecutive_long = 0
#     consecutive_short = 0

#     if n != 0 and position:
#         previous_value = signal_data[n-1][1]
#         if previous_value > 0:
#             consecutive_long = previous_value + 1
#         else:
#             consecutive_long = 1

#     elif n !=0 and not position:
#         previous_value = signal_data[n-1][2]
#         if previous_value > 0:
#             consecutive_short = previous_value + 1
#         else:
#             consecutive_short = 1

#     if consecutive_long >=3:
#         order_signal = 'LOLNG'
#     elif consecutive_short >=3:
#         order_signal = 'SHORT'
#     else:
#         order_signal = None
#     signal_data.append([position, consecutive_long, consecutive_short, order_signal])
#     n +=1

# n = 0
# for i in data:
#     if signal_data[n][3]=='LONG' or signal_data[n][3]=='SHORT':
#         print(signal_data[n])
#         print(data[n])
#     n +=1
