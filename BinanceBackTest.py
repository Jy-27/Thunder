import os
import utils
import Analysis
import time
import numpy as np
import pickle
import asyncio
import DataProcess
from numpy.typing import NDArray
from TradingDataManager import SpotTrade, FuturesTrade
from typing import Dict, List, Union, Any, Optional, Tuple
import utils
import datetime
from BinanceTradeClient import FuturesOrder, SpotOrder

"""
1. 목적
    >>> 대입결과 최상의 이익조건을 찾고 실제 SystemTrading에 반영한다.
    >>> Binanace kline Data를 활용하여 각종 시나리오를 대입해본다.
    
2. 기능
    CLASS
        1) DataManager : 과거 데이터를 수신하고 실제 SystemTrading시 적용할 Data와 동일하게 생성한다.
            >>> 특정기간동안 데이터 수신
            >>> 수신 데이터를 1개의 dict파일로 구성
            >>> interval별 매칭 idx 데이터 생성
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
        self.ins_spot = SpotTrade()
        self.ins_futures = FuturesTrade()

        self.storeage = "DataStore"
        self.kline_closing_sync_data = "closing_sync_data.pkl"
        self.indices_file = "indices_data.json"
        self.kline_data_file = "kline_data.json"

    # 시장의 interval 값 전체를 수신하여 websocket 편집 데이터와 동일한 형태로 반환한다. (오리지날 데이터)
    async def generate_kline_interval_data(
        self,
        symbols: Optional[Union[str, list]] = None,
        intervals: Optional[Union[List[str], str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Dict[str, List[List[Union[str, int]]]]]:
        """
        1. 기능 : 시장의 interval 값 전체를 수신하여 websocket 편집 데이터와 동일한 형태로 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) start_date : '2024-01-01 00:00:00'
            3) end_date : '2024-01-02 00:59:59'  << 59로 끝낼것. 아니면 Error
            4) save_directory_path : 저장할 파일 위치 (파일명 or 전체 경로)
            5) intervals : 수신하고자 하는 데이터의 interval 구간
        """

        # target_symbols 타입힌트 오류 방지용
        symbols = symbols or []
        if isinstance(symbols, str):
            symbols = [symbols]

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
                ] = await FuturesTrade().get_historical_kline_hour_min(
                    symbol=symbol,
                    interval=interval,
                    start_date=conv_start_date,
                    end_date=conv_end_date,
                )

        return historical_data

    # 1분봉 데이터를 기반으로, 가장 마지막 값을 누적 계산하여 다른 interval 데이터들을 생성하고, 이를 1분봉과 동일한 길이로 맞춘다
    def generate_kline_closing_sync(
        self,
        indices_data: List[List[int]],
        kline_data: Dict[str, Dict[str, List[Union[Any]]]],
    ):
        """
        1. 기능 : 1분봉 데이터를 기반으로, 가장 마지막 값을 누적 계산하여 다른 interval 데이터들을 생성하고, 이를 1분봉과 동일한 길이로 맞춘다
        2. 매개변수
            1) indices_data : get_matching_indices() 함수 데이터
            2) kline_data : generate_kline_interval_data() 함수 데이터
        3. 리얼데이터 생성기로 백테스트 연산시 본 함수의 결과물을 대입할 것.
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
                        object=kline_data_interval, dtype=np.float64
                    )
                    continue

                # target data가 None인 경우 처리 (예: 빈 리스트로 대체)
                if target_interval_data is None:
                    raise ValueError(f"target interval 데이터가 비어있음.")

                # tarket data를 순차적으로 조회
                for idx, current_data in enumerate(target_interval_data):
                    # 인덱스 매핑
                    idx_map: Dict[str, int] = self.__map_intervals_to_indices(
                        idx_values=indices_data[idx]
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
                    object=processed_data[symbol][interval], dtype=np.float64
                )

        return processed_data

    # kline_data의 특정 interval idx를 closing_sync_data 값으로 동기화 시킨다. 백테스트에 사용될 데이터에 적용됨
    def sync_kline_data(self, idx: int, kline_data: dict, idx_mapping: list, sync_data: dict) -> Dict[str, Dict[str, np.ndarray[np.float64]]]:
        """
        1. 기능 : 백테스트에 적용시킬 kline_data의 특정 interval idx데이터를 closing_sync_data값으로 동기화 시킨다.
        2. 매개변수
            1) idx : 적용시킬 Index 값
            2) kline_data : read_data_run함수의 [1] 반환값. >> kline_data
            3) idx_mapping : read_data_run함수의 [2] 반환값. >> indices_data
            4) sync_data : read_data_run 함수의 [3] 반환값. >> closing_sync_data
        
        동작은 문제 없으나 너무 느림. 개선이 필요함.
        """
        idx_map_data = self.__map_intervals_to_indices(idx_values=idx_mapping[idx])
        for symbol, kline_data_symbol in kline_data.items():
            for interval, kline_data_interval in kline_data_symbol.items():
                idx_map = idx_map_data.get(interval)
                
                kline_data[symbol][interval][idx_map] = sync_data[symbol][interval][idx]
        return kline_data

    # 각 interval별 1minute 단위로 환산한다.
    def __convert_interval_to_minutes(self, minute:int, interval:str):
        """
        1. 기능 : 1muntes값을 각 interval별 값으로 환산한다.
        2. 매개변수
            1) minute : 타겟 시간 (분)
            2) interval : 환산하고자 하는 interval 값        
        """
        result = {'1m': 1,
                  '3m': 3,
                  '5m':5,
                  '15m':15,
                  '30m':30,
                  '1h':60,
                  '2h':120,
                  '4h':240,
                  '6h':360,
                  '8h':480,
                  '12h':720,
                  '1d':1440,
                  '3d':4320}
        if not minute in result.keys():
            raise ValueError(f'interval이 유효하지 않음 - {interval}')
        return result.get(interval) / minute


    # 연산이 용이하도록 interval값과 idx값을 이용하여 매핑값을 반환한다.
    def __map_intervals_to_indices(self, idx_values: List[int]) -> Dict[str, int]:
        """
        1. 기능 : interval과 idx데이터를 연산이 용이하도록 매핑한다.
        2. 매개변수
            1) idx_values : 각 구간별 idx 정보
        """
        mapped_intervals = {}
        for i, interval in enumerate(self.intervals):
            mapped_intervals[interval] = idx_values[i]
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
                result[interval] = np.array(nested_data, dtype=np.float64)
        return result

    # kline_data의 최하위 중첩 데이터를 np.array처리한다.
    def convert_kline_data_array(self, kline_data: Dict) -> Dict[str, Dict[str, np.ndarray]]:
        result = {}
        for symbol, kline_data_symbol in kline_data.items():
            if not isinstance(kline_data_symbol, dict) or not kline_data_symbol:
                raise ValueError('kline data가 유효하지 않음.')
            result[symbol] = {}
            for interval, kline_data_interval in kline_data_symbol.items():
                if not isinstance(kline_data_interval, Union[List, np.ndarray]) or not kline_data_interval:
                    raise ValueError('kline data가 유효하지 않음.')
                result[symbol][interval] = np.array(object=kline_data_interval, dtype=np.float64)
        return result                
                

    # 각 interval구간 데이터의 연결되는 data idx값을 연산 및 반환한다. (최종 결과물 / 저장은 별도로)
    def get_matching_indices(self, kline_data: Dict) -> List[List[int]]:
        """
        1. 기능 : 각 interval구간 데이터의 연결되는 data idx값을 연산 및 반환한다.
        2. 매개변수
            1) kline_data : 원본 kline data 또는 self.generate_kline_interval_data() 함수값
        """
        array_data = self.__convert_dict_to_array(kline_data=kline_data)
        intervals = self.__extract_intervals(array_data)
        matching_indices = []

        for idx, base_entry in enumerate(array_data[intervals[0]]):
            match_row = [idx]
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
                        f"Interval 데이터 길이가 일치하지 않음. 기초 데이터 삭제 요망 : {unique_lengths}"
                    )

        # 길이가 하나뿐이라면, 값을 반환
        return unique_lengths.pop()

    # 데이터를 start_idx:end
    def get_kline_closing_data_by_range(
        self, end_idx: int, kline_data: Dict, step: int = 4_320
    ):

        result: Dict[str, Dict[str, NDArray[np.float64]]] = {}
        for symbol, kline_data_symbol in kline_data.items():
            result[symbol] = {}
            for interval, kline_data_interval in kline_data_symbol.items():
                start_idx = end_idx - step
                if start_idx < 0:
                    start_idx = 0
                result[symbol][interval] = kline_data_interval[start_idx:end_idx]
        return result

    # # 
    # def get_kline_interval_data_by_range(
    #     self,
    #     end_idx: int,
    #     kline_data: Dict,
    #     idx_data: List[List[int]],
    #     step: int = 4_320,
    # ) -> Dict[str, Dict[str, NDArray[np.float64]]]:
    #     """
    #     1. 기능 : 기간별 데이터를 추출한다.
    #     2. 매개변수
    #         1) start_idx : idx 0 ~ x까지 값을 입력
    #         2) step : 데이터 기간(min : 4320
    #             - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
    #         3) idx_data : self.get_matching_indices() 연산값.
    #         4) step : 시작과 끝점간의 범위 (단위 : minutes)
    #     3.Memo
    #         >>> closing_sync_data를 대상으로 하는게 아님.
    #         >>> 각 interval간 open_timestamp, close_timestamp간 매칭되는 부분을 추출
    #         >>> 주의 : 이후 interval 값은 이전 interval값의 최종 값이 이미 반영됐으므로 상호 실시간 변동사항 반영이 안됨.
    #                 예) 1분봉 idx 1 ~ 5 값 범위가 존재해도 5분봉은 이미 1분봉 idx 5번값 까지 최종 반영이 완료된 상태임.
    #                 1분봉 idx별 더 큰 묶음 interval값 실시간 반영 필요시 get_ral_time_kline_data_by_range()함수 사용할 것.
    #     """
    #     result: Dict[str, Dict[str, NDArray[np.float64]]] = {}

    #     idx_map: Dict[str, int] = self.__map_intervals_to_indices(
    #                     idx_values=idx_data[end_idx]
    #                 )
        

    #     for symbol, kline_data_symbol in kline_data.items():
    #         result[symbol] = {}
    #         for interval, kline_data_interval in kline_data_symbol.items():
    #             idx_convert_map: Dict[str, int] =self.__convert_interval_to_minutes(minute=step, interval=interval)
    #             # intervals 리스트에 없는 interval은 제외한다.
    #             if not interval in self.intervals:
    #                 continue
    #             if interval == self.intervals[0]:
    #                 start_idx = end_idx - step
    #             else:
    #                 start_idx = end_idx - (step/idx_convert_map)
                
    #             if start_idx < 0:
    #                 start_idx = 0

    #             result[symbol][interval] = kline_data_interval[start_idx:end_idx]

    #     return result

    def get_kline_interval_data_by_range(
        self,
        end_idx: int,
        kline_data: Dict[str, Dict[str, NDArray[np.float64]]],
        idx_data: List[List[int]],
        step: int = 4320,
    ) -> Dict[str, Dict[str, NDArray[np.float64]]]:
        """
        개선된 버전: 비효율적인 반복문과 조건문 최적화
        """
        result: Dict[str, Dict[str, NDArray[np.float64]]] = {}

        # intervals를 집합으로 변환
        interval_set = set(self.intervals)

        # 사전 계산된 매핑 캐싱
        idx_map: Dict[str, int] = self.__map_intervals_to_indices(idx_values=idx_data[end_idx])
        idx_convert_map: Dict[str, int] = {
            interval: self.__convert_interval_to_minutes(minute=step, interval=interval)
            for interval in self.intervals
        }

        for symbol, kline_data_symbol in kline_data.items():
            result[symbol] = {}

            # start_idx를 미리 계산하여 캐싱
            start_idx_map = {}
            for interval in self.intervals:
                if interval == self.intervals[0]:
                    start_idx_map[interval] = max(0, end_idx - step)
                else:
                    start_idx_map[interval] = max(0, end_idx - int(step / idx_convert_map.get(interval, 1)))

            # 데이터를 처리
            for interval, kline_data_interval in kline_data_symbol.items():
                if interval not in interval_set:
                    continue

                start_idx = start_idx_map[interval]
                result[symbol][interval] = kline_data_interval[start_idx:end_idx]

        return result



    # kline real_data 확보 관련 통합실행
    async def download_data_run(
        self, directory: Optional[str] = None
    ) -> Tuple[int, Dict]:
        """
        1. 기능 : 위 함수를 사용하기 복잡하기에 통합 다운로드 기능을 제공함.
        2. 매개변수
            1) directory : 각 파일 저장할 메인 폴더명 (파일명은 별도로 자동 지정됨.)
        3. 반환값
            1) range_length_data : for _ in range(range_length_data)에 들어감.
            2) kline_data : 각 interval별 데이터를 수집 및 dict형태로 반환
            3) indices_data : kline_data 1분봉 기준으로 매칭되는 다른 interval data index
            4) closing_sync_data : 1분봉 기준 각 interval별 closing data
        """
        # directory가 None일 경우 상위폴더 위치로 지정
        target_directory = os.path.join(
            directory or os.path.dirname(os.getcwd()), self.storeage
        )

        if not os.path.exists(target_directory):
            os.makedirs(target_directory)

        # Data 순차적 로드
        kline_data = await self.generate_kline_interval_data(symbols=self.symbols)
        indices_data = self.get_matching_indices(kline_data=kline_data)
        closing_sync_data = self.generate_kline_closing_sync(
            indices_data=indices_data, kline_data=kline_data
        )

        # closing_sync_data를 이용하여 데이터 길이 값 연산
        range_length_data = self.get_range_length(kline_data_real=closing_sync_data)

        # 각 데이터들 저장할 path 지정
        kline_path = os.path.join(target_directory, self.kline_data_file)
        indices_path = os.path.join(target_directory, self.indices_file)
        closing_sync_data_path = os.path.join(target_directory, self.kline_closing_sync_data)

        # Data 저장
        utils._save_to_json(file_path=kline_path, new_data=kline_data, overwrite=True)
        utils._save_to_json(
            file_path=indices_path, new_data=indices_data, overwrite=True
        )
        # utils._save_to_json(file_path=closing_sync_data_path, new_data=closing_sync_data_file, overwrite=True)
        # closing_sync_data_path는 np.array타입이므로 별도 저장.

        with open(closing_sync_data_path, "wb") as file:
            pickle.dump(closing_sync_data, file)

        # Tuple 형태로 자료 반환.
        return (range_length_data, kline_data, indices_data, closing_sync_data)

    # 기존에 작업 저장된 데이터를 불러오며, 선택적으로 데이터 없일시 신규 다운로드 기능 구현.
    async def read_data_run(self, download_if_missing: bool = False):
        """
        1. 기능 : 본 class의 기능을 사용하기 용이하도록 통합적용. 데이터를 불러오는 함수이며, 데이터가 미존재시 신규 다운로드 하는 기능 추가.
        2. 매개변수
            1) download_if_missing : True일 경우 파일없을시 신규 다운로드.
        """

        # 불러올 데이터의 초기부분 주소명 확보
        parent_folder = os.path.dirname(os.getcwd())
        # indices_path 주소 생성
        closing_sync_data_path = os.path.join(
            parent_folder, self.storeage, self.kline_closing_sync_data
        )
        kline_data_path = os.path.join(parent_folder, self.storeage, self.kline_data_file)
        indices_data_path = os.path.join(parent_folder, self.storeage, self.indices_file)
        

        if download_if_missing:
            if not os.path.exists(parent_folder):
                os.makedirs(parent_folder)
            # if not os.path.exists(closing_sync_data_path):
            return await self.download_data_run()
        else:
            if not os.path.exists(path=kline_data_path):
                raise ValueError(f"path 정보가 유효하지 않음 - {kline_data_path}")
            if not os.path.exists(path=indices_data_path):
                raise ValueError(f"path 정보가 유효하지 않음 - {indices_data_path}")
            if not os.path.exists(path=closing_sync_data_path):
                raise ValueError(f"path 정보가 유효하지 않음 - {closing_sync_data_path}")
            with open(closing_sync_data_path, "rb") as file:
                closing_sync_data = pickle.load(file)
            
            range_length_data = self.get_range_length(kline_data_real=closing_sync_data)
            kline_data = utils._load_json(file_path=kline_data_path)
            indices_data = utils._load_json(file_path=indices_data_path)
            

        return (range_length_data, kline_data, indices_data, closing_sync_data)


