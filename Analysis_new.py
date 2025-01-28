### 초기설정

import asyncio
import MarketDataFetcher
import numpy as np
from pprint import pprint
import DataStoreage
from typing import Dict, List, Final, Optional

class AvgMoving:
    """
    이동평균값을 계산한다.
    """
    def __init__(self, kline_datasets:Dict[str, DataStoreage.KlineData], interval:str='3m', periods: List=[7, 25, 99]):
        self.kline_datasets = kline_datasets
        self.periods:List[int] = periods
        self.interval:str = interval
        self.type_str:Optional[str] = None
    
    def cals_sma(self, data:np.ndarray, period:int) -> np.ndarray:
        """
        단순 이동평균(SMA)을 계산하는 함수
        """
        self.type_str = 'sma'
        prices = data[:, 4]
        return np.convolve(prices, np.ones(period) / period, mode='valid')
    
    def cals_ema(self, data:np.ndarray, period:int) -> np.ndarray:
        """
        지수 이동평균(EMA)을 계산하는 함수
        """
        self.type_str = 'ema'
        prices = data[:, 4]
        ema = np.zeros_like(prices, dtype=float)
        multiplier = 2 / (period + 1)
        
        # 첫 EMA는 SMA로 초기화
        ema[period - 1] = np.mean(prices[:period])
        
        # EMA 계산
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]
        
        return ema[period - 1:]
    
    def cals_wma(self, data:np.ndarray, period:int) -> np.ndarray:
        """
        지수 이동평균(WMA)을 계산하는 함수
        """
        self.type_str = 'wma'
        prices = data[:, 4]
        weights = np.arange(1, period + 1)
        wma = np.convolve(prices, weights / weights.sum(), mode='valid')
        return wma

    def run(self, ma_type:str):
        ma_types:Final[List[str]] = ['sma', 'ema','wma']
        if not ma_type in ma_types:
            raise ValueError(f'type 입력 오류:{ma_type}')

        for symbol, data in self.kline_datasets.items():
            base_data = data.get_data(interval=self.interval)
            array_data = np.array(base_data, float)
            for preiod in self.periods:
                if ma_type == ma_types[0]:
                    setattr(self, f'{symbol}_{ma_type}_{preiod}', self.cals_sma(array_data, preiod))         
                elif ma_type == ma_types[1]:
                    setattr(self, f'{symbol}_{ma_type}_{preiod}', self.cals_ema(array_data, preiod))
                else:
                    setattr(self, f'{symbol}_{ma_type}_{preiod}', self.cals_wma(array_data, preiod))
                    
class AnalysisManager:
    def __init__(self, kline_datasets:Dict[str, DataStoreage.KlineData]):
        self.data_sets = kline_datasets

        self.ins_avg_moving = AvgMoving(self.data_sets)

    def run(self):
        self.ins_avg_moving.run()
        return self.ins_avg_moving
    
