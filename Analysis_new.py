### 초기설정

import asyncio
import MarketDataFetcher
import numpy as np
import DataStoreage
import utils
from pprint import pprint
from typing import Dict, List, Final, Optional
from copy import copy

class IndicatorMA:
    """
    이동평균값을 계산한다.
    """

    def __init__(
        self,
        kline_datasets: Dict[str, DataStoreage.KlineData],
        data_type: str = "sma",
        interval: str = "3m",
        periods: List = [7, 25, 99],
    ):
        self.kline_datasets = kline_datasets
        self.periods: List[int] = periods
        self.interval: str = interval
        self.type_str: str = data_type
        self.ma_types: Final[List[str]] = ["sma", "ema", "wma"]

    def cals_sma(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        단순 이동평균(SMA)을 계산하는 함수
        """
        self.type_str = "sma"
        prices = data[:, 4]
        return np.convolve(prices, np.ones(period) / period, mode="valid")

    def cals_ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        지수 이동평균(EMA)을 계산하는 함수
        """
        self.type_str = "ema"
        prices = data[:, 4]
        ema = np.zeros_like(prices, dtype=float)
        multiplier = 2 / (period + 1)

        # 첫 EMA는 SMA로 초기화
        ema[period - 1] = np.mean(prices[:period])

        # EMA 계산
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema[period - 1 :]

    def cals_wma(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        지수 이동평균(WMA)을 계산하는 함수
        """
        self.type_str = "wma"
        prices = data[:, 4]
        weights = np.arange(1, period + 1)
        wma = np.convolve(prices, weights / weights.sum(), mode="valid")
        return wma

    def run(self):
        if not self.type_str in self.ma_types:
            raise ValueError(f"type 입력 오류:{self.type_str}")

        ma_func = {"sma": self.cals_sma, "ema": self.cals_ema, "wma": self.cals_wma}

        for symbol, data in self.kline_datasets.items():
            base_data = data.get_data(interval=self.interval)
            array_data = np.array(base_data, float)
            for preiod in self.periods:
                result = ma_func[self.type_str](data=array_data, period=preiod)
                setattr(self, f"{symbol}_{self.type_str}_{preiod}", result)

class IndicatorMACD:
    def __init__(self, kline_datasets: Dict[str, DataStoreage.KlineData],
                 interval:str = "3m",
                 data_type:str = 'macd',
                 col_index:int = 4,
                 short_window: int=12,
                 long_window: int=26,
                 signal_window:int=9):
        self.kline_datasets = kline_datasets = kline_datasets
        self.interval = interval
        self.type_str = data_type
        self.col_index = col_index
        self.short_window = short_window
        self.long_window = long_window
        self.signal_window = signal_window
    
    def __ema(self, data: np.ndarray, window: int) -> np.ndarray:
        """EMA 계산 (데이터 길이 유지)"""
        alpha = 2 / (window + 1)
        ema_values = np.empty_like(data, dtype=np.float64)
        ema_values[0] = data[0]  # 초기값 설정

        for i in range(1, len(data)):
            ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i - 1]

        return ema_values

    def macd(self, data: np.ndarray, col_index:int=4,  short_window: int = 12, long_window: int = 26, signal_window: int = 9):
        value = data[:,col_index]
        macd_line = self.__ema(value, short_window) - self.__ema(value, long_window)
        signal_line = self.__ema(macd_line, signal_window)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram 
    
    def run(self):
        for symbol, data in self.kline_datasets.items():
            base_data = data.get_data(interval=self.interval)
            array_data = np.array(base_data, float)
            
            result = self.macd(data=array_data, col_index=self.col_index, short_window=self.short_window, long_window=self.long_window, signal_window=self.signal_window)
            setattr(self, f'{symbol}_{self.type_str}_{self.short_window}_{self.long_window}_{self.signal_window}', result)
    
class IndicatorRSI:
    ...
    
class IndicatorOscillator:
    ...

class SellStrategy1:
    """
    Short 포지션 관련 분석
    """

    def __init__(self, ma_data: IndicatorMA, macd_data:IndicatorMACD):
        self.ins_ma = ma_data
        self.ins_macd = macd_data

        self.kline_datasets = self.ins_ma.kline_datasets
        self.periods = self.ins_ma.periods
        self.interval = self.ins_ma.interval
        self.type_str = self.ins_ma.type_str

        # 어떻게 결과물을 발생시킬지 검토필요함.
        self.result: Optional[list[int]] = None

        # 상태(True/False) / position(1/2) / class number(1)
        self.fail_message: List = [0, 2, 1, 0]
        self.success_message: List = [1, 2, 1]

    def reset_message(self):
        self.fail_message: List = [0, 2, 1, 0]
        self.success_message: List = [1, 2, 1]

    def run(self):
        symbols = list(self.kline_datasets.keys())
        result = {}
        for symbol in symbols:
            ma_1 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[0]}"
            )  # 7
            ma_2 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[1]}"
            )  # 25
            ma_3 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[2]}"
            )  # 99

            macd = getattr(
                self.ins_macd, f"{symbol}_{self.ins_macd.type_str}_{self.ins_macd.short_window}_{self.ins_macd.long_window}_{self.ins_macd.signal_window}"
            )
            macd_line = macd[0]
            signal_line = macd[1]
            histogram = macd[2]
            
            
            base_data = getattr(
                self.kline_datasets[symbol], f"interval_{self.interval}"
            )
            convert_to_array = np.array(base_data, float)
            current_price = float(convert_to_array[-1][4])
            open_price = float(convert_to_array[-1][1])

            # 조건 1 : 캔들 하락
            if not open_price > current_price:
                result[symbol] = self.fail_message
                continue

            # 조건 2 : MA간 순위 비교
            is_price_trend = current_price < ma_3[-1] < open_price < ma_1[-1] < ma_2[-1]
            if not is_price_trend:
                result[symbol] = self.fail_message
                continue

            # 조건 3 : 볼륨 강도
            volume_ratio = np.mean(convert_to_array[-3:,10] / convert_to_array[-3:,7])
            volume_target_ratio = 0.45
            if not volume_ratio <= volume_target_ratio:
                result[symbol] = self.fail_message
                continue
                
            ### DEBUG CODE                
            if not macd_line[-1] > signal_line[-1]:
                result[symbol] = self.fail_message
                continue

            # 조건 4 : 장기 MA 하락
            target_hr = 6
            hour_minute = 60
            interval_min = 3
            data_lengh = int((target_hr * hour_minute) / interval_min)
            # print(f' data_lengh = {data_lengh}')
            select_data_ma_3 = ma_3[-1 * data_lengh :]
            # print(f'ma_lengh = {len(ma_3)}')
            group_count = 5
            if data_lengh % group_count != 0:
                raise ValueError(f"시간 또는 그룹값 수정 필요함.")

            data_step = int(data_lengh / group_count)
            group_condition = []
            for count in range(group_count):

                start = count * data_step
                stop = start + data_step
                group_condition.append(np.arange(start=start, stop=stop, step=1))
            down_count = 0

            target_ratio = 1

            for condition in reversed(group_condition):
                diff_ma = np.diff(select_data_ma_3[condition])
                positive_ratio = np.sum(diff_ma < 0) / (data_step - 1)
                if not target_ratio <= positive_ratio:
                    continue
                down_count += 1

            if down_count < 2:
                result[symbol] = self.fail_message
                continue
            self.success_message.append(down_count)
            result[symbol] = self.success_message
            self.reset_message()
        self.result = result


class BuyStrategy1:
    """
    Short 포지션 관련 분석
    """

    def __init__(self, ma_data: IndicatorMA, macd_data:IndicatorMACD):
        self.ins_ma = ma_data
        self.ins_macd = macd_data

        self.kline_datasets = self.ins_ma.kline_datasets
        self.periods = self.ins_ma.periods
        self.interval = self.ins_ma.interval
        self.type_str = self.ins_ma.type_str

        # 어떻게 결과물을 발생시킬지 검토필요함.
        self.result: Optional[list[int]] = None

        # 상태(True/False) / position(1/2) / class number(1)
        self.fail_message: List = [0, 1, 1, 0]
        self.success_message: List = [1, 1, 1]

    def reset_message(self):
        self.fail_message: List = [0, 1, 1, 0]
        self.success_message: List = [1, 1, 1]

    def run(self):
        symbols = list(self.kline_datasets.keys())
        result = {}
        for symbol in symbols:
            ma_1 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[0]}"
            )  # 7
            ma_2 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[1]}"
            )  # 25
            ma_3 = getattr(
                self.ins_ma, f"{symbol}_{self.type_str}_{self.periods[2]}"
            )  # 99

            macd = getattr(
                self.ins_macd, f"{symbol}_{self.ins_macd.type_str}_{self.ins_macd.short_window}_{self.ins_macd.long_window}_{self.ins_macd.signal_window}"
            )
            macd_line = macd[0]
            # print(f'MACD:{macd_line}')
            signal_line = macd[1]
            histogram = macd[2]


            base_data = getattr(
                self.kline_datasets[symbol], f"interval_{self.interval}"
            )
            convert_to_array = np.array(base_data, float)
            current_price = float(convert_to_array[-1][4])
            open_price = float(convert_to_array[-1][1])

            # 조건 1 : 캔들 상승
            if not open_price < current_price:
                result[symbol] = self.fail_message
                # print(f'fail 1 {symbol} - {result[symbol]}')
                continue

            # 조건 2 : MA간 순위 비교
            is_price_trend = current_price > ma_1[-1] > open_price > ma_3[-1] > ma_2[-1]

            if not is_price_trend:
                result[symbol] = self.fail_message
                continue

            # 조건 3 : 볼륨 강도
            volume_ratio = np.mean(convert_to_array[-3:,10] / convert_to_array[-3:,7])
            volume_target_ratio = 0.55
            if not volume_ratio >= volume_target_ratio:
                result[symbol] = self.fail_message
                continue

            ### DEBUG CODE                
            if not macd_line[-1] < signal_line[-1]:
                result[symbol] = self.fail_message
                continue

            # 조건 4 : 장기 MA 하락
            target_hr = 6
            hour_minute = 60
            interval_min = 3
            data_lengh = int((target_hr * hour_minute) / interval_min)
            select_data_ma_3 = ma_3[-1 * data_lengh :]

            group_count = 5
            if data_lengh % group_count != 0:
                raise ValueError(f"시간 또는 그룹값 수정 필요함.")

            data_step = int(data_lengh / group_count)
            group_condition = []
            for count in range(group_count):

                start = count * data_step
                stop = start + data_step
                group_condition.append(np.arange(start=start, stop=stop, step=1))
            down_count = 0

            target_ratio = 1
            for condition in reversed(group_condition):
                diff_ma = np.diff(select_data_ma_3[condition])
                positive_ratio = np.sum(diff_ma > 0) / (data_step - 1)
                if not target_ratio <= positive_ratio:
                    continue
                # print(positive_ratio)
                down_count += 1
            if down_count < 2:
                result[symbol] = self.fail_message
                continue

            self.success_message.append(down_count)
            result[symbol] = self.success_message
            self.reset_message()
        self.result = result
        # print(self.result)


class AnalysisManager:
    def __init__(self, kline_datasets: Dict[str, DataStoreage.KlineData]):
        self.data_sets = kline_datasets
        
        ### 공통 설정
        self.interval_3m: str = "3m"

        ### MA 분석
        self.data_type_sma: str = "sma"
        self.data_type_ema: str = "ema"
        self.data_type_wma: str = "wma"
        self.data_type_macd: str = "macd"
        self.periods: List[int] = [7, 25, 99]
        self.ins_ma_sma_3m = IndicatorMA(
            kline_datasets=self.data_sets,
            data_type=self.data_type_sma,
            interval=self.interval_3m,
            periods=self.periods,
        )

        ### MACD 분석
        self.col_index = 10
        # utils._info_colums()값 반영
        self.short_window = 12
        self.long_window = 26
        self.signal_window = 9
        self.ins_macd_12_26_9 = IndicatorMACD(kline_datasets=self.data_sets,
                                              col_index=self.col_index,
                                              short_window=self.short_window,
                                              long_window=self.long_window,
                                              signal_window=self.signal_window)

        self.ins_sell_strategy_1: BuyStrategy1 = SellStrategy1(self.ins_ma_sma_3m,
                                                               self.ins_macd_12_26_9)
        self.ins_buy_strategy_1: BuyStrategy1 = BuyStrategy1(self.ins_ma_sma_3m,
                                                             self.ins_macd_12_26_9)

        self.success_buy_signal:Dict[str, List[int]] = {}
        self.success_sell_signal:Dict[str, List[int]] = {}
    
    def reset_signal(self):
        self.success_buy_signal:Dict[str, List[int]] = {}
        self.success_sell_signal:Dict[str, List[int]] = {}
        
    def __run_func(self):
        self.ins_ma_sma_3m.run()
        self.ins_macd_12_26_9.run()
        self.ins_sell_strategy_1.run()
        self.ins_buy_strategy_1.run()

    def get_success_signal(self):
        # self.__run_func()
        for attr_name in vars(self).keys():
            base_name = "strategy"
            if base_name in attr_name:
                # getattr을 올바르게 사용
                strategy_instance = getattr(self, attr_name, None)
                for symbol, signal in strategy_instance.result.items():
                    if signal[0] and signal[1]==1:
                        self.success_buy_signal[symbol] = signal
                    elif signal[0] and signal[1]==2:
                        self.success_sell_signal[symbol] = signal

    def run(self):
        self.__run_func()
        self.get_success_signal()
        # self.reset_signal()