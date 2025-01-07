import asyncio
import numpy as np
import utils
import copy
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple, Final
from dataclasses import dataclass, fields, field, asdict
from numpy.typing import NDArray
import inspect

"""
시나리오 1. 
    5분봉 연속 3회 상승
    첫번째 5분봉 < 두번째 5분봉 < 세번째 5분봉 상승률
    위꼬리 아래꼬리 합계 전체 몸통대비 40% 초과 금지 
    


1 : long
2 : short
3 : None 
으로 신호 정의함.
"""


@dataclass
class BaseConfig:
    test_mode: bool
    ALL_KLINE_INTERVALS = utils._info_kline_intervals()  # 클래스 변수
    OHLCV_COLUMNS = utils._info_kline_columns()
    ACTIVE_COLUMNS_INDEX = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
    selected_intervals = ["5m", "15m", "1h"]  # , "2h", "1d"]
    lookback_days = 2
    """
    kline 1회 최대 수신가능갯수 1,000개 이며,
    3분봉 기준 2.08일에 해당함.
    다회 수신할 수 있으나, 수신 횟수 증가시 수신 완료시까지 지연발생을 방지하고자
    MAX 2일로 작업할 것.
    """

    def __post_init__(self):
        # target_interval 유효성 검사
        for interval in self.selected_intervals:
            if interval not in self.ALL_KLINE_INTERVALS:
                raise ValueError(f"interval 값이 유효하지 않음: {interval}")

        # test모드의 경우 interval '1m' 을 추가함.
        if self.test_mode:
            self.intervals = ["1m"] + self.selected_intervals  # .insert(0, '1m')
        elif not self.test_mode:
            self.intervals = self.selected_intervals

        # interval_maps 속성 초기화
        self.intervals_idx_map = {
            f"interval_{data}": idx for idx, data in enumerate(self.intervals)
        }


class Processing:
    # @staticmethod
    # def find_peaks_in_column(data, column_index, max_peaks=None):
    #     """
    #     주어진 np.ndarray 데이터의 특정 열에서 상승 꼭지점을 찾고, 상위 max_peaks 개를 반환합니다.

    #     Args:
    #         data (np.ndarray): 2차원 Numpy 배열.
    #         column_index (int): 상승 꼭지점을 찾을 열의 인덱스.
    #         max_peaks (int, optional): 반환할 꼭지점 갯수 (기본값: None, 모든 꼭지점 반환).

    #     Returns:
    #         np.ndarray: 최대 max_peaks만큼의 꼭지점 인덱스 배열, 값 기준으로 정렬.
    #     """
    #     column_data = data[:, column_index]  # 타겟 열 추출

    #     # 국소 최대값(상승 꼭지점) 찾기
    #     peaks = (column_data[1:-1] > column_data[:-2]) & (column_data[1:-1] > column_data[2:])
    #     peak_indices = np.where(peaks)[0] + 1  # 중앙 기준으로 인덱스 조정

    #     # 경계 조건 처리
    #     if column_data[0] > column_data[1]:  # 첫 번째 값이 꼭지점인 경우
    #         peak_indices = np.r_[0, peak_indices]
    #     if column_data[-1] > column_data[-2]:  # 마지막 값이 꼭지점인 경우
    #         peak_indices = np.r_[peak_indices, len(column_data) - 1]

    #     # 꼭지점 값 기준으로 정렬
    #     peak_indices = peak_indices[np.argsort(column_data[peak_indices])[::-1]]

    #     # 반환할 꼭지점 갯수 제한
    #     if max_peaks is not None:
    #         peak_indices = peak_indices[:max_peaks]
    #     print(peak_indices)
    #     return peak_indices

    @staticmethod
    def find_peaks_in_column(data, column_index, max_peaks=None):
        column_data = data[:, column_index]  # 타겟 열 추출

        # 국소 최대값(상승 꼭지점) 찾기
        diff = np.diff(column_data)  # 이전-다음 차이 계산
        peaks = np.hstack(([False], diff > 0)) & np.hstack((diff < 0, [False]))

        peak_indices = np.where(peaks)[0]  # 꼭지점 인덱스 추출
        peak_values = column_data[peak_indices]

        if max_peaks is not None:
            # 꼭지점 값 기준으로 상위 max_peaks만 선택
            top_indices = np.argpartition(-peak_values, max_peaks)[:max_peaks]
            sorted_indices = top_indices[np.argsort(-peak_values[top_indices])]
        else:
            sorted_indices = np.argsort(-peak_values)

        return peak_indices[sorted_indices]

    @staticmethod
    def find_valleys_in_column(data, column_index, max_valleys=None):
        column_data = data[:, column_index]  # 타겟 열 추출

        # 국소 최소값(하락 꼭지점) 찾기
        diff = np.diff(column_data)  # 이전-다음 차이 계산
        valleys = np.hstack(([False], diff < 0)) & np.hstack((diff > 0, [False]))

        valley_indices = np.where(valleys)[0]  # 하락 꼭지점 인덱스 추출
        valley_values = column_data[valley_indices]

        if max_valleys is not None:
            # 꼭지점 값 기준으로 상위 max_valleys만 선택
            top_indices = np.argpartition(valley_values, max_valleys)[:max_valleys]
            sorted_indices = top_indices[np.argsort(valley_values[top_indices])]
        else:
            sorted_indices = np.argsort(valley_values)

        return valley_indices[sorted_indices]


