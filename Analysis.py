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
    def __init__(self, back_test: bool = False):  # , symbols: list):
        self.back_test = back_test
        self.symbols = []
        self.kline_data = {}
        self.intervals = []
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
            return 0, 0, 0

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
        symbol: str,
        convert_data: Dict[str, Dict[str, NDArray[np.float64]]] = None,
    ):
        """'
        1. 5분봉 close 가격 연속 3회 상승 or 하락
        2. 5분봉 상승금액 연속 3회 이상 상승 or 하락
        3. 5분봉 거래대금 연속 3회 이상 상승 or 하락
        4. [:-1]hour max or min값 초과시
        5. candle 꼬리 합 비율 40% 미만시
        """
        if convert_data is None:
            convert_data = self.kline_data
        target_interval = ["1m", "5m", "1h"]
        for interval in target_interval:
            if not interval in self.intervals:
                raise ValueError(f"kline 데이터에 {interval}데이터가 없음.")

        # kline data를 interval별로 변수 지정
        kline_data_5m = convert_data.get(symbol).get(target_interval[1])
        kline_data_1h = convert_data.get(symbol).get(target_interval[2])
        kline_data_1m = convert_data.get(symbol).get(target_interval[0])

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
