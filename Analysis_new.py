### 초기설정

import asyncio
import MarketDataFetcher
import numpy as np
import DataStoreage
import utils
from pprint import pprint
from typing import Dict, List, Final, Optional


class IndicatorMA:
    """
    이동평균값을 계산한다.
    """

    def __init__(
        self,
        kline_datasets: Dict[str, DataStoreage.KlineData],
        ma_type: str = "sma",
        interval: str = "3m",
        periods: List = [7, 25, 99],
    ):
        self.kline_datasets = kline_datasets
        self.periods: List[int] = periods
        self.interval: str = interval
        self.type_str: str = ma_type
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


class SellStrategy1:
    """
    Short 포지션 관련 분석
    """

    def __init__(self, ma_data: IndicatorMA):
        self.ins_ma = ma_data

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
            is_price_trend = (current_price < ma_3[-1] < ma_1[-1] < ma_2[-1]) or (
                current_price < ma_3[-1] < ma_1[-1] < ma_2[-1]
            )

            if not is_price_trend:
                result[symbol] = self.fail_message
                continue

            # 조건 3 : 장기 MA 하락
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

            target_ratio = 0.9

            for condition in reversed(group_condition):
                diff_ma = np.diff(select_data_ma_3[condition])
                negative_ratio = np.sum(diff_ma > 0) / (data_step - 1)
                if not target_ratio <= negative_ratio:
                    result[symbol] = self.fail_message
                    continue
                down_count += 1
            result[symbol] = self.success_message.extend(down_count)
            self.reset_message()
        self.result = result


class BuyStrategy1:
    """
    Short 포지션 관련 분석
    """

    def __init__(self, ma_data: IndicatorMA):
        self.ins_ma = ma_data

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

            base_data = getattr(
                self.kline_datasets[symbol], f"interval_{self.interval}"
            )
            convert_to_array = np.array(base_data, float)
            current_price = float(convert_to_array[-1][4])
            open_price = float(convert_to_array[-1][1])

            # 조건 1 : 캔들 상승
            if not open_price < current_price:
                result[symbol] = self.fail_message
                continue

            # 조건 2 : MA간 순위 비교
            is_price_trend = current_price > ma_1[-1] > ma_3[-1] > ma_2[-1]

            if not is_price_trend:
                result[symbol] = self.fail_message
                continue

            # 조건 3 : 장기 MA 하락
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

            target_ratio = 0.9

            for condition in reversed(group_condition):
                diff_ma = np.diff(select_data_ma_3[condition])
                negative_ratio = np.sum(diff_ma < 0) / (data_step - 1)
                if not target_ratio <= negative_ratio:
                    result[symbol] = self.fail_message
                    continue
                down_count += 1
            result[symbol] = self.success_message.extend(down_count)
            self.reset_message()
        self.result = result


class AnalysisManager:
    def __init__(self, kline_datasets: Dict[str, DataStoreage.KlineData]):
        self.data_sets = kline_datasets

        self.interval_3m: str = "3m"
        self.ma_type_sma: str = "sma"
        self.ma_type_ema: str = "ema"
        self.ma_type_wma: str = "wma"
        self.periods: List[int] = [7, 25, 99]
        self.ins_ma_sma_3m = IndicatorMA(
            kline_datasets=self.data_sets,
            ma_type=self.ma_type_sma,
            interval=self.interval_3m,
            periods=self.periods,
        )

        self.ins_sell_strategy_1: BuyStrategy1 = SellStrategy1(self.ins_ma_sma_3m)
        self.ins_buy_strategy_1: BuyStrategy1 = BuyStrategy1(self.ins_ma_sma_3m)

        self.success_signal: Dict[int, Dict] = {1:{}, 2:{}}
    
    def reset_signal(self):
        self.success_signal: Dict[int, Dict] = {1:{}, 2:{}}
        
    def __run_func(self):
        self.ins_ma_sma_3m.run()
        self.ins_sell_strategy_1.run()
        self.ins_buy_strategy_1.run()

    def get_success_signal(self):
        self.__run_func()
        for attr_name in vars(self).keys():
            base_name = "strategy"
            if base_name in attr_name:
                # getattr을 올바르게 사용
                strategy_instance = getattr(self, attr_name, None)
                for symbol, signal in strategy_instance.result.items():
                    if not signal[0]:
                        self.success_signal[signal[1]][symbol] = signal
                        print(self.success_signal)

    def run(self):
        self.__run_func()
        self.get_success_signal()
        self.reset_signal()