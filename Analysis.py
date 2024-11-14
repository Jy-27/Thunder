import asyncio
import numpy as np
import utils
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple


# 멀티프로세스로 실행할 것.
class AnalysisManager:
    def __init__(self, kline_data, intervals, tickers):
        self.kline_data = kline_data
        self.intervals: List[str] = intervals
        self.tickers: List[str] = tickers
        # self.point: Optional[List[int]] = None

    # kline 데이터의 자료를 리터럴 변환
    def _convert_kline_data_to_literals(self) -> Dict[str, Dict[str, Union[Any]]]:
        """
        1. 기능 : kline_data를 리터럴 처리
        2. 매개변수 : 해당없음
        """
        for ticker in self.tickers:
            # 거래 데이터가 딕셔너리이며 해당 ticker 데이터가 존재하는지 확인
            if not isinstance(self.kline_data, dict) or ticker not in self.kline_data:
                continue

            ticker_data = self.kline_data[ticker]

            for interval in self.intervals:
                # ticker 데이터가 딕셔너리이며 해당 interval 데이터가 있는지 확인
                if not isinstance(ticker_data, dict) or interval not in ticker_data:
                    continue

                interval_data = ticker_data[interval]

                # 중첩된 리스트를 리터럴 형태로 변환
                literals_converted_data = utils._convert_nested_list_to_literals(
                    interval_data
                )
                self.kline_data[ticker][interval] = literals_converted_data

        return self.kline_data

    # kline 데이터 자료형을 np.array형으로 변환
    def _convert_kline_data_to_array(self) -> Dict[str, Dict[str, np.ndarray]]:
        """
        1. 기능 : kline_data 전체를 np.array형으로 변환
        2. 매개변수 : 해당없음.
        
        """
        for ticker in self.tickers:
            # 거래 데이터가 딕셔너리이며 해당 ticker 데이터가 존재하는지 확인
            if not isinstance(self.kline_data, dict) or ticker not in self.kline_data:
                continue

            ticker_data = self.kline_data[ticker]

            for interval in self.intervals:
                # ticker 데이터가 딕셔너리이며 해당 interval 데이터가 있는지 확인
                if not isinstance(ticker_data, dict) or interval not in ticker_data:
                    continue

                interval_data = ticker_data[interval]

                # 중첩된 리스트를 리터럴 형태로 변환
                numpy_array = np.array(object=interval_data, dtype=float)
                self.kline_data[ticker][interval] = numpy_array
        return self.kline_data

    # interval별 연속 상승/하락에 대한 값을 연산 반환한다.
    def _compute_trend_scores(
        self, kline_data: List[List[Union[str, int]]]
    ) -> List[List[int]]:
        """
        1. 기능 : ohlcv의 LONG, SHORT 연속성 데이터를 연산한다.
        2. 매개변수
            1) kline_data : kline의 각 interval값 입력(중첩 dict 최하단 데이터)
        """
        trend_data = []  # 각 캔들에 대한 트렌드 점수 [Long, Short, Continuity]

        for index, data in enumerate(kline_data):
            if index == 0:
                trend_data.append([0, 0, 0])  # 첫 번째 데이터 초기화
                continue

            prev_index = index - 1
            current_open = float(data[1])
            current_close = float(data[4])

            prev_trend = trend_data[prev_index]
            prev_continuity = prev_trend[2]

            is_bullish = current_open < current_close
            is_bearish = current_open > current_close

            if is_bullish:
                continuity_count = prev_continuity + 1 if prev_trend[0] else 1
            elif is_bearish:
                continuity_count = prev_continuity + 1 if prev_trend[1] else 1
            else:
                continuity_count = 0

            long_score = 1 if is_bullish else 0
            short_score = 1 if is_bearish else 0
            trend_data.append([long_score, short_score, continuity_count])

        return trend_data

    # kline데이터의 'high'값의 max값을 반환한다. (전고점))
    def _get_previous_high(self, kline_data: List[Union[str, int]]) -> float:
        """
        1. 기능 : kline 데이터의 max high값을 반환한다.
        2. 매개변수
            1) kline_data : get(interval)값을 입력
        """
        np_array = np.array(object=kline_data, dtype=float)
        return np.max(np_array[:, 2])

    # kline데이터의 'low'값의 min값을 반환한다. (전저점))
    def _get_previous_low(self, kline_data: List[Union[str, int]]) -> float:
        """
        1. 기능 : kline 데이터의 min low값을 반환한다.
        2. 매개변수
            1) kline_data : get(interval)값을 입력
        """
        np_array = np.array(object=kline_data, dtype=float)
        return np.min(np_array[:, 3])

    # kline에서 특정값의 인덱스를 찾는다.
    def _get_row_indices_by_threshold(
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

    def _get_row_indices_by_threshold_range(
            self,
            kline_data: List[List[Union[str, int]]],
            threshold_min: float,
            threshold_max: float,
            column_index: int,
        ) -> Optional[int]:
        """
        1. 기능 : kline에서 특정 범위 내 값의 인덱스를 찾는다.
        2. 매개변수
            1) klline_data : 찾고자하는 데이터의 interval.get()
            2) threshold_min : 찾고자 하는 값의 최소값
            3) threshold_max : 찾고자 하는 값의 최대값
            4) column_index : 자료의 column_index값
        """
        # kline_data를 numpy 배열로 변환
        np_array = np.array(kline_data, dtype=float)

        # 주어진 열에서 범위 내에 있는 행의 인덱스 찾기
        row_indices = np.where((np_array[:, column_index] >= threshold_min) & 
                            (np_array[:, column_index] <= threshold_max))[0]

        # 조건을 만족하는 첫 번째 인덱스를 반환하거나, 없으면 None 반환
        return int(row_indices[0]) if row_indices.size > 0 else None

    # kline 데이터가 속성에 지정된 interval값에 따라 올바르게 존재하는지 점검함.
    def _validate_kline_data(self, ticker: str) -> bool:
        """
        1. 기능 : kline의 데이터가 interval에 맞도록 올바르게 존재하는지 여부를 점검한다.
        2. 매개변수
            1) ticker : 예)BTCUSDT
        """
        kline_data_for_ticker = self.kline_data.get(ticker, {})

        # 티커의 kline 데이터가 존재하고 딕셔너리인지 확인
        if not isinstance(kline_data_for_ticker, dict) or not kline_data_for_ticker:
            return False

        # 각 interval의 데이터가 존재하고 올바른지 확인
        for interval in self.intervals:
            interval_data = kline_data_for_ticker.get(interval, {})
            
            # interval 데이터가 딕셔너리 형태이고 비어있지 않은지 검사
            if not isinstance(interval_data, list) or not interval_data:
                return False
        return True

    # candle의 길이를 구한다.
    def _candle_lengths(self, kline_data_single: list):
        """
        1. 기능 : 개별 kline 데이터의 캔들스틱 길이 요소를 계산
        2. 매개변수:
            kline_data_single (list): 하나의 kline 데이터, [time, open, high, low, close, ...] 형식
        
        반환값:
            Tuple[float, float, float, float]: 각각 윗꼬리 길이, 아랫꼬리 길이, 몸통 길이, 전체 길이
        """
        open_price = float(kline_data_single[1])
        high_price = float(kline_data_single[2])
        low_price = float(kline_data_single[3])
        close_price = float(kline_data_single[4])
        
        # 캔들 길이 계산
        upper_wick_length = abs(high_price - max(open_price, close_price))
        lower_wick_length = abs(low_price - min(open_price, close_price))
        body_length = abs(open_price - close_price)
        total_length = abs(high_price - low_price)
        
        return (upper_wick_length, lower_wick_length, body_length, total_length)
        
        
    def case1_conditions(self, ticker: str) -> Tuple[int, bool, Optional[int]]:
        """
        1. 기능 : position 진입 시그널을 나타낸다. Spot시장일경우 position은 long만 진입할 것.
        2. 매개변수
            1) ticker : 예) BTCUSDT
        """
        trend_check_interval = '1h'
        trend_period = '3d'
        position_check_interval = '5m'
        
        if trend_check_interval not in self.intervals or position_check_interval not in self.intervals:
            raise ValueError(f'유효하지 않은 interval 값이 있음.')
        
        # 데이터 유효성 점검
        if not self._validate_kline_data(ticker=ticker):
            raise ValueError(f'{ticker} - kline 데이터가 유효하지 않음.')

        ticker_data = self.kline_data.get(ticker, {})
        trend_data_for_high_low = self._compute_trend_scores(ticker_data.get(trend_check_interval, {}))
        trend_data_for_position = self._compute_trend_scores(ticker_data.get(position_check_interval, {}))

        if not trend_data_for_high_low or not trend_data_for_position:
            raise ValueError(f'{ticker}의 interval 데이터가 유효하지 않음.')

        # 포지션 결정
        if trend_data_for_position[-1][0]:
            position = 1  # LONG
        elif trend_data_for_position[-1][1]:
            position = 2  # SHORT
        else:
            position = 0  # NO POSITION

        # 연속성 여부 점검
        score = trend_data_for_position[-1][2]
        is_continuous_trend = score >= 3  # 연속성 여부 판단
        
        check_interval_data = self.kline_data.get(ticker).get(trend_check_interval)

        # 전고점 또는 전저점과의 시간 차이 계산
        time_difference = None
        is_over_threshold = False
        if position == 1:
            previous_high = self._get_previous_high(kline_data=check_interval_data[:-1])
            high_index = self._get_row_indices_by_threshold(kline_data=check_interval_data[:-1],
                                                            threshold=previous_high,
                                                            column_index=2)
            is_over_threshold = previous_high < float(check_interval_data[-1][2])
            time_difference = int(len(trend_data_for_high_low) - high_index) if high_index is not None else None
        elif position == 2:
            previous_low = self._get_previous_low(kline_data=check_interval_data[:-1])
            low_index = self._get_row_indices_by_threshold(kline_data=check_interval_data[:-1],
                                                        threshold=previous_low,
                                                        column_index=3)
            is_over_threshold = previous_low > float(check_interval_data[-1][2])
            time_difference = int(len(trend_data_for_high_low) - low_index) if low_index is not None else None

        return (position, score, is_continuous_trend, time_difference, is_over_threshold)
