import asyncio
import numpy as np
import utils
import copy
from collections import defaultdict
from typing import List, Dict, Optional, Union, Any, Tuple, Final
from numpy.typing import NDArray


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


# 멀티프로세스로 실행할 것.
class AnalysisManager:
    def __init__(self, intervals: List, back_test: bool = False):  # , symbols: list):
        self.back_test = back_test
        self.symbols = []
        self.kline_data = {}
        self.intervals = []
        self.maps_interval = {interval: idx for idx, interval in enumerate(intervals)}
        self.OHLCV_COLUMNS: Final[List[str]] = [
            "Open Time",  # 0
            "Open",  # 1
            "High",  # 2
            "Low",  # 3
            "Close",  # 4
            "Volume",  # 5
            "Close Time",  # 6
            "Quote Asset Volume",  # 7
            "Number of Trades",  # 8
            "Taker Buy Base Asset Volume",  # 9
            "Taker Buy Quote Asset Volume",  # 10
            "Ignore",  # 11
        ]
        self.ACTIVE_COLUMNS_INDEX: List[int] = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]
        self.intervals = intervals
        # np.array([])로 초기화 후 추가 하는 작업은 성능저하 생기므로 list화 한 후 np.array처리함.
        self.case_1 = []
        self.case_2 = []
        self.case_3 = []
        self.case_4 = []
        self.case_5 = []
        self.case_6 = []
        self.case_7 = []
        self.case_8 = []
        self.case_9 = []
        self.case_10 = []
        self.case_11 = []
        self.case_12 = []
        self.case_13 = []
        self.case_14 = []

    # def set_data_length(self, kline_data_v3)
    def reset_cases(self):
        for i in range(1, 15):
            getattr(self, f"case_{i}").clear()

    """
    case들을 속성값에 저장시 반드시 tuple or list로 한번 감싼 후 추가할 것.
    interval데이터 분리 및 조회를 용이하기 위함.    
    """

    def __oscillator(self, kline_data_lv3, col, short_window, long_window):
        volume = kline_data_lv3[:, col]

        # 이동평균 계산
        short_ma = np.convolve(
            volume, np.ones(short_window) / short_window, mode="valid"
        )
        long_ma = np.convolve(volume, np.ones(long_window) / long_window, mode="valid")

        # 두 이동평균 배열 길이 맞춤 (슬라이싱 또는 패딩 필요)
        min_length = min(len(short_ma), len(long_ma))
        short_ma = short_ma[-min_length:]
        long_ma = long_ma[-min_length:]

        # 0 또는 NaN 값 처리
        with np.errstate(divide="ignore", invalid="ignore"):
            volume_oscillator = np.where(
                (long_ma == 0) | np.isnan(long_ma),
                np.nan,  # 분모가 0이거나 NaN이면 NaN 반환
                (short_ma - long_ma) / long_ma * 100,
            )

        return volume_oscillator

    def __sort_indices_by_column_ascending(
        self, kline_data_lv3: np.ndarray, col: int
    ) -> np.ndarray:
        """
        2차원 np.ndarray의 특정 column을 기준으로 오름차순 정렬된 인덱스를 반환.
        """
        if len(kline_data_lv3.shape) != 2:
            raise ValueError("Input array must be 2-dimensional.")
        if col < 0 or col >= kline_data_lv3.shape[1]:
            raise IndexError(
                f"Column index {col} is out of bounds for array with shape {kline_data_lv3.shape}."
            )
        return np.argsort(kline_data_lv3[:, col])

    def __sort_indices_by_column_descending(
        self, kline_data_lv3: np.ndarray, col: int
    ) -> np.ndarray:
        """
        2차원 np.ndarray의 특정 column을 기준으로 내림차순 정렬된 인덱스를 반환.
        """
        if len(kline_data_lv3.shape) != 2:
            raise ValueError("Input array must be 2-dimensional.")
        if col < 0 or col >= kline_data_lv3.shape[1]:
            raise IndexError(
                f"Column index {col} is out of bounds for array with shape {kline_data_lv3.shape}."
            )
        return np.argsort(kline_data_lv3[:, col])[::-1]

    def case_1_data_length(self, kline_data_lv3: np.ndarray):
        """
        1. 기능 : 데이터 길이 정보를 저장한다.
        2. 매개변수
            1) kline_data_v3 : interval data

        3. 추가설명
            >> 각 case검토건중 이부는 좌표값만 연산된다. 이때 기준잡기 위하여 데이터길이를 연산한다.
            index값 확인이 필요하다면 길이 -1 하면 된다.
        """
        self.case_1.append(len(kline_data_lv3))

    def case_2_candle_length(self, kline_data_lv3: np.ndarray):
        """
        1. 기능 : 캔들 길이를 벡터 분석한다.
        2. 매개변수
            1) kline_data_v3 : interval data
        """
        open_prices = kline_data_lv3[:, 1]
        high_prices = kline_data_lv3[:, 2]
        low_prices = kline_data_lv3[:, 3]
        close_prices = kline_data_lv3[:, 4]

        # 캔들 길이 계산
        upper_wick_lengths = np.abs(high_prices - np.maximum(open_prices, close_prices))
        lower_wick_lengths = np.abs(low_prices - np.minimum(open_prices, close_prices))
        body_lengths = np.abs(open_prices - close_prices)
        total_lengths = np.abs(high_prices - low_prices)
        # 윗꼬리 길이, 아래꼬리 길이, 몸통길이, 전체 길이.
        self.case_2.append(
            (
                np.column_stack(
                    (
                        upper_wick_lengths,
                        lower_wick_lengths,
                        body_lengths,
                        total_lengths,
                    )
                )
            )
        )

    # 연속증가 및 연속하락 구간을 찾는다.
    def case_3_continuous_trend_position(
        self, kline_data_lv3: np.ndarray, col: int = 4
    ):
        """
        kline_data_lv3가 numpy 배열일 때, 연속 증가와 감소 구간의 위치를 찾습니다.
        """
        # 1. 가격 데이터 (예: close 가격이 4번째 열이라고 가정)
        data = kline_data_lv3[:, col]

        # 2. 데이터의 변화 계산
        diff = np.diff(data)
        trend = np.sign(diff)  # 증가: 1, 감소: -1, 동일: 0

        # 3. 변화 탐지 (증가/감소 방향이 바뀌는 지점)
        trend_change = np.diff(trend)
        split_indices = np.where(trend_change != 0)[0] + 1

        # 4. 연속 구간의 시작과 끝 인덱스
        segment_starts = np.r_[0, split_indices]
        segment_ends = np.r_[split_indices, len(data) - 1]

        # 5. 증가/감소 구간 필터링
        increase_positions = [
            (start, end)
            for start, end in zip(segment_starts, segment_ends)
            if np.all(trend[start:end] == 1)
        ]
        decrease_positions = [
            (start, end)
            for start, end in zip(segment_starts, segment_ends)
            if np.all(trend[start:end] == -1)
        ]

        self.case_3.append((increase_positions, decrease_positions))

    # 가장 마지막값이 이전값의 누적 합계보다 몇개의 데이터보다 큰지 연산한다.
    def case_4_process_neg_counts(self, kline_data_lv3: np.ndarray, col: int):
        """
        1. 기능 : 마지막 데이터의 값이 앞의 데이터의 누계합계보다 얼마나 큰지 연산한다.
        2. 매개변수
            1) kline_data : interval data
            2) col : 연산하고 싶은 컬럼값


        """
        col_data = kline_data_lv3[:, col]
        rev_cumsum = np.cumsum(col_data[::-1])[::-1]
        results = rev_cumsum - (col_data[-1] * 2)
        neg_count = np.sum(results < 0)
        adj_neg_count = neg_count - 1
        self.case_4.append(
            (max(adj_neg_count, 0) if neg_count > 0 else len(kline_data_lv3))
        )

    # 두 값의 차이내고 이전 값의 누적 합계보다 몇개의 데이터보다 큰지 연산한다.
    def case_5_diff_neg_counts(self, kline_data_lv3: np.ndarray, col1: int, col2: int):
        """
        두 컬럼의 차이 절대값을 기준으로 음수 개수를 계산하고 조건에 따라 반환.

        조건:
        1. 보정된 음수 개수 < 0이면 0 반환
        2. 음수 개수 == 0이면 데이터 길이를 반환

        :param data: 2D numpy 배열
        :param col1: 첫 번째 컬럼 인덱스
        :param col2: 두 번째 컬럼 인덱스
        :return: 보정된 음수 개수 또는 조건에 따른 값
        """
        # 두 컬럼의 차이의 절대값 계산
        abs_diff = np.abs(kline_data_lv3[:, col1] - kline_data_lv3[:, col2])

        # 누적합을 뒤에서부터 계산
        rev_cumsum = np.cumsum(abs_diff[::-1])[::-1]
        results = rev_cumsum - (abs_diff[-1] * 2)

        # 음수 개수 계산
        neg_count = np.sum(results < 0)

        # 보정값 -1 적용
        adj_neg_count = neg_count - 1

        # 조건에 따른 반환
        self.case_5.append(max(adj_neg_count, 0) if neg_count > 0 else 0)

    def case_6_ocillator_volume(
        self, kline_data_lv3: np.ndarray, short_window: int = 5, long_window=10
    ):
        self.case_6.append(
            self.__oscillator(
                kline_data_lv3=kline_data_lv3,
                col=9,
                short_window=short_window,
                long_window=long_window,
            )
        )

    def case_7_ocillator_value(
        self, kline_data_lv3: np.ndarray, short_window: int = 5, long_window=10
    ):
        self.case_7.append(
            self.__oscillator(
                kline_data_lv3=kline_data_lv3,
                col=10,
                short_window=short_window,
                long_window=long_window,
            )
        )

    def case_8_sorted_indices(
        self, kline_data_lv3: np.ndarray, high_col: int, low_col: int
    ):
        high_idx = np.argmax(kline_data_lv3[:, high_col])
        low_idx = np.argmin(kline_data_lv3[:, low_col])
        
        last_idx = len(kline_data_lv3) - 1
        
        is_high = high_idx == last_idx
        is_low = low_idx == last_idx
        
        self.case_8.append([is_high, is_low])

    def case_9_rsi(
        self, kline_data_lv3: np.ndarray, col: int, window: int = 14
    ) -> np.ndarray:
        """
        2차원 np.ndarray에서 특정 column을 기준으로 RSI 계산.

        Parameters:
        - data (np.ndarray): 2차원 배열 (행: 데이터 포인트, 열: 속성)
        - column (int): RSI를 계산할 기준 열 (예: 종가)
        - window (int): RSI를 계산할 기간 (기본값: 14)

        Returns:
        - np.ndarray: RSI 값 배열 (NaN 포함, 길이는 원본 데이터와 동일)
        """
        # 특정 열의 데이터를 추출
        prices = kline_data_lv3[:, col]

        # 데이터 크기에 맞게 window 값 조정
        actual_window = min(window, len(prices) - 1)

        # 가격 변화 계산
        deltas = np.diff(prices)  # 현재 가격과 이전 가격의 차이
        gains = np.maximum(deltas, 0)  # 상승폭 (음수는 0으로 처리)
        losses = np.abs(np.minimum(deltas, 0))  # 하락폭 (양수는 0으로 처리)

        # 평균 상승/하락 계산
        avg_gain = np.empty_like(prices)
        avg_loss = np.empty_like(prices)
        avg_gain[:actual_window] = np.nan  # 초기값 NaN
        avg_loss[:window] = np.nan  # 초기값 NaN

        # 초기 평균 계산
        avg_gain[actual_window] = np.mean(gains[:actual_window])
        avg_loss[actual_window] = np.mean(losses[:actual_window])

        # 지수 이동 평균 방식으로 계산
        for i in range(actual_window + 1, len(prices)):
            avg_gain[i] = (
                avg_gain[i - 1] * (actual_window - 1) + gains[i - 1]
            ) / actual_window
            avg_loss[i] = (
                avg_loss[i - 1] * (actual_window - 1) + losses[i - 1]
            ) / actual_window

        # RS 계산 및 RSI 계산
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # 초기 window 기간은 NaN으로 설정
        rsi[:actual_window] = np.nan

        self.case_9.append(rsi)

    def case_10_macd(self, data, short_window=12, long_window=26, signal_window=9, volume_threshold=500):
        """
        NumPy 기반 MACD 계산과 거래 전략 수행
        :param prices: ndarray, 종가 데이터
        :param volumes: ndarray, 거래량 데이터
        :param short_window: Short EMA 기간 (기본값: 12)
        :param long_window: Long EMA 기간 (기본값: 26)
        :param signal_window: Signal EMA 기간 (기본값: 9)
        :param volume_threshold: 거래량 임계값 (기본값: 500)
        :return: 신호 배열 ('buy', 'sell', None), MACD, Signal, Histogram (ndarray)
        """
        # EMA 계산 함수
        
        prices=data[:,4]
        volumes=data[:,9]
        
        def ema(values, window):
            alpha = 2 / (window + 1)
            ema_values = np.zeros_like(values)
            ema_values[0] = values[0]
            for i in range(1, len(values)):
                ema_values[i] = alpha * values[i] + (1 - alpha) * ema_values[i - 1]
            return ema_values

        # MACD 계산
        ema_short = ema(prices, short_window)
        ema_long = ema(prices, long_window)
        macd = ema_short - ema_long
        signal = ema(macd, signal_window)
        histogram = macd - signal

        # print(ema_short)
        # print(ema_long)
        # print(macd)
        # print(signal)
        # print(histogram)

        # 거래 전략 신호 계산
        buy_signals = (macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1)) & (volumes > volume_threshold)
        # print(buy_signals)
        sell_signals = (macd < signal) & (np.roll(macd, 1) >= np.roll(signal, 1))
        # print(sell_signals)

        if buy_signals[-1]:
            self.case_10.append(1)
        elif sell_signals[-1]:
            self.case_10.append(2)
        else:
            self.case_10.append(0)




    def calculate_macd_numpy(prices, short_window=12, long_window=26, signal_window=9):
        """
        NumPy 기반 MACD, Signal, Histogram 계산
        :param prices: ndarray, 종가 데이터
        :param short_window: Short EMA 기간 (기본값: 12)
        :param long_window: Long EMA 기간 (기본값: 26)
        :param signal_window: Signal EMA 기간 (기본값: 9)
        :return: MACD, Signal, Histogram (ndarray)
        """
        # EMA 계산
        def ema(values, window):
            alpha = 2 / (window + 1)
            ema_values = np.zeros_like(values)
            ema_values[0] = values[0]
            for i in range(1, len(values)):
                ema_values[i] = alpha * values[i] + (1 - alpha) * ema_values[i - 1]
            return ema_values

        ema_short = ema(prices, short_window)
        ema_long = ema(prices, long_window)
        macd = ema_short - ema_long
        signal = ema(macd, signal_window)
        histogram = macd - signal
        return macd, signal, histogram

    def macd_trading_strategy_numpy(prices, volumes, macd, signal, volume_threshold=500):
        """
        NumPy 기반 MACD 전략으로 매수/매도 신호 계산
        :param prices: ndarray, 종가 데이터
        :param volumes: ndarray, 거래량 데이터
        :param macd: ndarray, MACD 값
        :param signal: ndarray, Signal 값
        :param volume_threshold: 거래량 임계값 (기본값: 500)
        :return: 신호 배열 ('buy', 'sell', None)
        """
        buy_signals = (macd > signal) & (np.roll(macd, 1) <= np.roll(signal, 1)) & (volumes > volume_threshold)
        sell_signals = (macd < signal) & (np.roll(macd, 1) >= np.roll(signal, 1))
        
        signals = np.full(prices.shape, None, dtype=object)
        signals[buy_signals] = 1
        signals[sell_signals] = 2
        return signals

    def scenario_3(self):
        scenario = 3
        is_order_signal = self.case_10[0]
        leverage = 10
        if is_order_signal > 0:
            return (True, is_order_signal, leverage, scenario)
        else:
            return (False, is_order_signal, leverage, scenario)

    def scenario_2(self):
        """
        적용 interval : 5m, 1h
        조건
            1) 연속 3회 상승 or 하락. >> case_3
            2) candle 의 몸통부분이 전체의 70% 이상.  >> case_2
            3) 오실리언 벨류 플러스 일경우. >> case_7
            4) 전고점 or 전저점 돌파.   >> case_8

        leverage : 2) 전고점 or 전저점 돌파 시간 diff
        """

        target_interval_5m = self.maps_interval["5m"]
        target_interval_15m = self.maps_interval["15m"]

        long_idx = 0
        short_idx = 1
        end_idx = -1

        # case_3연산시 조건에 안맞는 부분이 있을 수 있다. 그럴 경우를 대비한 검사.
        for i, (increase, decrease) in enumerate(self.case_3):
            if not increase or not decrease:  # 리스트가 비어있는지 확인
                return (False, 0, 0, 2)


        # 연속증가 / 연속 하락 구간을 찾는다. 없을 경우 fail
        is_case_3_long_last_idx = self.case_3[target_interval_5m][long_idx][end_idx][end_idx] == (self.case_1[target_interval_5m] - 1)
        is_case_3_long_count = np.diff(self.case_3[target_interval_5m][long_idx])[end_idx][0] >= 3

        is_case_3_short_last_idx = self.case_3[target_interval_5m][long_idx][end_idx][end_idx] == (self.case_1[target_interval_5m] - 1)
        is_case_3_short_count = np.diff(self.case_3[target_interval_5m][long_idx])[end_idx][0] >= 3

        if is_case_3_long_last_idx and is_case_3_long_count:
            position = 1

        elif is_case_3_short_last_idx and is_case_3_short_count:
            position = 2

        else:
            return (False, 0, 0, 2)
            

        # # 연속증가 / 연속 하락 구간을 찾는다. 없을 경우 fail
        # if self.case_3[target_interval_5m][long_idx][end_idx][end_idx] == (
        #     self.case_1[target_interval_5m] - 1
        # ):
        #     count = np.diff(self.case_3[target_interval_5m][long_idx])[end_idx][0]

        # elif self.case_3[target_interval_5m][short_idx][end_idx][end_idx] == (
        #     self.case_1[target_interval_5m] - 1
        # ):
        #     position = 2
        #     count = np.diff(self.case_3[target_interval_5m][short_idx])[end_idx][0]
        # else:
        #     return (False, 0, 0, 2)

        # candle길이 검토
        target_length_ratio = 0.5
        target_idx = -3
        # candle 몸통 비율 검토
        target_candle_data = self.case_2[target_interval_5m][target_idx:]
        if np.all(target_candle_data == 0):
            return (False, 0, 0, 2)

        # 분모 검사 추가
        if np.any(target_candle_data[:, 3] == 0):
            return (False, 0, 0, 2)

        length_ratio = target_candle_data[:, 2] / target_candle_data[:, 3]
        # 몸통 길이 비율이 target_length_ratio 보다 이상
        if not np.all(length_ratio >= target_length_ratio):
            return (False, 0, 0, 2)

        # 오실리언 벨유 플러스 여부 확인
        is_ocillator_value = self.case_7[target_interval_5m][-1] > 0

        if not is_ocillator_value:
            return (False, 0, 0, 2)

        # 전고점 / 전저점 돌파여부 확인
        # data_length = self.case_1[target_interval_15m] - 1

        hour_range_idx = -4 * 4
        leverage=10

        if position == 1 and self.case_8[target_interval_15m][long_idx]:
            return (True, position, leverage, 2)
        elif position == 2 and self.case_8[target_interval_15m][short_idx]:
            return (True, position, leverage, 2)
        else:
            return (False, 0, 0, 2)

    # def scenario_1(self):
    #     """
    #     적용 interval : 5m, 1h
    #     조건
    #         1) 연속 3회 상승 or 하락.
    #         2) 전고점 or 전저점 돌파.
    #         3) candle 의 몸통부분이 전체의 70% 이상.
    #         4) 오실리언 벨류 플러스 일경우.

    #     leverage : 2) 전고점 or 전저점 돌파 시간 diff
    #     """

    #     target_diff = 3
    #     interval_5m = 2

    #     is_case_5 = self.case_5[interval_5m] > 5

    #     case_3_data_increase = self.case_3[interval_5m][0]
    #     case_3_data_decrease = self.case_3[interval_5m][1]

    #     # 데이터가 없을경우 False를 반환한다.
    #     if not case_3_data_increase or not case_3_data_decrease:
    #         return (False, 0, 0, 2)

    #     target_data_max_idx = self.case_1[interval_5m] - 1
    #     if case_3_data_increase[-1][-1] == target_data_max_idx:
    #         diff_data = np.diff(case_3_data_increase)[-1][0]
    #         is_case_3 = (True, 1, diff_data)
    #     elif case_3_data_decrease[-1][-1] == target_data_max_idx:
    #         diff_data = np.diff(case_3_data_increase)[-1][0]
    #         is_case_3 = (True, 2, diff_data)
    #     else:
    #         is_case_3 = (False, 0, 0)

    #     if (
    #         is_case_5
    #         and is_case_3[0]
    #         and is_case_3[2] >= target_diff
    #         and self.case_4[0] > 5
    #     ):
    #         return is_case_3
    #     else:
    #         return (False, 0, 0, 2)


