### 초기설정

import asyncio
import numpy as np
from pprint import pprint
from typing import Dict, List, Final, Optional
from copy import copy


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Analysis.Indicator import *


def count_consecutive_drops(values:np.ndarray) -> int:
    """
    📉 값의 연속 하락횟수를 연산한다.    

    Args:
        values (np.ndarray): 계산하고자 하는 값(예: prices, values)

    Returns: int
    """
    values_reversed = values[::-1]
    diff = np.diff(values)
    return next((i for i, v in enumerate(diff) if v > 0), len(diff))

def count_consecutive_gains(values:np.ndarray) -> int:
    """
    📈 값의 연속 상승횟수를 연산한다.    

    Args:
        values (np.ndarray): 계산하고자 하는 값(예: prices, values)

    Returns: int
    """
    values_reversed = values[::-1]
    diff = np.diff(values)
    return next((i for i, v in enumerate(diff) if v < 0), len(diff))

def detect_bid_wall(orderbook) -> tuple:
    """
    NumPy를 사용하여 매수벽(Bid Wall)의 가격, 볼륨, 금액, 인덱스를 찾는 함수
    - orderbook["bids"]: [[price, volume], [price, volume], ...]

    반환값:
    - index (int): 최대 볼륨을 가진 행의 인덱스
    - price (float): 매수벽의 가격
    - volume (float): 매수벽의 주문량
    - total_value (float): 총 금액 (price * volume)
    """
    bids = np.array(orderbook["bids"], dtype=float)  # NumPy 배열 변환
    max_idx = int(np.argmax(bids[:, 1]))  # 최대 볼륨 인덱스 찾기

    price = float(bids[max_idx, 0])  # 가격
    volume = float(bids[max_idx, 1])  # 볼륨
    total_value = price * volume  # 총 금액 (price × volume)

    return max_idx, price, volume, total_value

def detect_ask_wall(orderbook) -> tuple:
    """
    NumPy를 사용하여 매수벽(Bid Wall)의 가격, 볼륨, 금액, 인덱스를 찾는 함수
    - orderbook["bids"]: [[price, volume], [price, volume], ...]

    반환값:
    - index (int): 최대 볼륨을 가진 행의 인덱스
    - price (float): 매수벽의 가격
    - volume (float): 매수벽의 주문량
    - total_value (float): 총 금액 (price * volume)
    """
    asks = np.array(orderbook["asks"], dtype=float)  # NumPy 배열 변환
    max_idx = int(np.argmax(asks[:, 1]))  # 최대 볼륨 인덱스 찾기

    price = float(asks[max_idx, 0])  # 가격
    volume = float(asks[max_idx, 1])  # 볼륨
    total_value = price * volume  # 총 금액 (price × volume)

    return max_idx, price, volume, total_value

def short_sma(values:Dict, periods:List):
    conver_to_array = np.array(values, float)
    close_prices = conver_to_array[:, 4]
    
    if conver_to_array[-1, 4] > conver_to_array[-1, 1]:
        return False, 0
    
    if close_prices[-1] > close_prices[-2]:
        return False, 0

    
    for period in periods:
        sma[period] = MA.sma(values, close_prices)