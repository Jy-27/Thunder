import asyncio
import numpy as np
import utils
import copy
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple, Final
from dataclasses import dataclass, fields, field, asdict
from numpy.typing import NDArray
import inspect
import time

"""
과최적화가 나쁜것만은 아니다.
내 돈 나가는데 그게 무슨 상관?
"""


@dataclass
class BaseConfig:
    test_mode: bool
    ALL_KLINE_INTERVALS = utils._info_kline_intervals()  # 클래스 변수
    OHLCV_COLUMNS = utils._info_kline_columns()
    ACTIVE_COLUMNS_INDEX = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
    selected_intervals = ["3m"]  # , "15m", "1h"]  # , "2h", "1d"]
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
        self.lookback_days = self.base_config.lookback_days
        self.processing = Processing()
        self.symbols: List = []
        self.kline_data: Dict = {}
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

    def __get_scenario_number(self) -> Tuple:
        stack = inspect.stack()
        parent_function_name = stack[1].function
        return (parent_function_name, int(parent_function_name.split("_")[-1]))

    def __fail_signal(self, scenario_number: int):
        # 상태, symbol, position, 레버리지, 시나리오 번호
        return (False, None, 0, 0, scenario_number)

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

    def __get_symbols(self):
        dataset_names = self.data_container.get_all_data_names()
        symbols = list(set([symbol.split("_")[1] for symbol in dataset_names]))
        self.symbols = symbols
        return symbols

    def scenario_1(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
        """
        시나리오.
        4개식 3개의 그룹으로 나눈다.
        
        마지막 그룹의 거래대금이 가장 클 것.
        마지막 그룹의 거래횟수가 가장 높을 것.
        마지막 그룹이 전부 상승일 것.
        24시간중 마지막 그룹이 max일 것.
        마지막 그룹이 앞의 2그룹보다 상승폭이 클 것.
        
        최종 집계 후 가장 거래대금이 낮은것을 반환할 것.
        """

        # 진입여부, symbol, 포지션, 시나리오 번호, 레버리지.
        fail_signal = (False, None, 0, 0, 0)

        target_interval = "3m"

        temp_data = {}

        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)

                if len(base_data) < 13:
                    continue

                symbol = name.split("_")[1]

                REFERENCE_RATIO = 1.15
                TAKER_RATIO = 0.65
                CANDLE_RATIO = 0.6

                # 데이터 슬라이싱
                slice_1 = base_data[-11:-7]
                slice_2 = base_data[-7:-4]
                slice_3 = base_data[-4:]

                # taker 구매비율
                total_volume = np.sum(slice_3[:, 10])
                taker_volume = np.sum(slice_3[:, 7])
                if total_volume == 0 or taker_volume == 0:
                    # print(f'1차 {scenario_number} fail - {symbol}')
                    continue

                # debug
                # print(f'1차 통과 - {symbol}')

                taker_volume_ratio = taker_volume / total_volume
                if taker_volume_ratio < TAKER_RATIO:
                    # print(f'2차 {scenario_number} fail - {symbol}')
                    continue

                # print(f'2차 통과 - {symbol}')
                # 거래대금 검토
                value_1 = np.sum(slice_1[:, 7]) * REFERENCE_RATIO
                value_2 = np.sum(slice_2[:, 7]) * REFERENCE_RATIO
                value_3 = np.sum(slice_3[:, 7])

                # 마지막 거래 대금의 합이 제일 커야함.
                is_value = (value_1 < value_3) and (value_2 < value_3)
                # 조건 안맞으면 pass
                if not is_value:
                    # print(f'3차 {scenario_number} fail - {symbol}')
                    # 종료
                    continue

                # print(f'3차 통과 - {symbol}')
                # debug
                count_1 = np.sum(slice_1[:, 8]) * REFERENCE_RATIO
                count_2 = np.sum(slice_2[:, 8]) * REFERENCE_RATIO
                count_3 = np.sum(slice_3[:, 8])

                is_count = (count_1 < count_3) and (count_2 < count_3)
                # 거래횟수가 마지막 그룹이 max가 아니면
                if not is_count:
                    # print(f'4차 {scenario_number} fail - {symbol}')
                    # 종료
                    continue
                # print(f'4차 통과 - {symbol}')

                # 마지막 그룹이 종가기준 전부 상승일 것.
                diff_close_1 = slice_1[:, 4] - slice_1[:, 1]
                diff_close_2 = slice_2[:, 4] - slice_2[:, 1]
                diff_close_3 = slice_3[:, 4] - slice_3[:, 1]
                # print(f'AAAAA - {diff_close_3}')
                if not np.all(diff_close_3 > 0):
                    # print(f'5차 {scenario_number} fail - {symbol}')
                    continue

                # print(f'5차 통과 - {symbol}')
                wick_close_3 = slice_3[:, 2] - slice_3[:, 3]
                body_close_3 = np.abs(diff_close_3)
                candle_body_mean = np.mean(body_close_3 / wick_close_3)
                # print("=============")
                # print(candle_body_mean)
                # print("=============")
                # # candle 몸통의 비율이 목표 비율보다 낮으면,
                if not candle_body_mean > CANDLE_RATIO:
                    # print(f'6차 {scenario_number} fail - {symbol}')
                    #     # 종료
                    continue
                # print(f'6차 통과 - {symbol}')
                # 마지막 가격이 24시간 max가격이 아니면
                max_close_price = np.max(base_data[:, 4])

                if not max_close_price == slice_3[-1][4]:
                    # print(f'7차 {scenario_number} fail - {symbol}')
                    # 종료
                    continue
                # print(f'7차 통과 - {symbol}')
                time_ = utils._convert_to_datetime(time.time() * 1_000)
                print(f"검토 승인 : {scenario_name} - {symbol} -{time_}")
                # continue
                # debug
                temp_data[symbol] = value_3

        if not temp_data:
            return fail_signal
        # print('종점.')
        leverage = len(temp_data)
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 1, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)

    def scenario_2(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
        """
        시나리오.
        4개식 3개의 그룹으로 나눈다.
        
        마지막 그룹의 거래대금이 가장 클 것.
        마지막 그룹의 거래횟수가 가장 높을 것.
        마지막 그룹이 전부 상승일 것.
        24시간중 마지막 그룹이 max일 것.
        마지막 그룹이 앞의 2그룹보다 상승폭이 클 것.
        
        최종 집계 후 가장 거래대금이 낮은것을 반환할 것.
        """

        # 진입여부, symbol, 포지션, 시나리오 번호, 레버리지.
        fail_signal = (False, None, 0, 0, 0)

        target_interval = "3m"

        temp_data = {}

        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)

                if len(base_data) < 13:
                    continue

                symbol = name.split("_")[1]

                REFERENCE_RATIO = 1.15
                TAKER_RATIO = 0.35
                CANDLE_RATIO = 0.6

                # 데이터 슬라이싱
                slice_1 = base_data[-11:-7]
                slice_2 = base_data[-7:-4]
                slice_3 = base_data[-4:]

                # taker 구매비율
                total_volume = np.sum(slice_3[:, 7])
                taker_volume = np.sum(slice_3[:, 10])
                if total_volume == 0 or taker_volume == 0:
                    # print(f'1차 {scenario_number} fail - {symbol}')
                    continue

                # debug
                # print(f'1차 통과 - {symbol}')

                taker_volume_ratio = taker_volume / total_volume
                # print(f'{taker_volume_ratio:,.2f}')
                if not taker_volume_ratio < TAKER_RATIO:
                    # print(f'2차 {scenario_number} fail - {symbol}')
                    continue

                # print(f'2차 통과 - {symbol}')
                # 거래대금 검토
                value_1 = np.sum(slice_1[:, 7]) * REFERENCE_RATIO
                value_2 = np.sum(slice_2[:, 7]) * REFERENCE_RATIO
                value_3 = np.sum(slice_3[:, 7])

                # 마지막 거래 대금의 합이 제일 커야함.
                is_value = (value_1 < value_3) and (value_2 < value_3)
                # 조건 안맞으면 pass
                if not is_value:
                    # print(f'3차 {scenario_number} fail - {symbol}')
                    # 종료
                    continue

                # print(f'3차 통과 - {symbol}')
                # debug
                count_1 = np.sum(slice_1[:, 8]) * REFERENCE_RATIO
                count_2 = np.sum(slice_2[:, 8]) * REFERENCE_RATIO
                count_3 = np.sum(slice_3[:, 8])

                is_count = (count_1 < count_3) and (count_2 < count_3)
                # 거래횟수가 마지막 그룹이 max가 아니면
                if not is_count:
                    # print(f'4차 {scenario_number} fail - {symbol}')
                    # 종료
                    continue
                # print(f'4차 통과 - {symbol}')

                # 마지막 그룹이 종가기준 전부 하락일 것.
                diff_close_1 = slice_1[:, 1] - slice_1[:, 4]
                diff_close_2 = slice_2[:, 1] - slice_2[:, 4]
                diff_close_3 = slice_3[:, 1] - slice_3[:, 4]

                # print(f'AAAAA - {diff_close_3}')
                if not np.all(diff_close_3 > 0):
                    # print(f"5차 {scenario_number} fail - {symbol}")
                    continue

                # print(f'5차 통과 - {symbol}')
                wick_close_3 = slice_3[:, 3] - slice_3[:, 2]
                body_close_3 = np.abs(diff_close_3)
                candle_body_mean = np.mean(body_close_3 / wick_close_3)
                # print("=============")
                # print(candle_body_mean)
                # print("=============")
                # # candle 몸통의 비율이 목표 비율보다 낮으면,
                if not candle_body_mean > CANDLE_RATIO:
                    # print(f"6차 {scenario_number} fail - {symbol}")
                    # 종료
                    continue
                # print(f'6차 통과 - {symbol}')
                # 마지막 가격이 24시간 max가격이 아니면
                min_close_price = np.min(base_data[:, 4])
                if not min_close_price == slice_3[-1][4]:
                    # print(f"7차 {scenario_number} fail - {symbol}")
                    # 종료
                    continue
                # print(f'7차 통과 - {symbol}')
                time_ = utils._convert_to_datetime(time.time() * 1_000)
                print(f"검토 승인 : {scenario_name} - {symbol} -{time_}")
                # continue
                # debug
                temp_data[symbol] = value_3

        if not temp_data:
            return fail_signal
        # print('종점.')
        leverage = len(temp_data)
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 2, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)

    def scenario_3(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
        """
        시나리오
        
            1. 분석 대상 : 3m
            2. 포지션 : Long
            3. 조건
                1) close - open의 연속성을 가질 것.
                    >> 연속성 가진 값의 index값을 추출한다.
                
                    데이터의 길이를 활용해 해당 Step별로 3개 그룹으로 구성
                
                2) 거래대금의 합계가 마지막 그룹이 3배 넘을 것.
                3) 각 그룹의 길이는 최소 3개 이상일 것.
                4) 거래대금 / 거래 건수를 계산하여 평균값이 최고가 아닐것. 고민해볼 필요가 있다.
                5) 평균 캔들 꼬리길이가 body길이의 40%를 초과하지 말 것. 
        """
        target_interval = '3m'
        temp_data = {}
        reference_ratio = 1.2
        max_body_ratio = 0.8
        
        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)
        
                symbol = name.split("_")[1]
        
                close_idx = 4
                open_idx = 1
        
                candle_body_lengh = base_data[:,4] - base_data[:,1]
                diff_body = np.diff(candle_body_lengh)
                condition = diff_body[::-1] > 0
                true_len = np.argmax(condition) if np.any(condition) else len(diff_body)
                
                
                data_group_1 = base_data[-3*true_len:-2*true_len]
                data_group_2 = base_data[-2*true_len:-1*true_len]
                data_group_3 = base_data[-1*true_len:]
                # 데이터의 길이가 3개 미만이면
                if not true_len >= 3 :
                    # print(f'1차 롱 페일')
                    # 종료
                    continue
                
                group_1_volume = np.sum(data_group_1[:, 7])
                group_2_volume = np.sum(data_group_2[:, 7])
                group_3_volume = np.sum(data_group_3[:, 7])
                # 마지막 거래대금이 이전 거래대금보다 1.5배 더 클것.
                if not (group_1_volume < group_3_volume) and (group_2_volume < group_3_volume):
                    # print(f'2차 롱 페일')
                    # 종료
                    continue
                
                taker_1_q_volume = np.sum(data_group_1[:,10])
                taker_2_q_volume = np.sum(data_group_2[:,10])
                taker_3_q_volume = np.sum(data_group_3[:,10])
                
                
                taker_ratio_1 = taker_1_q_volume / group_1_volume
                taker_ratio_2 = taker_2_q_volume / group_2_volume
                taker_ratio_3 = taker_3_q_volume / group_3_volume
  
                # 테이커의 비율이 마지막 그룹이 제일 높을 것.
                if not (taker_ratio_1 < taker_ratio_3) and not (taker_ratio_2 < taker_ratio_3):
                    continue
                               
                candle_total_lengh = base_data[-1*true_len:,2] - base_data[-1*true_len:,3]
                # print(candle_total_lengh)
                body_ratio = np.mean(candle_body_lengh[-1*true_len:,] / candle_total_lengh)
                # print(body_ratio)
                if not body_ratio > max_body_ratio:
                    print(f'{symbol} - 4차 롱 페일')
                    # 종료
                    continue
                temp_data[symbol] = taker_3_q_volume
                
        if not temp_data:
            return fail_signal
                
        # leverage = len(temp_data)
        leverage = 1
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 5, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)

    def scenario_4(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
        """
        시나리오
        
            1. 분석 대상 : 3m
            2. 포지션 : Long
            3. 조건
                1) close - open의 연속성을 가질 것.
                    >> 연속성 가진 값의 index값을 추출한다.
                
                    데이터의 길이를 활용해 해당 Step별로 3개 그룹으로 구성
                
                2) 거래대금의 합계가 마지막 그룹이 3배 넘을 것.
                3) 각 그룹의 길이는 최소 3개 이상일 것.
                4) 거래대금 / 거래 건수를 계산하여 평균값이 최고가 아닐것. 고민해볼 필요가 있다.
                5) 평균 캔들 꼬리길이가 body길이의 40%를 초과하지 말 것. 
        """
        target_interval = '3m'
        temp_data = {}
        reference_ratio = 1.2
        max_body_ratio = 0.6
        
        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)
        
                symbol = name.split("_")[1]
        
                close_idx = 4
                open_idx = 1
        
                candle_body_lengh = base_data[:,open_idx] - base_data[:,close_idx]
                diff_body = np.diff(candle_body_lengh)
                condition = diff_body[::-1] < 0
                true_len = np.argmax(condition) if np.any(condition) else len(diff_body)
                
                
                data_group_1 = base_data[-3*true_len:-2*true_len]
                data_group_2 = base_data[-2*true_len:-1*true_len]
                data_group_3 = base_data[-1*true_len:]
                # 데이터의 길이가 3개 미만이면
                if not true_len > 3:
                    print(f'1차 {symbol} - short fail')
                    # 종료
                    continue
                
                group_1_value = np.sum(data_group_1[:, 5]) * reference_ratio
                group_2_value = np.sum(data_group_2[:, 5]) * reference_ratio
                group_3_value = np.sum(data_group_3[:, 5])
                # 마지막 거래대금이 이전 거래대금보다 1.5배 더 클것.
                if not (group_1_value < group_3_value) and (group_2_value < group_3_value):
                    print(f'2차 {symbol} -  short fail')
                    # 종료
                    continue
                
                group_1_count = np.sum(data_group_1[:, 8]) * reference_ratio
                group_2_count = np.sum(data_group_2[:, 8]) * reference_ratio
                group_3_count = np.sum(data_group_3[:, 8])
                # 마지막 거래횟수가 이전 거래횟수보다 1.5배 더 클 것.
                if not (group_1_count < group_3_count) and (group_2_count < group_3_count):
                    print(f'3차 {symbol} -  short fail')
                    # 종료
                    continue
                
                candle_total_lengh = base_data[-1*true_len:,2] - base_data[-1*true_len:,3]
                # print(candle_total_lengh)
                body_ratio = np.mean(candle_body_lengh[-1*true_len:,] / candle_total_lengh)
                # print(body_ratio)
                if not body_ratio > max_body_ratio:
                    print(f'4차 {symbol} - short fail')
                    # 종료
                    continue
                temp_data[symbol] = group_3_value
                
        if not temp_data:
            return fail_signal
                
        # leverage = len(temp_data)
        leverage = 2
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 2, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)

    def scenario_5(self):
        target_interval = '3m'
        temp_data = {}
        reference_ratio = 1.2
        max_body_ratio = 0.6
        data_range = 20
        
        
        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)
                select_data = base_data[-1*data_range:]
                
                open_idx = 1
                close_idx = 4
                
                # 음봉
                bearish_candle = select_data[:, close_idx] - select_data[:, open_idx]
                # 양봉
                bullish_candle = select_data[:, open_idx] - select_data[:, close_idx]
                
                bearish_sum = np.sum(bearish_candle)
                bullish_sum = np.sum(bullish_candle)
                
                bearish_count = np.sum(bearish_sum < 0)
                bullish_count = np.sum(bullish_sum > 0)
                
    def scenario_6(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
            
        temp_data = {}
        target_interval = '3m'
        
        # 숏 포지션.
        
        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)
                
                symbol = name.split("_")[1]
                
                data_a = base_data[-8:-3, 4]-base_data[-8:-3, 1]
                data_b = base_data[-3:, 4]-base_data[-3:, 1]
                
                is_bearish_candle = np.all(data_a < 0)
                is_bullish_candle = np.all(data_b > 0)
                
                # 조건 검토
                if not is_bearish_candle or not is_bullish_candle:
                    continue
                
                start_price = base_data[-8][4]
                end_price = base_data[-1][4]
                
                if not start_price < end_price:
                    continue
                
                value = np.sum(base_data[-8:, 7])
                
                temp_data[symbol] = value
                
        if not temp_data:
            return fail_signal
                
        leverage = 2
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 2, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)

    def scenario_7(self):
        scenario_name, scenario_number = self.__get_scenario_number()
        fail_signal = self.__fail_signal(scenario_number)
            
        temp_data = {}
        target_interval = '3m'
        
        # 숏 포지션.
        
        data_names = self.data_container.get_all_data_names()
        for name in data_names:
            if target_interval in name:
                base_data = self.data_container.get_data(name)
                
                symbol = name.split("_")[1]
                
                data_a = base_data[-8:-3, 4]-base_data[-8:-3, 1]
                data_b = base_data[-3:, 4]-base_data[-3:, 1]
                
                is_bearish_candle = np.all(data_a > 0)
                is_bullish_candle = np.all(data_b < 0)
                
                # 조건 검토
                if not is_bearish_candle or not is_bullish_candle:
                    continue
                
                start_price = base_data[-8][4]
                end_price = base_data[-1][4]
                
                if not start_price > end_price:
                    continue
                
                value = np.sum(base_data[-8:, 7])
                
                temp_data[symbol] = value
                
        if not temp_data:
            return fail_signal
                
        leverage = 2
        symbol = min(temp_data, key=temp_data.get)
        success_signal = (True, symbol, 1, leverage, scenario_number)
        return self.scenario_data.set_data(scenario_name, success_signal)
                
    def scenario_run(self):
        # 진입여부, 포지션, 시나리오 번호, 레버리지.
        fail_signal = (False, None, 0, 0, 0)
        # 수신 데이터에서 심볼 정보를 추출하여 속성에 저장한다.
        self.__get_symbols()
        ### scenario 함수 실행 공간
        self.scenario_1()
        self.scenario_2()
        self.scenario_3()
        # self.scenario_6()
        # self.scenario_7()

        ###
        scenario_list = self.scenario_data.get_all_data_names()
        for name in scenario_list:
            signal = self.scenario_data.get_data(data_name=name)
            time_ = utils._convert_to_datetime(time.time() * 1_000)
            # 조건을 추가할 수 있다. 레버리지값이 2이상일때?라는 조건.
            if signal[0] and signal[3]>=2:
                print("====== 최종 승인 ======")
                print(f"1. Symbol      : {signal[1]}")
                print(f"2. Position    : {signal[2]}")
                print(f"3. Scenario_no : {signal[4]}")
                print(f"4. Leverage    : {signal[3]}")
                print(f"5. time        : {time_}")
                self.clear_dataset()
                return signal
        self.clear_dataset()
        return fail_signal