class Disposer:
    # kline 데이터의 자료를 리터럴 변환

    # 첫번째, 필수사항
    # 검토할 데이터를 연산이 용이하도록 np.array처리한다.
    def convert_kline_array(
        self, kline_data: Optional[Dict[str, Dict[str, List[Union[int, str]]]]] = None
    ) -> Dict[str, Dict[str, NDArray[np.float64]]]:
        """
        1. 기능 : 데이터를 연산하기 전에 self.kline_data를 numpy.array타입으로 변환한다.
        2. 매개변수 : 해당없음.

        수정사항
            24.11.27 : data를 parameter로 지정할까 고민했었으나, 불필요하다는 결론을 내림.

        """
        if kline_data is None:
            kline_data = self.kline_data
        result = {}
        for symbol, kline_data_symbol in kline_data.items():
            result[symbol] = {}
            for interval, kline_data_interval in kline_data_symbol.items():
                result[symbol][interval] = np.array(
                    object=kline_data_interval, dtype=np.float32
                )
        return result

    # 두번째, 선택사항
    # 데이터의 유효성을 검사한다. covert_kline_array실행 전에 진행한다.
    def describe_data_state(self) -> Dict[str, Dict[str, Optional[Any]]]:
        """
        1. 기능 : kline_data의 상태를 설명하고 유효하지 않은 항목을 반환한다.
        2. 매개변수 : 해당없음.
        """
        # 상태 초기화
        status = {"valid": [], "invalid": [], "status": None}

        # 1. 기본 데이터 상태 확인
        if not isinstance(self.symbols, list) or not self.symbols:
            status["invalid"].append(f"symbols 값이 유효하지 않음: {self.symbols}")
        else:
            status["valid"].append("symbols 값이 유효함")

        if not isinstance(self.intervals, list) or not self.intervals:
            status["invalid"].append(f"intervals 값이 유효하지 않음: {self.intervals}")
        else:
            status["valid"].append("intervals 값이 유효함")

        if not isinstance(self.kline_data, dict) or not self.kline_data:
            status["invalid"].append(
                f"kline_data 값이 유효하지 않음: {self.kline_data}"
            )
        else:
            status["valid"].append("kline_data 값이 유효함")

        # 2. 중첩된 데이터 상태 확인
        if isinstance(self.kline_data, dict):  # kline_data가 dict인지 확인
            for symbol, kline_data_symbol in self.kline_data.items():
                if not kline_data_symbol:
                    status["invalid"].append(
                        f"symbol '{symbol}'의 kline_data_symbol 값이 비어 있음"
                    )
                    continue

                for interval, kline_data_interval in kline_data_symbol.items():
                    if kline_data_interval.size > 0:
                        status["valid"].append(
                            f"symbol '{symbol}'의 interval '{interval}' 데이터가 유효함"
                        )
                    else:
                        status["invalid"].append(
                            f"symbol '{symbol}'의 interval '{interval}' 데이터가 비어 있음"
                        )

        # 최종 상태 결정
        status["status"] = len(status["invalid"]) == 0
        return status

    # np.array데이터의 최대값 또는 최소값을 반환한다.
    def __get_column_extreme(
        self, mode: str, data: NDArray[np.float64], col_idx: int
    ) -> float:
        """
        1. 기능 : 지정된 열(column)의 최대값 또는 최소값을 반환합니다.
        2. 매개변수:
            1) mode (str): "MAX" 또는 "MIN" (대소문자 구분 없음)
            2) data (NDArray[np.float64]): numpy 2D 배열
            3) col_idx (int): 대상 열의 인덱스 (0부터 시작)
        """
        # mode를 대문자로 변환
        mode = mode.upper()

        # col_idx 범위 검증
        if not (0 <= col_idx < data.shape[1]):
            raise ValueError(
                f"col_idx 값이 유효하지 않습니다 - col_idx: {col_idx}, 허용 범위: 0 ~ {data.shape[1] - 1}"
            )

        # mode에 따라 최대값 또는 최소값 반환
        if mode == "MAX":
            return np.max(data[:, col_idx])
        elif mode == "MIN":
            return np.min(data[:, col_idx])
        else:
            raise ValueError(f"mode 값이 유효하지 않습니다 - mode: {mode}")

    # kline에서 특정값의 인덱스를 찾는다.
    def __get_index_by_value(
        self,
        kline_data_interval: NDArray[np.float64],
        threshold: float,
        col_idx: int,
    ) -> Optional[int]:
        """
        1. 기능 : kline에서 특정값의 인덱스를 찾는다.
        2. 매개변수
            1) klline_data_interval : 찾고자하는 데이터의 interval.get()
            2) threshold : 찾고자하는 값
            3) col_idx : 자료의 col_idx값
        """
        # 주어진 열에서 기준값과 정확히 일치하는 행의 인덱스 찾기
        row_indices = np.where(kline_data_interval[:, col_idx] == threshold)[0]
        # 조건을 만족하는 첫 번째 인덱스를 반환하거나, 없으면 None 반환
        return int(row_indices[0]) if row_indices.size > 0 else None

    # 캔들 길이를 분석한다.
    def __get_candle_length(self, kline_data_lv3: list):
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
        # 윗꼬리 길이, 아래꼬리 길이, 몸통길이, 전체 길이.
        return (upper_wick_length, lower_wick_length, body_length, total_length)

    # np.array 데이터에서 지정 index위치의 증감 현황과 포지션 상태를 반환한다.
    def __get_trade_score(
        self, kline_data_interval: np.ndarray, col_idx: int
    ) -> Tuple[int, int, int]:
        """'
        1. 기능 : 데이터 트렌드 분석하는 함수
        2. 매개변수 : kline_data_interval
            1) kline_data_interval : kilne_data
            2) col_idx : 확인하고자 하는 index

        3. 반환값 내용 상세 - (A, B, C)
            1) position >> {1:'LONG', 2:'SHORT', 0:None}
            2) position_count >> 상승 하락 연속성
            3) trend
                1 >> 점점 증가
                2 >> 점점 감소
            4) streack_count : 최고점 또는 최저점이 몇시간 전인지 체크
        """

        def count_increasing_streak(values, index):
            """
            재귀적으로 값이 증가하는 구간의 길이를 계산.
            """
            if index <= 0:  # 리스트 시작
                return 0
            if values[index] <= values[index - 1]:  # 증가 조건 깨짐
                return 0
            return 1 + count_increasing_streak(values, index - 1)

        def count_decreasing_streak(values, index):
            """
            재귀적으로 값이 감소하는 구간의 길이를 계산.
            """
            if index <= 0:  # 리스트 시작
                return 0
            if values[index] >= values[index - 1]:  # 감소 조건 깨짐
                return 0
            return 1 + count_decreasing_streak(values, index - 1)

        # 데이터가 3개 미만이면 분석 불가능
        column_values = kline_data_interval[:, col_idx]
        n = len(column_values)
        if n < 3:
            return 0, 0, 0, 0

        # 1. 포지션 결정
        last_value = column_values[-1]
        second_last_value = column_values[-2]

        if last_value > second_last_value:
            increasing_streak = count_increasing_streak(
                column_values, len(column_values) - 1
            )
            decreasing_streak = 0
        elif last_value < second_last_value:
            decreasing_streak = count_decreasing_streak(
                column_values, len(column_values) - 1
            )
            increasing_streak = 0
        else:
            increasing_streak = 0
            decreasing_streak = 0

        if increasing_streak > decreasing_streak:
            position = 1  # Long
            position_count = increasing_streak
            relevant_values = (
                column_values[-increasing_streak - 1 :]
                if increasing_streak > 0
                else column_values[-1:]
            )
        else:
            position = 2  # Short
            position_count = decreasing_streak
            relevant_values = (
                column_values[-decreasing_streak - 1 :]
                if decreasing_streak > 0
                else column_values[-1:]
            )

        # 2. 변화 계산
        differences = []
        for i in range(len(relevant_values) - 1):
            diff = abs(relevant_values[i] - relevant_values[i + 1])
            differences.append(diff)

        # 차이값 역순 처리
        differences = differences[::-1]

        # 증가 및 감소 구간 계산
        decreasing_streak_diff = count_decreasing_streak(
            differences, len(differences) - 1
        )
        increasing_streak_diff = count_increasing_streak(
            differences, len(differences) - 1
        )

        # None 처리 (불필요하지만 안전하게)
        decreasing_streak_diff = decreasing_streak_diff or 0
        increasing_streak_diff = increasing_streak_diff or 0

        # 상황 결정
        if decreasing_streak_diff < increasing_streak_diff:
            trend = 1
            streak_count = increasing_streak_diff + 1
        elif decreasing_streak_diff > increasing_streak_diff:
            trend = 2
            streak_count = decreasing_streak_diff + 1
        else:
            trend = 0
            streak_count = 0

        return (position, position_count, trend, streak_count)

    def scenario_1(
        self,
        # symbol: str,
        kline_data_5m,
        kline_data_1h,
        # convert_data: Dict[str, Dict[str, NDArray[np.float64]]] = None,
    ):
        """'
        1. 5분봉 close 가격 연속 3회 상승 or 하락
        2. 5분봉 상승금액 연속 3회 이상 상승 or 하락
        3. 5분봉 거래대금 연속 3회 이상 상승 or 하락
        4. [:-1]hour max or min값 초과시
        5. candle 꼬리 합 비율 40% 미만시
        """
        # if convert_data is None:
        #     convert_data = self.kline_data
        target_interval = ["1m", "5m", "1h"]
        # for interval in target_interval:
        #     if not interval in self.intervals:
        #         raise ValueError(f"kline 데이터에 {interval}데이터가 없음.")

        # kline data를 interval별로 변수 지정
        # kline_data_5m = convert_data.get(symbol).get(target_interval[1])
        # kline_data_1h = convert_data.get(symbol).get(target_interval[2])
        # kline_data_1m = convert_data.get(symbol).get(target_interval[0])

        # 종가 연속성 및 포지션 체크
        price_bool, count, price_case, close_price_score = self.__get_trade_score(
            col_idx=4, kline_data_interval=kline_data_5m
        )
        # 거래대금 연속성 및 포지션 체크
        value_bool, count, value_case_, value_score = self.__get_trade_score(
            col_idx=10, kline_data_interval=kline_data_5m
        )

        # mode 초기값 None으로 처리하여 연속성 데이터 검토시 (0, 0)결과에 대비한다.
        mode = None

        # #positiosn 반전
        # if price_bool == 1:
        #     position_signal = 2
        # elif price_bool == 2:
        #     position_signal = 1
        # else:
        #     position_signal = 0

        position_signal = price_bool
        if price_bool == 1 and value_bool == 1:
            # interval 동안 high값 찾기위함.
            mode = "max"
        elif price_bool == 2 and value_bool == 1:
            # interval 동안 low값 찾기위함.
            mode = "min"
        # 결과값이 long or short이 아닐경우 time_diff값, position_signal을 0으로 처리한다.
        else:
            position_signal = 0
            time_diff = 0

        # 백테스트용으로 사용시 별도 세팅값 적용

        time_ago_minute = -60
        time_ago_hour = -1

        # # 초기 데이터의 길이가 60이 넘지 않을경우 time_ago_minute 반영시 error발생. 이를 방지하기 위함.
        # if self.back_test and len(kline_data_1m) >= abs(
        #     time_ago_minute + time_ago_hour
        # ):
        #     """
        #     real time data의 1h값 데이터는 1m과 길이가 같으므로 동일하게 -1 적용시 1분 전 데이터 반영됨.
        #     그러므로 60분 전 데이터를 적용
        #     """
        #     target_end_idx = time_ago_minute
        # else:
        #     target_end_idx = time_ago_hour

        # mode None이 아닐경우 계산을 시작한다.
        if mode:
            extreme_price = self.__get_column_extreme(
                mode=mode, data=kline_data_1h[:time_ago_hour], col_idx=4
            )
            time_diff = self.__get_index_by_value(
                kline_data_interval=kline_data_1h[:time_ago_hour],
                threshold=extreme_price,
                col_idx=4,
            )

        # 꼬리값 계산
        result_bool = []
        for data in reversed(kline_data_5m[:3]):
            upper, lower, body, total = self.__get_candle_length(data)

            if total == 0:
                result_bool.append(False)
                continue

            target_ratio = 0.4
            wick_ratio = (upper + lower) / total
            result_bool.append(wick_ratio <= target_ratio)

        wick_bool = all(result_bool)
        scenario_code = 1
        return (
            scenario_code,
            position_signal,
            close_price_score,
            value_score,
            time_diff,
            wick_bool,
        )