class OrderManager:

    def __init__(self):
        self.ins_futures_client = FuturesOrder()
        self.ins_spot_client = SpotOrder()
        self.ins_trade_stopper = DataProcess.TradeStopper()
        self.market_type = ["FUTURES", "SPOT"]
        self.MAX_LEVERAGE = 30
        self.MIN_LEVERAGE = 5

    # 가상의 주문(open)을 생성한다.
    async def generate_order_open_signal(
        self,
        symbol: str,
        position: int,
        leverage: int,
        balance: float,
        entry_price: float,
        open_timestamp: int,
        market_type: str = "futures",
        fee: float = 0.0005,
    ):
        """
        1. 기능 : 조건 신호 발생시 가상의 구매신호를 발생한다.
        2. 매개변수
        """
        market = market_type.upper()
        if market not in self.market_type:
            raise ValueError(f"market type 입력 오류 - {market}")

        if market == self.market_type[0]:
            ins_obj = self.ins_futures_client
        else:
            ins_obj = self.ins_spot_client

        # position stopper 초기값 설정
        # self.ins_trade_stopper(symbol=symbol, position=position, entry_price=entry_price)

        date = utils._convert_to_datetime(open_timestamp)

        # print(date)
        # leverage 값을 최소 5 ~ 최대 30까지 설정.
        target_leverage = min(max(leverage, self.MIN_LEVERAGE), self.MAX_LEVERAGE)

        # 현재가 기준 최소 주문 가능량 계산
        get_min_trade_qty = await ins_obj.get_min_trade_quantity(symbol=symbol)
        # 조건에 부합ㅎ는 최대 주문 가능량 계산
        get_max_trade_qty = await ins_obj.get_max_trade_quantity(
            symbol=symbol, leverage=target_leverage, balance=balance
        )

        margin = (get_max_trade_qty * entry_price) / target_leverage
        break_event_price = entry_price * (1 + fee)

        # position을 문자형으로 변환함. {0:None, 1:'long', 2':'short'}
        position_str = "LONG" if position == 1 else "SHORT"

        fail_message = {
            "symbol": symbol,
            "tradeTimestamp": open_timestamp,
            "tradeDate": date,
            "entryPrice": entry_price,
            "currentPrice": entry_price,
            "position": position_str,
            "quantity": get_max_trade_qty,
            "margin": margin,
            "breakEventPrice": break_event_price,
            "leverage": target_leverage,
            "liq.Price": None,
        }

        if get_max_trade_qty < get_min_trade_qty:
            fail_message["memo"] = "기본 주문 수량 > 최대 주문 수량"
            return (False, fail_message)

        if margin > balance:
            fail_message["memo"] = "마진 금액 > 주문 금액"
            return (False, fail_message)

        liq_price = self.__get_liquidation_price(
            entry_price=entry_price,
            leverage=target_leverage,
            quantity=get_max_trade_qty,
            margin_balance=margin,
            position_type=position_str,
        )

        result = {
            "symbol": symbol,
            "tradeTimestamp": open_timestamp,
            "tradeDate": date,
            "entryPrice": entry_price,
            "currentPrice": entry_price,
            "position": position_str,
            "quantity": get_max_trade_qty,
            "margin": margin,
            "breakEventPrice": break_event_price,
            "leverage": target_leverage,
            "liq.Price": liq_price,
            "memo": None,
        }
        return (True, result)

    # 가상의 주문(close)을 생성하고, 매각에 대한 가치(usdt)를 연산 및 반환한다.
    def generate_order_close_signal(
        self,
        symbol: str,
        current_price: float,
        wallet_data: Dict[str, Dict[str, Union[Any]]],
        fee: float = 0.0005,
    ) -> float:
        """
        1. 기능 : 가상의 매각 주문 접수에 따른 매각 시 총 가치를 계산
        2. 매개변수
            1) symbol (str): 거래 심볼 (예: BTCUSDT)
            2) current_price (float): 현재 가격
            3) wallet_data (Dict): 지갑 데이터, 각 심볼별 포지션 정보
            4) fee (float): 거래 수수료율 (기본값: 0.0005)
        3. Memo
            >> 별다른 신호를 발생하는 것이 아닌, 손익 관련 계산값만 반환함.
        """
        # 대상 심볼 데이터 가져오기
        target_data = wallet_data.get(symbol)
        if not isinstance(target_data, dict) or not target_data:
            raise ValueError(f"지갑 데이터 오류: {wallet_data}")

        # 필요한 데이터 추출
        target_data = wallet_data.get(symbol)
        position = target_data.get("position")
        quantity = target_data.get("quantity")
        margin = target_data.get("margin")
        entry_price = target_data.get("entryPrice")

        # 입력 데이터 검증
        if not isinstance(current_price, (int, float)) or current_price <= 0:
            raise ValueError("현재 가격은 0보다 커야 합니다.")
        if quantity is None or margin is None or entry_price is None:
            raise ValueError(f"지갑 데이터 누락: {target_data}")
        if not all(
            isinstance(value, (int, float)) for value in [quantity, margin, entry_price]
        ):
            raise ValueError("quantity, margin, entry_price 값은 숫자형이어야 합니다.")
        if quantity <= 0 or margin <= 0 or entry_price <= 0:
            raise ValueError("quantity, margin, entry_price 값은 0보다 커야 합니다.")

        # 수익 계산
        realized_pnl = self.get_calc_pnl(
            current_price=current_price,
            entry_price=entry_price,
            quantity=quantity,
            position=position,
        )  # 실현된 손익
        transaction_fee = current_price * quantity * fee  # 거래 수수료
        total_value = (margin + realized_pnl) - transaction_fee  # 총 반환 가치

        return total_value

    @staticmethod
    def get_calc_pnl(
        entry_price: float, current_price: float, quantity: float, position: str
    ) -> float:
        """
        1. 기능 : 실현된 손익 값을 반환한다.
        2. 매개변수
            1) entry_price : 진입가격
            2) current_price : 현재 가격
            3) quantity : 수량
            4) position : 현재 포지션
        """
        position = position.upper()

        if current_price == 0 and entry_price == 0:
            return 0

        if position == "LONG":
            return (current_price - entry_price) * quantity  # long 실현된 손익
        elif position == "SHORT":
            return (entry_price - current_price) * quantity  # short 실현된 손익
        else:
            raise ValueError(f"position 입력 오류 - {position}")

    # 테스트 실행결과 안맞다. 방법을 못찾겠따.
    def __get_liquidation_price(
        self,
        entry_price: float,
        leverage: int,
        quantity: float,
        margin_balance: float,
        position_type="long",
    ):
        """
        Binance 선물 거래 청산 가격 계산 함수.

        :param entry_price: 진입 가격 (float)
        :param leverage: 레버리지 (int)
        :param position_size: 포지션 크기 (float, 계약 수)
        :param margin_balance: 증거금 (float)
        :param position_type: 포지션 타입 ("long" 또는 "short")
        :return: 청산 가격 (float)
        """
        position_type = position_type.upper()

        if leverage <= 0:
            raise ValueError("Leverage must be greater than 0.")
        if quantity <= 0:
            raise ValueError("Position size must be greater than 0.")
        if margin_balance <= 0:
            raise ValueError("Margin balance must be greater than 0.")
        if position_type not in ["LONG", "SHORT"]:
            raise ValueError("Position type must be 'long' or 'short'.")

        # 초기 증거금 계산
        initial_margin = quantity / leverage

        # 롱 포지션 청산 가격 계산
        if position_type == "LONG":
            liquidation_price = entry_price * (1 - (margin_balance / quantity))
        # 숏 포지션 청산 가격 계산
        else:  # position_type == "short"
            liquidation_price = entry_price * (1 + (margin_balance / quantity))

        return round(liquidation_price, 2)