# def scenario_1(self):
#     scenario_name, scenario_number = self.__get_scenario_number()
#     fail_signal = self.__fail_signal(scenario_number)
#     """
#     시나리오 1
#         1. 48시간 기준 가장 최고/최저 점 도딜시점에 5분봉 연속 하락 또는 상승
#         2. candle길이는 증가해야함.
#     """

#     data_5m = self.data_container.get_data("interval_5m")
#     data_15m = self.data_container.get_data("interval_15m")
#     data_1h = self.data_container.get_data("interval_1h")

#     ## 최고점 / 최저점 확인
#     open_price = 1
#     high_price = 2
#     low_price = 3
#     close_price = 4

#     quote_value = 7

#     price_max = np.max(data_1h[:, open_price])
#     price_min = np.min(data_1h[:, open_price])

#     is_price_max = price_max == data_1h[-1][open_price]
#     is_price_min = price_min == data_1h[-1][open_price]


#     if not (is_price_max or is_price_min):
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     candle_up_15m = data_15m[:, 1] - data_15m[:, 4]
#     candle_down_15m = data_15m[:, 4] - data_15m[:, 1]

#     candle_up_diff_15m = np.diff(candle_up_15m)
#     candle_down_diff_15m = np.diff(candle_down_15m)

#     is_candle_up_15m = np.all(candle_up_diff_15m[-2:] > 0)
#     is_candle_down_15m = np.all(candle_down_diff_15m[-2:] < 0)

