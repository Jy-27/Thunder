import os
import utils
import Analysis
import time
import numpy as np
import asyncio
from numpy.typing import NDArray
from TradingDataManager import SpotDataControl, FuturesDataControl
from typing import Dict, List, Union, Any, Optional, Tuple
import utils
import datetime

"""
1. 목적
    >>> 대입결과 최상의 이익조건을 찾고 실제 SystemTrading에 반영한다.
    >>> Binanace kline Data를 활용하여 각종 시나리오를 대입해본다.
    
2. 기능
    CLASS
        1) DataManager : 과거 데이터를 수신하고 실제 SystemTrading시 적용할 Data와 동일하게 생성한다.
            >>> 특정기간동안 데이터 수신
            >>> 수신 데이터를 1개의 dict파일로 구성
            >>> interval별 매칭 index 데이터 생성
            >>> 1분봉 기준 실시간 데이터 생성
            
        2) TradeSignalManager : 주문(매수 또는 매도) 신호를 발생하고 해당 내용을 기록 누적 저장한다.
            >>> Marging 세팅
            >>> Leverage 세팅
            >>> 
            
            
        3) TradeStopperManager : 매도 또는 Stoploss구간을 계산한다. TradeSignal과 별개로 동작하게 한다.
            >>> 시나리오 1. entryPrice <-> highPrice간 비율 유지 
            >>> 시나리오 2. closePrice 지정 (수익률 지정, 도달시 매도)
            >>> 시나리오 3. 보유기간 지정 (특정기간 보유 후 자동 매매)
            >>> 시나리오 4. Spot / Futures Market 괴리율 검토.
            >>> 시나리오 5. 
            
        4) ClientManager : 주문 설정관련된 정보를 관리하다.
            >>> 주문가능 수량 계산
            
            
        4) WalletManager : 가상의 지갑정보를 생성한다. 주문(매수 또는 매도)에 따른 계좌정보를 update한다.
            >>> 기초 데이터 설정
            >>> 거래 발생시 출금처리
            >>> 거래 발생시 입금처리
            >>> 현재가 기준 계좌 가치 update
            
        
        5) SpecialMethodManager : __메소드를 관리하는 class이며 간단한 유틸리티 함수도 포함한다.



        6) 폐기함수.
        
3. 코드 구성 방향
    parameter는 다 받는다. 기본값을 None으로 하고 None입력시 내부에 저징된 변수값을 대입할 수 있도록 조치하낟.
    동기식으로 생성한다.

    저장은 별도의 함수를 구성해라. 한가지 함수에 너무 많은 기능을 담지마라.
"""