class WalletManager:
    """
    가상의 wallet을 생성 및 운영함.
    """

    def __init__(self, initial_fund: float):
        self.account_balances = {}
        self.initial_fund = initial_fund
        self.balance_info = {
            "available_funds": self.initial_fund,
            "locked_funds": {
                "number_of_stocks": 0,
                "profit_and_loss": 0,
                "maintenance_margin": 0,
                "profit_margin_ratio": 0,
            },
            "total_assets": self.initial_fund,
        }
        self.fee = 0.0005

    # 매수(position open)주문 생성시 계좌에 정보 추가.
    def add_funds(
        self, order_signal: Dict[str, Optional[Any]]
    ) -> Tuple[Dict[str, Union[float, Dict[str, float]]], float]:
        """
        1. 기능 : 신규 주문 진행시 해당종목의 정보를 기록한다.
        2. 매개변수
            1) order_signal : 주문 신호 정보
        """
        symbol = order_signal.get("symbol")
        if not isinstance(symbol, str):
            raise ValueError(f"Order signal error - {symbol}")
        margin = order_signal.get("margin")
        if margin is None:
            raise ValueError(f"주문 정보가 유효하지 않음.")

        self.account_balances[symbol] = order_signal
        self.balance_info["available_funds"] -= margin * (1 - self.fee)
        self.__update_locked_funds
        return (self.balance_info, margin)

    # 거래 종료시 해당 종목의 정보를 삭제하고, 손익비용을 반환한다.
    def remove_funds(
        self, symbol: str
    ) -> Tuple[Dict[str, Union[float, Dict[str, float]]], float]:
        """
        1. 기능 : 거래 종료시 해당 종목의 정보를 삭제하고, 손익비용을 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        """
        target_data = self.account_balances.get(symbol)
        if target_data is None:
            raise ValueError("데이터가 유효하지 않음.")

        entry_price = target_data.get("entryPrice")
        current_price = target_data.get("currentPrice")
        quantity = target_data.get("quantity")
        position = target_data.get("position")
        margin = target_data.get("margin")
        if None in (entry_price, current_price, quantity, position, margin):
            raise ValueError("데이터가 유효하지 않음.")

        pnl_value = OrderManager.get_calc_pnl(
            entry_price=entry_price,
            current_price=current_price,
            quantity=quantity,
            position=position,
        )
        fund = pnl_value + margin

        self.balance_info["available_funds"] += fund
        del self.account_balances[symbol]

        # wallet정보를 업데이트 한다.
        self.__update_locked_funds
        return (self.balance_info, pnl_value)

    # 계좌 정보를 업데이트한다.
    def __update_locked_funds(self):
        """
        1. 기능 : 계좌정보를 현재가격을 반영하여 업데이트한다.
        2. 매개변수 : 해당없음.
        """
        number_of_stocks = 0
        profit_and_loss = 0
        maintenance_margin = 0
        profit_margin_ratio = 0

        # 업데이트 할 내용 없을경우 함수 종료
        if self.account_balances == {}:
            return self.balance_info

        # account_balaces의 정보를 기준으로 연산에 필요한 정보를 수집한다.
        for symbol, symbol_data in self.account_balances.items():
            entry_price = symbol_data.get("entryPrice")
            current_price = symbol_data.get("currentPrice")
            quantity = symbol_data.get("quantity")
            position = symbol_data.get("position")
            margin = symbol_data.get("margin")

            # 데이터에 문제가 발생할 경우 stop처리 한다. 하나라도 이상 데이터가 나올 수 없다.
            if None in (entry_price, current_price, quantity, position, margin):
                raise ValueError(f"account_balance 오류 - {symbol_data}")

            # 보유량 표시
            number_of_stocks += 1
            profit_and_loss += OrderManager.get_calc_pnl(
                entry_price=entry_price,
                current_price=current_price,
                quantity=quantity,
                position=position,
            )
            maintenance_margin += margin

        # pnl정보가 0이 아닐경우 초기값인 0을 연산값으로 대체한다. (에러 대응)
        if not profit_and_loss == 0:
            profit_margin_ratio = round(profit_and_loss / maintenance_margin, 3)

        available_funds = self.balance_info["available_funds"]
        total_assets = profit_and_loss + maintenance_margin + available_funds

        # balance_info update
        self.balance_info["locked_funds"]["number_of_stocks"] = number_of_stocks
        self.balance_info["locked_funds"]["profit_and_loss"] = profit_and_loss
        self.balance_info["locked_funds"]["maintenance_margin"] = maintenance_margin
        self.balance_info["locked_funds"]["profit_margin_ratio"] = profit_margin_ratio
        self.balance_info["total_assets"] = total_assets

        return self.balance_info

    # 계좌의 보유재고에 'currentPrice'항목 업데이트
    def __update_current_price(
        self, symbol: str, current_price: str
    ) -> Dict[str, Dict[str, Optional[Any]]]:
        """
        1. 기능 : 보유중인 코인정보의 현재가를 업데이트한다. 전체 계좌 업데이트시 사용
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) current_price :현재가
        """
        wallet = self.account_balances.get(symbol)
        if wallet:
            self.account_balances[symbol]["currentPrice"] = current_price
            return self.account_balances
        else:
            pass

    # 계좌의 정보를 연산 및 계좌 상태 정보를 반환한다.
    def get_wallet_status(
        self, symbol: Optional[str] = None, current_price: Optional[str] = None
    ) -> Dict[str, float]:
        # wallet에 대해 symbol정보 없을때에 대하여 대비 되어 있음 (pass 처리)
        self.__update_current_price(symbol=symbol, current_price=current_price)
        self.__update_locked_funds()
        return self.balance_info