#     if not (is_candle_up_15m or is_candle_down_15m):
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     # candle_up_5m = data_5m[:, 1] - data_5m[:, 4]
#     # candle_down_5m = data_5m[:, 4] - data_5m[:, 1]

#     candle_up_diff_5m = np.diff(data_5m[:, close_price])
#     candle_down_diff_5m = np.diff(data_15m[:, close_price])

#     is_candle_up_5m = np.all(candle_up_diff_5m[-3:] > 0)
#     is_candle_down_5m = np.all(candle_down_diff_5m[-3:] < 0)

#     if not (is_candle_up_5m or is_candle_down_5m):
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     if is_price_max:
#         success_signal = (True, 1, scenario_number)
#         return self.scenario_data.set_data(scenario_name, success_signal)

#     if is_price_min:
#         success_signal = (True, 2, scenario_number)
#         return self.scenario_data.set_data(scenario_name, success_signal)

# def scenario_2(self):
#     scenario_name, scenario_number = self.__get_scenario_number()
#     fail_signal = self.__fail_signal(scenario_number)

#     open_price = 1
#     high_price = 2
#     low_price = 3
#     close_price = 4

#     data_5m = self.data_container.get_data("interval_5m")

#     def ema(data, period):
#         alpha = 2 / (period + 1)
#         ema_values = np.empty_like(data)
#         ema_values[0] = data[0]  # 초기 값
#         for i in range(1, len(data)):
#             ema_values[i] = alpha * data[i] + (1 - alpha) * ema_values[i - 1]
#         return ema_values