# 멀티프로세스로 실행할 것.
class AnalysisManager:
    def __init__(self, back_test: bool = False):  # , symbols: list):
        # interval 값 세팅
        self.base_config = BaseConfig(test_mode=back_test)
        self.intervals = self.base_config.intervals
        self.interval_idx_map = self.base_config.intervals_idx_map
        self.lookbact_days = self.base_config.lookback_days
        self.processing = Processing()
        self.symbols = []
        self.kline_data = {}
        # np.array([])로 초기화 후 추가 하는 작업은 성능저하 생기므로 list화 한 후 np.array처리함.

        # data:np.ndarray // data_name=f'interval_{interval}' 데이터전달.
        self.data_container: Optional[utils.DataContainer] = None
        self.scenario_data = utils.DataContainer()

    # 데이터 셋을 생성한다.
    def set_dataset(self, name, data):
        self.scenario_data.set_data(name, data)

    # 데이터 셋을 초기화 한다.
    # 결과 반환시 클리어 처리한다. // 필요 엾을것 같은데?
    def clear_dataset(self):
        self.data_container.clear_all_data()
        self.scenario_data.clear_all_data()

    def __get_scenario_number(self) -> int:
        stack = inspect.stack()
        parent_function_name = stack[1].function
        return parent_function_name, int(parent_function_name.split("_")[-1])

    def __fail_signal(self, scenario_number: int):
        # 상태, position, 시나리오 번호
        return (False, 0, scenario_number)

    def __validate_interval(self, intervals):
        # 등록된 interval 확인
        missing_intervals = [item for item in intervals if item not in self.intervals]
        if missing_intervals:
            raise ValueError(f"미등록 interval 있음: {missing_intervals}")

        # 수신된 데이터에서 interval 확인
        container_name = self.data_container.get_all_data_names()
        available_intervals = [
            name.split("_")[1] for name in container_name
        ]  # 집합으로 처리
        missing_in_data = [
            item for item in intervals if item not in available_intervals
        ]
        if missing_in_data:
            raise ValueError(f"수신 데이터에서 interval값 없음: {missing_in_data}")

    def scenario_1(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_name)
        """
        시나리오 1
            1. 48시간 기준 가장 최고/최저 점 도딜시점에 5분봉 연속 하락 또는 상승
            2. candle길이는 증가해야함.
        """
        
        data_5m = self.data_container.get_data('interval_5m')
        data_15m = self.data_container.get_data('interval_15m')
        data_1h = self.data_container.get_data('interval_1h')
        
        ## 최고점 / 최저점 확인
        open_price = 1
        high_price = 2
        low_price = 3
        close_price = 4
        
        quote_value = 7
        
        price_max = np.max(data_1h[:, open_price])
        price_min = np.min(data_1h[:, open_price])
        
        is_price_max = price_max == data_1h[-1][open_price]
        is_price_min = price_min == data_1h[-1][open_price]

        if not (is_price_max or is_price_min):
            return self.scenario_data.set_data(scenario_name, fail_signal)
        
        
        candle_up_15m = data_15m[:, 1] - data_15m[:, 4]
        candle_down_15m = data_15m[:, 4] - data_15m[:, 1]
        
        candle_up_diff_15m = np.diff(candle_up_15m)
        candle_down_diff_15m = np.diff(candle_down_15m)
        
        is_candle_up_15m = np.all(candle_up_diff_15m[-2:] > 0)
        is_candle_down_15m = np.all(candle_down_diff_15m[-2:] < 0)
        
        if not (is_candle_up_15m or is_candle_down_15m):
            return self.scenario_data.set_data(scenario_name, fail_signal)
        
        # candle_up_5m = data_5m[:, 1] - data_5m[:, 4]
        # candle_down_5m = data_5m[:, 4] - data_5m[:, 1]
        
        candle_up_diff_5m = np.diff(data_5m[:, close_price])
        candle_down_diff_5m = np.diff(data_15m[:, close_price])
        
        is_candle_up_5m = np.all(candle_up_diff_5m[-3:] > 0)
        is_candle_down_5m = np.all(candle_down_diff_5m[-3:] < 0)
        
        if not (is_candle_up_5m or is_candle_down_5m):
            return self.scenario_data.set_data(scenario_name, fail_signal)
        
        if is_price_max:
            success_signal = (True, 1, scenario_number)
            return self.scenario_data.set_data(scenario_name, success_signal)
        
        if is_price_min:
            success_signal = (True, 2, scenario_number)
            return self.scenario_data.set_data(scenario_name, success_signal)
                

    def scenario_2(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_name)

        open_price = 1
        high_price = 2
        low_price = 3
        close_price = 4


        data_5m = self.data_container.get_data('interval_5m')
        def ema(data, period):
            alpha = 2 / (period + 1)
            ema_values = np.empty_like(data)
            ema_values[0] = data[0]  # 초기 값
            for i in range(1, len(data)):
                ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i - 1]
            return ema_values
        
        ema_5 = ema(data_5m[:, close_price], 99)
        
        last_ma_price = ema_5[-1]
        current_price = data_5m[-1][close_price]
        
        data_slice_5m = data_5m[-10:]
        
        candle_body_length = data_slice_5m[:, open_price] - data_slice_5m[:, close_price]
        candle_body_diff = np.diff(candle_body_length)[-2:]
        
        is_plus_length = np.all(candle_body_diff > 0)
        is_minus_legth = np.all(candle_body_diff < 0)

        if not(is_minus_legth or is_minus_legth):
            return self.scenario_data.set_data(scenario_name, fail_signal)
        
        if last_ma_price < current_price and is_plus_length:
            success_signal = (True, 1, scenario_number)
            return self.scenario_data.set_data(scenario_name, success_signal)
        elif last_ma_price > current_price and is_minus_legth:
            success_signal = (True, 2, scenario_number)
            return self.scenario_data.set_data(scenario_name, success_signal)
        else:
            return self.scenario_data.set_data(scenario_name, fail_signal)
    
    
    def scenario_run(self):
        fail_signal = (False, 0, 0)
        ### scenario 함수 실행 공간
        self.scenario_1()
        # self.scenario_2()
        ###
        scenario_list = self.scenario_data.get_all_data_names()
        for name in scenario_list:
            signal = self.scenario_data.get_data(data_name=name)
            if signal[0]:
                self.clear_dataset()
                return signal
        self.clear_dataset()
        return fail_signal
