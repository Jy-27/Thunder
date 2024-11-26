import asyncio
import numpy as np
import utils
import copy
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple



"""
시나리오 1. 
    5분봉 연속 3회 상승
    첫번째 5분봉 < 두번째 5분봉 < 세번째 5분봉 상승률
    위꼬리 아래꼬리 합계 전체 몸통대비 40% 초과 금지 
    

"""

# 멀티프로세스로 실행할 것.
class AnalysisManager:
    def __init__(self):#, symbols: list):
        self.symbols = []
        self.kline_data = {}
        self.intervals = []
        self.OHLCV_COLUMNS: Final[List[str]] = [
            "Open Time", "Open", "High", "Low", "Close", "Volume",
            "Close Time", "Quote Asset Volume", "Number of Trades",
            "Taker Buy Base Asset Volume", "Taker Buy Quote Asset Volume", "Ignore"
            ]
        self.ACTIVE_COLUMNS_INDEX: List[int] = [1,2,3,4,5,6,8,9,10,11]
    # kline 데이터의 자료를 리터럴 변환
    
    # 첫번재 작업
    # 중첩 kline data의 [symbol] interval값들을 array로 변환 후 dict로 반환한다.
    def __convert_kline_array(self, symbol:str, interval:str):
        """
        1. 기능 : 중첩 kline data의 interval값들을 array로 변환 후 dict로 변환한다. 
        2. 매개변수
            1) kline_data : raw data(symbol 이 최상위 key)
            2) symbol : target symbol
        """
        
        nested_kline = self.kline_data.get(symbol)
        if not isinstance(nested_kline, dict):
            raise ValueError(f'데이터가 유효하지 않음.')
        interval_data = nested_kline.get(interval)
        if not isinstance(interval_data, list) and not interval_data:
            raise ValueError(f'데이터가 유효하지 않음.')
        return np.array(object=interval_data, dtype=float)
        
    # kline데이터의 'high'값의 max값을 반환한다. (전고점))
    def __get_previous_high(self, kline_data_lv2: List[Union[str, int]]) -> float:
        """
        1. 기능 : kline 데이터의 max high값을 반환한다.
        2. 매개변수
            1) kline_data : get(interval)값을 입력
        """
        np_array = np.array(object=kline_data_lv2, dtype=float)
        return np.max(np_array[:, 2])

    # kline데이터의 'low'값의 min값을 반환한다. (전저점))
    def __get_previous_low(self, kline_data_lv2: List[Union[str, int]]) -> float:
        """
        1. 기능 : kline 데이터의 min low값을 반환한다.
        2. 매개변수
            1) kline_data : get(interval)값을 입력
        """
        np_array = np.array(object=kline_data_lv2, dtype=float)
        return np.min(np_array[:, 3])
    
    # kline에서 특정값의 인덱스를 찾는다.
    def __get_row_indices_by_threshold(
        self,
        kline_data: List[List[Union[str, int]]],
        threshold: float,
        column_index: int,
    ) -> Optional[int]:
        """
        1. 기능 : kline에서 특정값의 인덱스를 찾는다.
        2. 매개변수
            1) klline_data : 찾고자하는 데이터의 interval.get()
            2) threshold : 찾고자하는 값
            3) column_index : 자료의 column_index값
        """

        # kline_data를 numpy 배열로 변환
        np_array = np.array(kline_data, dtype=float)

        # 주어진 열에서 기준값과 정확히 일치하는 행의 인덱스 찾기
        row_indices = np.where(np_array[:, column_index] == threshold)[0]

        # 조건을 만족하는 첫 번째 인덱스를 반환하거나, 없으면 None 반환
        return int(row_indices[0]) if row_indices.size > 0 else None
    
    # 캔들 길이를 분석한다.
    def __candle_lengths(self, kline_data_lv3: list):
        """
        1. 기능 : 개별 kline 데이터의 캔들스틱 길이 요소를 계산
        2. 매개변수:
            kline_data_single (list): 하나의 kline 데이터, [time, open, high, low, close, ...] 형식
        """
        open_price = float(kline_data_lv3[1])
        high_price = float(kline_data_lv3[2])
        low_price = float(kline_data_lv3[3])
        close_price = float(kline_data_lv3[4])

        # 캔들 길이 계산
        upper_wick_length = abs(high_price - max(open_price, close_price))
        lower_wick_length = abs(low_price - min(open_price, close_price))
        body_length = abs(open_price - close_price)
        total_length = abs(high_price - low_price)
        #윗꼬리 길이, 아래꼬리 길이, 몸통길이, 전체 길이.
        return (upper_wick_length, lower_wick_length, body_length, total_length)
    
    # np.array 데이터에서 지정 index위치의 증감 현황과 포지션 상태를 반환한다.
    def __trade_score(self, col_idx:int, kline_data_lv2) -> Tuple[bool, int]:
        column_values = kline_data_lv2[::-1, col_idx]
        """
        1. 기능 : np.array의 값의 연속성을 계산하고 현재 등락 상태를 반환한다.
        2. 매개변서
            1) col_idx : 자료의 column_index값
            2) kline_data_lv2 : kline_data.get(interval)
        """        
        diffs = np.diff(column_values)
        is_decreasing = diffs < 0
        long_point = np.argmax(~is_decreasing) + 1 if np.any(~is_decreasing) else len(column_values)
        
        is_decreasing = diffs > 0
        short_point = np.argmax(~is_decreasing) + 1 if np.any(~is_decreasing) else len(column_values)
        
        if long_point > short_point:
            return (True, long_point)
        else:
            return (False, short_point)
        
    # kline에서 특정값의 인덱스를 찾는다.
    def __get_row_indices_by_threshold(
        self,
        kline_data_lv1: List[List[Union[str, int]]],
        threshold: float,
        col_idx: int,
    ) -> Optional[int]:
        """
        1. 기능 : kline에서 특정값의 인덱스를 찾는다.
        2. 매개변수
            1) klline_data : 찾고자하는 데이터의 interval.get()
            2) threshold : 찾고자하는 값
            3) col_idx : 자료의 column_index값
        """

        # kline_data를 numpy 배열로 변환
        np_array = np.array(kline_data, dtype=float)

        # 주어진 열에서 기준값과 정확히 일치하는 행의 인덱스 찾기
        row_indices = np.where(np_array[:, col_idx] == threshold)[0]

        # 조건을 만족하는 첫 번째 인덱스를 반환하거나, 없으면 None 반환
        return int(row_indices[0]) if row_indices.size > 0 else None

    def scenario_1(self, symbol: str):
        ticker_data = self.kline_data.get(symbol)
        if not isinstance(ticker_data, dict):
            pass
        
        total_signal = []
        total_score = []
        
        # 기초데이터 생성.
        data_convert = self.__convert_kline_array(kline_data=self.kline_data,
                                                  symbol=symbol)
        for idx in self.ACTIVE_COLUMNS_INDEX:
            signal, score = self.__trade_score(col_idx=idx, kline_data_lv2=data_convert)
            total_score.append(score)
            total_signal.append(signal)
        return (total_signal, total_score)
        
        









    # def _get_row_idices_by_threshold_range(
    #     self,
    #     kline_data: List[List[Union[str, int]]],
    #     threshold_min: float,
    #     threshold_max: float,
    #     column_index: int,
    # ) -> Optional[int]:
    #     """
    #     1. 기능 : kline에서 특정 범위 내 값의 인덱스를 찾는다.
    #     2. 매개변수
    #         1) klline_data : 찾고자하는 데이터의 interval.get()
    #         2) threshold_min : 찾고자 하는 값의 최소값
    #         3) threshold_max : 찾고자 하는 값의 최대값
    #         4) column_index : 자료의 column_index값
    #     """
    #     # kline_data를 numpy 배열로 변환
    #     np_array = np.array(kline_data, dtype=float)

    #     # 주어진 열에서 범위 내에 있는 행의 인덱스 찾기
    #     row_indices = np.where(
    #         (np_array[:, column_index] >= threshold_min)
    #         & (np_array[:, column_index] <= threshold_max)
    #     )[0]

    #     # 조건을 만족하는 첫 번째 인덱스를 반환하거나, 없으면 None 반환
    #     return int(row_indices[0]) if row_indices.size > 0 else None

    # # kline 데이터가 속성에 지정된 interval값에 따라 올바르게 존재하는지 점검함.
    # def _validate_kline_data(self, ticker: str) -> bool:
    #     """
    #     1. 기능 : kline의 데이터가 interval에 맞도록 올바르게 존재하는지 여부를 점검한다.
    #     2. 매개변수
    #         1) ticker : 예)BTCUSDT
    #     """
    #     if not isinstance(self.kline_data, dict):
    #         return False
    #     kline_data_for_ticker = self.kline_data.get(ticker, {})

    #     # 티커의 kline 데이터가 존재하고 딕셔너리인지 확인
    #     if not isinstance(kline_data_for_ticker, dict) or not kline_data_for_ticker:
    #         return False

    #     # 각 interval의 데이터가 존재하고 올바른지 확인
    #     if not isinstance(self.intervals, list):
    #         return False

    #     for interval in self.intervals:
    #         interval_data = kline_data_for_ticker.get(interval, {})

    #         # interval 데이터가 딕셔너리 형태이고 비어있지 않은지 검사
    #         if not isinstance(interval_data, list) or not interval_data:
    #             return False
    #     return True

    # # candle의 길이를 구한다.
    

    # def case1_conditions(
    #     self, ticker: str
    # ) -> Tuple[int, int, bool, Optional[int], bool]:
    #     """
    #     1. 기능: 포지션 진입 시그널을 계산한다. Spot 시장의 경우 LONG 포지션만 진입 가능.
    #     2. 매개변수:
    #         - ticker (str): 예) BTCUSDT
    #     3. 반환값:
    #         - position (int): 1 = LONG, 2 = SHORT, 0 = NO POSITION  -> 현재 포지션
    #         - trend_score (int): 연속성 점수 -> candle 꼬리길이가 30%를 넘으면 안됨.
    #         - is_continuous (bool): 연속된 트렌드 여부 -> trend_score를 기준으로 bool반영
    #         - time_diff (Optional[int]): 전고점/전저점과의 시간 차이
    #         - is_threshold_broken (bool): 현재 가격이 전고점/전저점 임계값을 넘었는지 여부
    #     """
    #     trend_check_interval = "1h"
    #     trend_period = "3d"
    #     position_check_interval = "5m"
    #     fail_data = (0, 0, False, 0, False)
    #     print(ticker)
    #     if not isinstance(self.intervals, list) or not isinstance(
    #         self.kline_data, dict
    #     ):
    #         return fail_data
    #     # 유효성 검사: 인터벌 확인
    #     if (
    #         trend_check_interval not in self.intervals
    #         or position_check_interval not in self.intervals
    #     ):
    #         raise ValueError(f"유효하지 않은 interval 값이 있음.")

    #     # 데이터 유효성 검사
    #     if not self._validate_kline_data(ticker=ticker):
    #         return fail_data

    #     ticker_data = self.kline_data.get(ticker, {})

    #     # 트렌드 점수 계산
    #     trend_data_high_low = self._compute_trend_scores(
    #         ticker_data.get(trend_check_interval, {})
    #     )
    #     trend_data_position = self._compute_trend_scores(
    #         ticker_data.get(position_check_interval, {})
    #     )

    #     if not trend_data_high_low or not trend_data_position:
    #         return fail_data

    #     # 포지션 결정
    #     last_trend_position = trend_data_position[-1]
    #     position = 1 if last_trend_position[0] else (2 if last_trend_position[1] else 0)

    #     # 연속성 점수 및 유효 캔들 점수 계산
    #     continuity_score = last_trend_position[2]
    #     valid_candle_score = last_trend_position[3]
    #     trend_score = min(continuity_score, valid_candle_score)
    #     is_continuous = trend_score >= 3

    #     # 데이터 준비
    #     trend_interval_data = ticker_data.get(trend_check_interval)

    #     # kline_data.clear()실행시 False로 반환처리 한다.
    #     # tickers update시 잔존하는 queue값 잔존시 kline_data가 생성되므로 이에 대한 False로 반환
    #     if len(trend_interval_data) == 1:
    #         return fail_data

    #     # 전고점/전저점 및 시간 차이 계산
    #     time_diff = None
    #     is_threshold_broken = False

    #     try:
    #         if position == 1:  # LONG
    #             previous_high = self._get_previous_high(
    #                 kline_data=trend_interval_data[:-1]
    #             )
    #             high_index = self._get_row_indices_by_threshold(
    #                 kline_data=trend_interval_data[:-1],
    #                 threshold=previous_high,
    #                 column_index=2,
    #             )
    #             is_threshold_broken = previous_high < float(trend_interval_data[-1][2])
    #             time_diff = (
    #                 len(trend_data_high_low) - high_index
    #                 if high_index is not None
    #                 else None
    #             )

    #         elif position == 2:  # SHORT
    #             previous_low = self._get_previous_low(
    #                 kline_data=trend_interval_data[:-1]
    #             )
    #             low_index = self._get_row_indices_by_threshold(
    #                 kline_data=trend_interval_data[:-1],
    #                 threshold=previous_low,
    #                 column_index=3,
    #             )
    #             is_threshold_broken = previous_low > float(trend_interval_data[-1][2])
    #             time_diff = (
    #                 len(trend_data_high_low) - low_index
    #                 if low_index is not None
    #                 else 0
    #             )
    #     except:
    #         print(trend_interval_data)
    #         print(ticker)
    #         raise ValueError("ERROR")

    #     return position, trend_score, is_continuous, time_diff, is_threshold_broken

    # def case2_conditions(
    #     self, ticker_data
    # ) -> Tuple[int, int, bool, Optional[int], bool]:
    #     """
    #     1. 기능: 포지션 진입 시그널을 계산한다. Spot 시장의 경우 LONG 포지션만 진입 가능.
    #     2. 매개변수:
    #         - ticker (str): 예) BTCUSDT
    #     3. 반환값:
    #         - position (int): 1 = LONG, 2 = SHORT, 0 = NO POSITION  -> 현재 포지션
    #         - trend_score (int): 연속성 점수 -> candle 꼬리길이가 30%를 넘으면 안됨.
    #         - is_continuous (bool): 연속된 트렌드 여부 -> trend_score를 기준으로 bool반영
    #         - time_diff (Optional[int]): 전고점/전저점과의 시간 차이
    #         - is_threshold_broken (bool): 현재 가격이 전고점/전저점 임계값을 넘었는지 여부
    #     """
    #     trend_check_interval = "1h"
    #     trend_period = "3d"
    #     position_check_interval = "5m"
    #     fail_data = (0, 0, False, 0, False)

    #     # if not isinstance(self.intervals, list) or not isinstance(
    #     #     self.kline_data, dict
    #     # ):
    #     #     return fail_data
    #     # 유효성 검사: 인터벌 확인
    #     # if (
    #     #     trend_check_interval not in self.intervals
    #     #     or position_check_interval not in self.intervals
    #     # ):
    #     #     raise ValueError(f"유효하지 않은 interval 값이 있음.")

    #     # # 데이터 유효성 검사
    #     # if not self._validate_kline_data(ticker=ticker):
    #     #     return fail_data

    #     # ticker_data = self.kline_data.get(ticker, {})

    #     # 트렌드 점수 계산
    #     trend_data_high_low = self._compute_trend_scores(
    #         ticker_data.get(trend_check_interval, {})
    #     )
    #     trend_data_position = self._compute_trend_scores(
    #         ticker_data.get(position_check_interval, {})
    #     )

    #     if not trend_data_high_low or not trend_data_position:
    #         return fail_data

    #     # 포지션 결정
    #     last_trend_position = trend_data_position[-1]
    #     position = 1 if last_trend_position[0] else (2 if last_trend_position[1] else 0)

    #     # 연속성 점수 및 유효 캔들 점수 계산
    #     continuity_score = last_trend_position[2]
    #     valid_candle_score = last_trend_position[3]
    #     trend_score = min(continuity_score, valid_candle_score)
    #     is_continuous = trend_score >= 3

    #     # 데이터 준비
    #     trend_interval_data = ticker_data.get(trend_check_interval)

    #     # kline_data.clear()실행시 False로 반환처리 한다.
    #     # tickers update시 잔존하는 queue값 잔존시 kline_data가 생성되므로 이에 대한 False로 반환
    #     if len(trend_interval_data) == 1:
    #         return fail_data

    #     # 전고점/전저점 및 시간 차이 계산
    #     time_diff = None
    #     is_threshold_broken = False

    #     try:
    #         if position == 1:  # LONG
    #             previous_high = self._get_previous_high(
    #                 kline_data=trend_interval_data[:-1]
    #             )
    #             high_index = self._get_row_indices_by_threshold(
    #                 kline_data=trend_interval_data[:-1],
    #                 threshold=previous_high,
    #                 column_index=2,
    #             )
    #             is_threshold_broken = previous_high < float(trend_interval_data[-1][2])
    #             time_diff = (
    #                 len(trend_data_high_low) - high_index
    #                 if high_index is not None
    #                 else None
    #             )

    #         elif position == 2:  # SHORT
    #             previous_low = self._get_previous_low(
    #                 kline_data=trend_interval_data[:-1]
    #             )
    #             low_index = self._get_row_indices_by_threshold(
    #                 kline_data=trend_interval_data[:-1],
    #                 threshold=previous_low,
    #                 column_index=3,
    #             )
    #             is_threshold_broken = previous_low > float(trend_interval_data[-1][2])
    #             time_diff = (
    #                 len(trend_data_high_low) - low_index
    #                 if low_index is not None
    #                 else 0
    #             )
    #     except:
    #         print(trend_interval_data)
    #         print(ticker)
    #         raise ValueError("ERROR")

    #     return position, trend_score, is_continuous, time_diff, is_threshold_broken


    
        