#     ema_5 = ema(data_5m[:, close_price], 99)

#     last_ma_price = ema_5[-1]
#     current_price = data_5m[-1][close_price]

#     data_slice_5m = data_5m[-10:]

#     candle_body_length = (
#         data_slice_5m[:, open_price] - data_slice_5m[:, close_price]
#     )
#     candle_body_diff = np.diff(candle_body_length)[-2:]

#     is_plus_length = np.all(candle_body_diff > 0)
#     is_minus_legth = np.all(candle_body_diff < 0)

#     if not (is_minus_legth or is_minus_legth):
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     if last_ma_price < current_price and is_plus_length:
#         success_signal = (True, 1, scenario_number)
#         return self.scenario_data.set_data(scenario_name, success_signal)
#     elif last_ma_price > current_price and is_minus_legth:
#         success_signal = (True, 2, scenario_number)
#         return self.scenario_data.set_data(scenario_name, success_signal)
#     else:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

# def scenario_3(self):
#     scenario_name, scenario_number = self.__get_scenario_number()
#     fail_signal = self.__fail_signal(scenario_number)

#     """"
#     시나리오
#     taker구매 비율이 높으면,
#     1h mean 이 1.2배 이상
#     15분봉 3회 연속 양봉
#     5분봉 양봉

#     """
#     data_1h = self.data_container.get_data("interval_1h")
#     data_15m = self.data_container.get_data("interval_15m")
#     data_5m = self.data_container.get_data("interval_5m")