class DataManager:
    FUTURES = "FUTURES"
    SPOT = "SPOT"

    def __init__(
        self,
        symbols: Union[str, List],
        intervals: Union[list[str], str],
        start_date: str,
        end_date: str,
    ):
        # str타입을 list타입으로 변형한다.
        self.symbols = [symbols] if isinstance(symbols, str) else symbols
        self.intervals = [intervals] if isinstance(intervals, str) else intervals

        # KlineData 다운로드할 기간. str(YY-MM-DD HH:mm:dd)
        self.start_date: str = start_date
        self.end_date: str = end_date

        # kline data수집을 위한 instance
        self.ins_spot = SpotDataControl()
        self.ins_futures = FuturesDataControl()

        self.real_data_file = "real_time_data.json"
        self.indices_file = "real_time_data.npy"
        self.kline_data_file = "kline_data.json"

    # 현물시장의 symbol별 입력된 interval값 전체를 수신 및 반환한다.
    async def get_spot_kilne_data(
        self,
        symbol: str,
        intervals: Union[List[str], str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, List]:
        """
        1. 기능 : symbol별 입력된 interval값 전체를 수신 및 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) start_date : '2024-01-01 00:00:00'
            3) end_date : '2024-01-02 00:00:00'
            4) save_directory_path : 저장할 파일 위치 (파일명 or 전체 경로)
            5) intervals : 수신하고자 하는 데이터의 interval 구간
        """

        # 매개변수 타입 통일 위하여 대문자로 변경함.
        symbol = symbol.upper()
        if isinstance(intervals, str):
            # interval값을 대문자로 적용시 1분봉 '1m'과 1개월봉 '1M'이 겹쳐버린다. 주의.
            intervals = [intervals]

        # 현재 매개변수 입력값이 None일경우 속성값으로 대체 (별도 계산필요시 적용 위함.)
        target_start_date: str = start_date or self.start_date
        target_end_date = end_date or self.end_date

        conv_start_date = utils._convert_to_datetime(target_start_date)
        conv_end_date = utils._convert_to_datetime(target_end_date)
        historical_data = {}

        for interval in intervals:
            historical_data[
                interval
            ] = await SpotDataControl().get_historical_kline_hour_min(
                symbol=symbol,
                interval=interval,
                start_date=conv_start_date,
                end_date=conv_end_date,
            )

        return historical_data

    # 선물시장의 symbol별 입력된 interval값 전체를 수신 및 반환한다.
    async def get_futures_kilne_data(
        self,
        symbols: Optional[str] = None,
        intervals: Optional[Union[List[str], str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, List]:
        """
        1. 기능 : symbol별 입력된 interval값 전체를 수신 및 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) start_date : '2024-01-01 00:00:00'
            3) end_date : '2024-01-02 00:00:00'
            4) save_directory_path : 저장할 파일 위치 (파일명 or 전체 경로)
            5) intervals : 수신하고자 하는 데이터의 interval 구간
        """

        # 현재 매개변수 입력값이 None일경우 속성값으로 대체 (별도 계산필요시 적용 위함.)
        target_symbols = symbols or self.symbols
        # symbol을 대문자로 통일
        target_symbols = [symbol.upper() for symbol in symbols]
        target_start_date = start_date or self.start_date
        target_end_date = end_date or self.end_date
        target_interval = intervals or self.intervals

        if isinstance(target_interval, str):
            # interval값을 대문자로 적용시 1분봉 '1m'과 1개월봉 '1M'이 겹쳐버린다. 주의.
            target_interval = [target_interval]

        conv_start_date = utils._convert_to_datetime(target_start_date)
        conv_end_date = utils._convert_to_datetime(target_end_date)
        historical_data: Dict = {}
        for symbol in target_symbols:
            historical_data[symbol] = {}
            for interval in target_interval:
                historical_data[symbol][
                    interval
                ] = await FuturesDataControl().get_historical_kline_hour_min(
                    symbol=symbol,
                    interval=interval,
                    start_date=conv_start_date,
                    end_date=conv_end_date,
                )

        return historical_data

    # kline의 과거 데이터를 활용하여 interval로 구분가능한 1분 단위 또는 지정 단위 기준으로 실시간 데이터 생성
    def generate_real_time_kline_data(
        self,
        indices_data: List[List[int]],
        kline_data: Dict[str, Dict[str, NDArray[np.float64]]],
    ):
        """
        1. 기능 : 수신된 각 symbol별, interval별 수신된 데이터를 1분봉 데이터 기준으로 리얼 데이터를 생성한다.
        2. 매개변수
            1) indices_data : 각 interval간 연결된 index 데이터
            2) kline_data : self.merge_json_files 반영한 데이터

        3. 매개변수 준비 순서
            1) kline_data : data_sync() 함수 생성
            2) index_data : data_index.py
        4. 리얼데이터 생성기로 백테스트 연산시 본 함수의 결과물을 대입할 것.
        """

        # 실시간 반영할 interval값. 일반적으로 1분봉 추천
        target_interval = self.intervals[0]
        # 데이터 생성 후 반환할 초기 데이터
        processed_data: Dict = {}

        # Dict 최상위 중첩 데이터 조회
        for symbol, kline_data_symbol in kline_data.items():
            # symbol key 생성
            processed_data[symbol] = {}

            # >>> Target interval data 조회 <<<
            target_interval_data = kline_data_symbol.get(target_interval)

            for interval, kline_data_interval in kline_data_symbol.items():
                processed_data[symbol][interval] = []

                # Target interval에 해당하는 데이터 복사
                if interval == target_interval:
                    processed_data[symbol][interval] = np.array(
                        object=kline_data_interval, dtype=float
                    )
                    continue

                # target data가 None인 경우 처리 (예: 빈 리스트로 대체)
                if target_interval_data is None:
                    raise ValueError(f"target interval 데이터가 비어있음.")

                # tarket data를 순차적으로 조회
                for idx, current_data in enumerate(target_interval_data):
                    # 인덱스 매핑
                    idx_map: Dict[str, int] = self.__map_intervals_to_indices(
                        index_values=indices_data[idx]
                    )

                    # Interval Kline에서 open/close 값 조회
                    mapped_idx = idx_map.get(interval)
                    if mapped_idx is None:
                        continue  # 유효하지 않은 인덱스는 건너뛰기

                    open_timestamp = kline_data_interval[mapped_idx][0]
                    close_timestamp = kline_data_interval[mapped_idx][6]

                    # 새로운 Kline 데이터 구성
                    new_kline = [
                        open_timestamp,  # Open Time
                        float(current_data[1]),  # Open
                        float(current_data[2]),  # High
                        float(current_data[3]),  # Low
                        float(current_data[4]),  # Close
                        float(current_data[5]),  # Volume
                        close_timestamp,  # Close Time
                        float(current_data[7]),  # Quote Asset Volume
                        float(current_data[8]),  # Number of Trades
                        float(current_data[9]),  # Taker Buy Base Asset Volume
                        float(current_data[10]),  # Taker Buy Quote Asset Volume
                        float(current_data[11]),  # Ignore
                    ]

                    # 데이터 추가 처리
                    if idx == 0:
                        processed_data[symbol][interval].append(new_kline)
                    else:
                        previous_kline = processed_data[symbol][interval][-1]
                        prev_open_timestamp = previous_kline[0]

                        # 이전 데이터를 업데이트하거나 새로운 데이터를 추가
                        if prev_open_timestamp == open_timestamp:
                            updated_kline = [
                                open_timestamp,  # Open Time
                                previous_kline[1],  # Open
                                max(previous_kline[2], float(current_data[2])),  # High
                                min(previous_kline[3], float(current_data[3])),  # Low
                                float(current_data[4]),  # Close
                                previous_kline[5] + float(current_data[5]),  # Volume
                                previous_kline[6],  # Close Time
                                previous_kline[7]
                                + float(current_data[7]),  # Quote Asset Volume
                                previous_kline[8]
                                + float(current_data[8]),  # Number of Trades
                                previous_kline[9]
                                + float(current_data[9]),  # Taker Buy Base Asset Volume
                                previous_kline[10]
                                + float(
                                    current_data[10]
                                ),  # Taker Buy Quote Asset Volume
                                0,  # Ignore
                            ]
                            processed_data[symbol][interval].append(
                                updated_kline
                            )  # 마지막 항목 업데이트
                        else:
                            processed_data[symbol][interval].append(new_kline)

                # 리스트를 NumPy 배열로 변환
                processed_data[symbol][interval] = np.array(
                    object=processed_data[symbol][interval], dtype=float
                )

        return processed_data

    # 연산이 용이하도록 interval값과 index값을 이용하여 매핑값을 반환한다.
    def __map_intervals_to_indices(self, index_values: List[int]) -> Dict[str, int]:
        """
        1. 기능 : interval과 index데이터를 연산이 용이하도록 매핑한다.
        2. 매개변수
            1) index_values : 각 구간별 index 정보
        """
        mapped_intervals = {}
        for i, interval in enumerate(self.intervals):
            mapped_intervals[interval] = index_values[i]

        return mapped_intervals

    # dict 타입 데이터의 key값을 불러온다.
    def __extract_intervals(self, kline_data: Dict) -> List[str]:
        """
        1. 기능 : dict 데이터의 최상위 key값을 추출하여 list타입으로 변환 및 반환한다.
        2. 매개변수 : dict데이터
        """
        return list(kline_data.keys())

    # timestemp값을 반환한다.
    def __extract_timestamps(self, nested_kline: Union[List, np.ndarray]):
        """
        1. 기능 : kline데이터의 최하위 중첩 내용의 timestamp를 반환한다.
        2. 매개변수
            1) nested_kline : kline 최하위 중첩데이터
        """
        open_timestamp = nested_kline[0]
        close_timestamp = nested_kline[6]
        return (open_timestamp, close_timestamp)

    # 최상위 key값을 제거하고 중첩된 dict값을 반환한다.
    def __convert_dict_to_array(self, kline_data: Dict) -> Dict[str, np.ndarray]:
        """
        1. 기능 : dict의 1차 중첩 내용을 반환한다.
        2. 매개변수
            1) kline_data : 원본 kline data
        """
        result = {}
        for _, data in kline_data.items():
            for interval, nested_data in data.items():
                result[interval] = np.array(nested_data, dtype=float)
        return result

    # 각 interval구간 데이터의 연결되는 data index값을 연산 및 반환한다. (최종 결과물 / 저장은 별도로)
    def get_matching_indices(self, kline_data: Dict) -> List[List[int]]:
        """
        1. 기능 : 각 interval구간 데이터의 연결되는 data index값을 연산 및 반환한다.
        2. 매개변수
            1) kline_data : 원본 kline data 또는 self.get_futures_kilne_data() 함수값
        """
        array_data = self.__convert_dict_to_array(kline_data=kline_data)
        intervals = self.__extract_intervals(array_data)
        matching_indices = []

        for index, base_entry in enumerate(array_data[intervals[0]]):
            match_row = [index]
            open_time, close_time = self.__extract_timestamps(base_entry)

            for interval in intervals[1:]:
                interval_data = array_data.get(interval)
                if interval_data is None:
                    # match_row.append(None)
                    continue

                # 조건을 만족하는 인덱스 찾기
                condition_indices = np.where(
                    (interval_data[:, 0] <= open_time)
                    & (interval_data[:, 6] >= close_time)
                )[0]

                if condition_indices.size == 0:
                    # match_row.append(None)
                    continue
                else:
                    match_row.append(int(condition_indices[0]))

            # if None in match_row:
            #     continue
            matching_indices.append(match_row)
            # utils._std_print(match_row)

        return matching_indices

    # 더미 데이터를 순환시킬때 for문의 range값을 계산한다.
    def get_range_length(self, kline_data_real: Dict) -> int:
        """
        1. 기능 : 더미 데이터를 for 문에 동작할때 range값을 계산한다.
        2. 매개변수
            1) kline_data
        """
        unique_lengths = set()

        for _, kline_data_symbol in kline_data_real.items():
            for _, kline_data_interval in kline_data_symbol.items():
                unique_lengths.add(len(kline_data_interval) - 1)
                # 길이가 두 개 이상이면 에러 발생
                if len(unique_lengths) > 1:
                    raise ValueError(
                        f"Interval 데이터 길이가 일치하지 않습니다: {unique_lengths}"
                    )

        # 길이가 하나뿐이라면, 값을 반환
        return unique_lengths.pop()

    # 기간별 각 interval값을 raw데이터와 동일한 형태로 반환한다.
    def get_kline_data_by_range(
        self,
        end_index: int,
        kline_data: Dict,
        idx_data: List[List[int]],
        step: int = 4_320,
    ) -> Dict[str, Dict[str, NDArray[np.float64]]]:
        """
        1. 기능 : 기간별 데이터를 추출한다.
        2. 매개변수
            1) start_index : index 0 ~ x까지 값을 입력
            2) step : 데이터 기간(min : 4320
                - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
        """
        result: Dict[str, Dict[str, NDArray[np.float64]]] = {}

        for symbol, kline_data_symbol in kline_data.items():
            result[symbol] = {}
            for interval, kline_data_interval in kline_data_symbol.items():
                # intervals 리스트에 없는 interval은 제외한다.
                if not interval in self.intervals:
                    continue
                start_index = end_index - step
                if start_index < 0:
                    start_index = 0
                start_indices = idx_data[start_index]
                end_indices = idx_data[end_index]

                start_mapped_intervals = self.__map_intervals_to_indices(
                    index_values=start_indices
                )
                end_mapped_intervals = self.__map_intervals_to_indices(
                    index_values=end_indices
                )

                start_index_value = start_mapped_intervals.get(interval)
                end_index_value = end_mapped_intervals.get(interval)

                sliced_data = kline_data_interval[start_index_value:end_index_value]
                result[symbol][interval] = sliced_data
        return result

    # kline real_data 확보 관련 통합실행
    async def download_data_run(
        self, directory: Optional[str] = None
    ) -> Tuple[int, Dict]:
        """
        1. 기능 : 위 함수를 사용하기 복잡하기에 통합 다운로드 기능을 제공함.
        2. 매개변수
            1) directory : 각 파일 저장할 메인 폴더명 (파일명은 별도로 자동 지정됨.)
        """
        # directory가 None일 경우 현재폴더 위치로 지정
        target_directory = directory or os.getcwd()

        # Data 순차적 로드
        kline_data = await self.get_futures_kilne_data(symbols=self.symbols)
        indices_data = self.get_matching_indices(kline_data=kline_data)
        real_time_data = self.generate_real_time_kline_data(
            indices_data=indices_data, kline_data=kline_data
        )

        # real_time_data를 이용하여 데이터 길이 값 연산
        range_length_data = self.get_range_length(kline_data_real=real_time_data)

        # 각 데이터들 저장할 path 지정
        kline_path = os.path.join(target_directory, self.kline_data_file)
        indices_path = os.path.join(target_directory, self.indices_file)
        real_time_path = os.path.join(target_directory, self.real_data_file)

        # Data 저장
        utils._save_to_json(file_path=kline_path, new_data=kline_data, overwrite=True)
        utils._save_to_json(
            file_path=indices_path, new_data=indices_data, overwrite=True
        )
        # utils._save_to_json(file_path=real_time_path, new_data=real_time_data, overwrite=True)
        # real_time_path는 np.array타입이므로 별도 저장.
        np.save(real_time_path, real_time_data)

        # Tuple 형태로 자료 반환.
        return (range_length_data, real_time_data)


class WasteTypeCode:
    ...
    """
    폐기 코드 집합소 / 전부 주석처리한다.
    """