#     def
class WasteTypeCode:
    """
    폐기 코드 집합소 / 전부 주석처리한다.
    """
    # # 현물시장의 symbol별 입력된 interval값 전체를 수신 및 반환한다.
    # async def get_kilne_data(
    #     self,
    #     symbol: str,
    #     intervals: Union[List[str], str],
    #     start_date: Optional[str] = None,
    #     end_date: Optional[str] = None,
    #     market_type: str = "futures",
    # ) -> Dict[str, List]:
    #     """
    #     1. 기능 : symbol별 입력된 interval값 전체를 수신 및 반환한다.
    #     2. 매개변수
    #         1) symbol : 쌍거래 symbol
    #         2) start_date : '2024-01-01 00:00:00'
    #         3) end_date : '2024-01-02 00:00:00'
    #         4) save_directory_path : 저장할 파일 위치 (파일명 or 전체 경로)
    #         5) intervals : 수신하고자 하는 데이터의 interval 구간
    #     """

    #     # 매개변수 타입 통일 위하여 대문자로 변경함.
    #     symbol = symbol.upper()
    #     if isinstance(intervals, str):
    #         # interval값을 대문자로 적용시 1분봉 '1m'과 1개월봉 '1M'이 겹쳐버린다. 주의.
    #         intervals = [intervals]

    #     # 현재 매개변수 입력값이 None일경우 속성값으로 대체 (별도 계산필요시 적용 위함.)
    #     target_start_date: str = start_date or self.start_date
    #     target_end_date = end_date or self.end_date

    #     conv_start_date = utils._convert_to_datetime(target_start_date)
    #     conv_end_date = utils._convert_to_datetime(target_end_date)
    #     historical_data = {}

    #     for interval in intervals:
    #         historical_data[interval] = await SpotTrade().get_historical_kline_hour_min(
    #             symbol=symbol,
    #             interval=interval,
    #             start_date=conv_start_date,
    #             end_date=conv_end_date,
    #         )

    #     return historical_data