#     data_1h_mean = np.mean(data_1h[:, 4])
#     data_1h_ratio = (data_1h[:, 4] - data_1h_mean) / data_1h_mean

#     data_1h_max_close_price = np.max(data_1h[:, 4])
#     is_last_price = data_1h_max_close_price == data_1h[-1][4]

#     # print('\n')
#     # print('='*10)
#     # print(data_1h_ratio)
#     # print('='*10)

#     if data_1h_ratio[-1] < 1.2 and not is_last_price:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_15m_diff = np.diff(data_15m[:, 4])
#     is_diff_15m_up = np.all(data_15m_diff[-3:] > 0)
#     if not is_diff_15m_up:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_5m_diff = np.diff(data_5m[:, 4])
#     is_diff_5m_up = np.all(data_15m_diff[-3:] > 0)
#     if not is_diff_5m_up:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_15m_TAKER_RATIO = data_15m[-1][9] / data_15m[-1][7]

#     if data_15m_TAKER_RATIO < 0.8:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     success_signal = (True, 1, scenario_number)
#     self.scenario_data.set_data(scenario_name, success_signal)

# def scenario_4(self):
#     scenario_name, scenario_number = self.__get_scenario_number()
#     fail_signal = self.__fail_signal(scenario_number)

#     """"
#     시나리오
#     taker구매 비율이 높으면,
#     1h mean 이 1.2배 이상
#     15분봉 3회 연속 양봉
#     5분봉 양봉
#     """
#     data_1h = self.data_container.get_data("interval_1h")
#     data_15m = self.data_container.get_data("interval_15m")
#     data_5m = self.data_container.get_data("interval_5m")

#     data_1h_mean = np.mean(data_1h[:, 4])
#     data_1h_ratio = (data_1h[:, 4] - data_1h_mean) / data_1h_mean

#     data_1h_min_close_price = np.min(data_1h[:, 4])
#     is_last_price = data_1h_min_close_price == data_1h[-1][4]

#     if data_1h_ratio[-1] > -1.2 and not is_last_price:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_15m_diff = np.diff(data_15m[:, 4])
#     is_diff_15m_down = np.all(data_15m_diff[-3:] < 0)
#     if not is_diff_15m_down:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_5m_diff = np.diff(data_5m[:, 4])
#     is_diff_5m_down = np.all(data_15m_diff[-3:] < 0)
#     if not is_diff_5m_down:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     data_15m_TAKER_RATIO = data_15m[-1][9] / data_15m[-1][7]
#     print(True)
#     if data_15m_TAKER_RATIO > 0.2:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     success_signal = (True, 2, scenario_number)
#     self.scenario_data.set_data(scenario_name, success_signal)

# def scenario_5(self):
#     scenario_name, scenario_number = self.__get_scenario_number()
#     fail_signal = self.__fail_signal(scenario_number)
#     """
#     시나리오.
#     =1시간 5분봉 데이터를 수집한다.
#     =마지막 3포인트는 연속성을 가진다.
#     =전체 비율에 up 또는 down의 방향성을 가진다.
#     3개 데이터씩 4개 그룹으로 나뉜다. 나뉜 그룹의 상승 또는 하락 여부를 True와 False로 구분 한다.
#     True가 3 이상이고 마지막값이 연속성을 가지면 long
#     False가 3 이상이고 마지막값이 연속성을 가지면 short
#     =시작부터 종료까지 1.5% 차이나면 True
#     """
#     data_5m = self.data_container.get_data("interval_5m")
#     data_slice_1 = data_5m[-16:-12]
#     data_slice_2 = data_5m[-12:-8]
#     data_slice_3 = data_5m[-8:-4]
#     data_slice_4 = data_5m[-4:]

#     slice_1_score = np.sum(np.diff(data_slice_1[:,4]) > 0)
#     slice_2_score = np.sum(np.diff(data_slice_2[:,4]) > 0)
#     slice_3_score = np.sum(np.diff(data_slice_3[:,4]) > 0)
#     slice_4_score = np.sum(np.diff(data_slice_4[:,4]) > 0)

#     if not (slice_4_score ==3 or slice_4_score == 0):
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     max_high_price = np.max(data_5m[-16:, 2])
#     min_low_price = np.min(data_5m[-16:, 3])
#     last_close_price = data_5m[-1][4]

#     ratio_diff = (max_high_price - min_low_price) / last_close_price
#     target_ratio = 0.02
#     if ratio_diff < target_ratio:
#         return self.scenario_data.set_data(scenario_name, fail_signal)

#     total_score = np.sum(np.array([slice_1_score, slice_2_score, slice_3_score, slice_4_score]))
#     # total_score = np.array([slice_2_score, slice_3_score, slice_4_score])
#     # print(total_score)
#     is_long_score = np.sum(total_score==3) > 2
#     is_short_score = np.sum(total_score==0) > 2

#     candle_body_length = np.sum(data_5m[:,4] - data_5m[:, 1])
#     if candle_body_length > 0 and total_score >= 9 and slice_4_score ==3 and max_high_price == last_close_price:
#         success_signal = (True, 1, scenario_number)
#         self.scenario_data.set_data(scenario_name, success_signal)
#         return

#     elif candle_body_length < 0 and total_score <= 3 and slice_4_score ==0 and min_closmin_low_price_price == last_close_price:
#         success_signal = (True, 2, scenario_number)
#         self.scenario_data.set_data(scenario_name, success_signal)
#         return
#     self.scenario_data.set_data(scenario_name, fail_signal)
