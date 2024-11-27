import os
import utils
import Analysis
import time
import numpy as np
from numpy.typing import NDArray
import TradingDataManager
import asyncio
from typing import Dict, List, Union, Any, Optional


def update_data(kline_path: str, index_path: str):
    if not os.path.exists(kline_path):
        raise ValueError(f"{kline_path} path가 올바르지 않음.")
    if not os.path.exists(index_path):
        raise ValueError(f"{index_path} path가 올바르지 않음.")
    kline_data = utils._load_json(file_path=kline_path)
    index_data = utils._load_json(file_path=index_path)
    return (kline_data, index_data)

# 임시생성 함수
def signal(analy_data):
    if analy_data[2] and analy_data[4]:
        position = 'LONG' if analy_data[0]==1 else 'SHORT'
        leverage = analy_data[3]
        return {'position':position,
                'leverage':leverage}
    else:
        return False

# 테스트에 사용할 Dummy Data를 수신한다.
class DummyDataGenerator:
    """백테스트에 사용할 더미 데이터를 수집한다. system trading에서 사용하는 타입과 동일하게 생성한다."""
    def __init__(self, market_type: str):
        """
        1. 기능 : 초기화 함수로 시장 유형에 따라 적절한 데이터 제어 인스턴스를 생성한다.
        2. 매개변수
            1) market_type : 'FUTURES' 또는 다른 시장 유형
        """
        self.market_type = market_type
        if market_type == "FUTURES":
            self.instance = TradingDataManager.FuturesDataControl()
        else:
            self.instance = TradingDataManager.SpotDataControl()

    # directory와 file을 합쳐 주소값을 반환한다.
    def __generate_path(self, directory: str, file_name: str) -> str:
        """
        1. 기능 : directory와 file명을 결합하여 주소값을 생성한다.
        2. 매개변수
            1) directory : 목표 최하위 디렉토리
            2) file_name : 파일명(확장자 포함)
        """
        return os.path.join(directory, file_name)

    # 폴더를 생성한다.
    def __create_folder(self, folder_path: str):
        """
        1. 기능 : 폴더를 생성한다.
        2. 매개변수
            1) folder_path : 생성하고자 하는 폴더의 전체 주소 (파일명 제외)
        """
        if not os.path.isdir(folder_path):
            os.makedirs(folder_path)

    # symbol별 입력된 interval값 전체를 수신 및 반환한다.
    async def get_historical_kline(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
        intervals: Union[List[str], str],
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
        symbol = symbol.upper()
        if isinstance(intervals, str):
            intervals = [intervals]

        start_date = utils._convert_to_datetime(start_date)
        end_date = utils._convert_to_datetime(end_date)
        historical_data = {}

        for interval in intervals:
            historical_data[interval] = await self.instance.fetch_historical_kline_hour_min(
                symbol=symbol,
                interval=interval,
                start_date=start_date,
                end_date=end_date,
            )

        return historical_data

    # KLINE_INTERVAL 유효성 검사 오류시 입력된 intervals값으로 초기화
    def set_intervals(self, intervals: List[str]):
        """
        1. 기능 : KLINE_INTERVAL 유효성 검사 오류시 입력된 intervals값으로 초기화
        2. 매개변수
            1) intervals : 적용하고자 하는 데이터의 interval 구간
        3. 기타 : 테스트 안 해봄
        """
        self.instance.KLINE_INTERVALS = intervals

    # 각각 symbol별 분리저장되어 있는 kline데이터를 하나의 dict형태로 결합한다. (최종결과물))
    def merge_json_files(self, directory_path: str, file_suffix: str) -> Dict[str, Dict]:
        """
        1. 기능 : 각각 symbol별 분리저장되어 있는 kline데이터를 하나의 dict형태로 결합한다.
        2. 매개변수
            1) directory_path : 데이터가 있는 디렉토리 전체 경로
            2) file_suffix : Dummy Data에 공통으로 들어가 있는 접미사 + 확장자명
        """
        merged_data = {}

        # 디렉토리 내의 파일 목록 탐색
        for file_name in os.listdir(directory_path):
            if file_name.endswith(file_suffix):
                symbol = file_name.split('_')[0]
                merged_data[symbol] = {}
                file_path = os.path.join(directory_path, file_name)

                # JSON 파일 로드
                json_data = utils._load_json(file_path=file_path)
                if not isinstance(json_data, dict):
                    raise ValueError(f"파일 '{file_name}'의 데이터가 딕셔너리 형식이 아닙니다.")

                # 병합 수행
                for key, value in json_data.items():
                    merged_data[symbol][key] = value
        return merged_data

# 더미테이더의 interval값들간 매칭되는 index값을 계산한다.
class MatchingIndicesGenerator:
    """각 interval별로 open, close 시간대가 매칭되는 값들의 index를 연산한다. 이에 따른 백테스트시 각종 interval 데이터의 유효성을 획득한다."""
    def __init__(self):
        pass

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
    def calculate_matching_indices(self, kline_data: Dict) -> List[List[int]]:
        """
        1. 기능 : 각 interval구간 데이터의 연결되는 data index값을 연산 및 반환한다.
        2. 매개변수
            1) kline_data : 원본 kline data
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
                    match_row.append(None)
                    continue

                # 조건을 만족하는 인덱스 찾기
                condition_indices = np.where(
                    (interval_data[:, 0] <= open_time) & 
                    (interval_data[:, 6] >= close_time)
                )[0]

                if condition_indices.size == 0:
                    match_row.append(None)
                else:
                    match_row.append(int(condition_indices[0]))

            if None in match_row:
                continue
            matching_indices.append(match_row)
            # utils._std_print(match_row)
        
        return matching_indices
"""



            여기까지 특이사항 없으나, 별도 각자 알아서 저장해야함이 조금 번거롭다.




"""
# interval별 index값을 반영하여 백테스트에 대입할 값을 추출한다.
class IntervalKlineExtractor:
    """획득한 interval별 index데이터를 대입하여 실제로 매칭되는 interval 값들만 추출한다. 해당 데이터를 백테스트 연산에 대입한다."""
    def __init__(self, symbols, kline_data, index_data):
        self.kline_data = kline_data
        self.index_data = index_data
        self.intervals = []
        self.symbols = symbols
        self.__update_intervals()
        self.__validate_data()

    # 클라스 속성의 intervals 값을 업데이트한다.
    def __update_intervals(self):
        intervals = []
        for _, data in self.kline_data.items():
            for key, _ in data.items():
                if not key in intervals:
                    intervals.append(key)
        self.intervals = intervals

    # 데이터의 유효성을 검사한다.
    def __validate_data(self):
        """
        1. 기능 : instance 선언시 입력되는 변수값의 유효성을 검사한다.
        2. 매개변수 : 해당없음.
        """
        if not isinstance(self.kline_data, dict) or not self.kline_data:
            raise ValueError(f"kline 데이터가 유효하지 않음.")
        if not isinstance(self.index_data, list) or not self.index_data:
            raise ValueError(f"index 데이터가 유효하지 않음.")
        
        for key, data in self.kline_data.items():
            if len(data.keys()) != len(self.index_data[0]):
                raise ValueError(f"kline interval값과 index 데이터의 길이가 맞지 않음.")
        return True

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

    # range에 반영할 data의 길이를 계산 및 반환한다.
    def get_data_length(self):
        length = len(self.index_data) - 1
        return length

    # 기간별 각 interval값을 raw데이터와 동일한 형태로 반환한다.
    def get_kline_data_by_range(
        self, end_index: int, step: int = 4320
    ) -> Dict[str, Dict[str, NDArray[np.float64]]]:
        """
        1. 기능 : 기간별 데이터를 추출한다.
        2. 매개변수
            1) start_index : index 0 ~ x까지 값을 입력
            2) step : 데이터 기간(min : 4320
                - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
        """
        result = {}
        
        for symbol, kline_data_symbol in self.kline_data.items():
            result[symbol] = {}
            for interval, kline_data_interval in kline_data_symbol.items():
                #intervals 리스트에 없는 interval은 제외한다.
                if not interval in self.intervals:
                    continue
                start_index = end_index - step
                if start_index < 0:
                    start_index = 0
                start_indices = self.index_data[start_index]
                end_indices = self.index_data[end_index]

                
                start_mapped_intervals = self.__map_intervals_to_indices(
                    index_values=start_indices
                )
                end_mapped_intervals = self.__map_intervals_to_indices(index_values=end_indices)


                start_index_value = start_mapped_intervals.get(interval)
                end_index_value = end_mapped_intervals.get(interval)

                sliced_data = kline_data_interval[start_index_value:end_index_value]
                data_np_array = np.array(object=sliced_data, dtype=float)
                result[symbol][interval] = data_np_array
        return result


class SignalRecorder:
    """
    가상 거래 내역을 기록하고 해당 내용을 공유한다.
    """

    def __init__(self):
        self.trade_history: List[Dict[str, Union[Any]]] = []

    def submit_trade_open_signal(
        self,
        position: bool,
        nested_kline_data: list[Union[str, int]],
        leverage: int,
        quantity: float,
        analysis_type: str = "anylisys_1",
    ):
        close_timestamp = nested_kline_data[6]
        close_price = nested_kline_data[4]
        trade_data = {
            "tradeStatus": True,
            "executionTimestamp": close_timestamp,
            # "executionDate": utils._convert_to_datetime(close_timestamp),
            "price": float(close_price),
            "position": position,
            "leverage": leverage,
            "quantity": quantity,
        }
        self.trade_history.append(trade_data)
        return trade_data

    def submit_trade_close_signal(
        self, nested_kline_data: list[Union[str, int]], stoploss_type: str = "stop_1"
    ):
        close_timestamp = nested_kline_data[6]
        close_price = nested_kline_data[4]
        quantity = self.trade_history[-1].get("quantity")
        leverage = self.trade_history[-1].get("leverage")
        last_position = self.trade_history[-1].get("position")
        position = "LONG" if last_position == "SHORT" else "SHORT"
        datetime = utils._convert_to_datetime(close_timestamp)
        trade_data = {
            "tradeStatus": False,
            "executionTimestamp": close_timestamp,
            # "executionDate": utils._convert_to_datetime(close_timestamp),
            "price": close_price,
            "position": position,
            "leverage": leverage,
            "quantity": quantity,
        }
        self.trade_history.append(trade_data)
        return trade_data

    def dump_to_json(self, file_path: str):
        utils._save_to_json(
            file_path=file_path, new_data=self.trade_history, overwrite=True
        )
        return

    def get_trade_history(self):
        return self.trade_history


class TradeStopper:
    def __init__(self, rist_ratio: float = 0.85, profit_ratio: float = 0.015):
        self.reference_price: Optional[float] = None

        self.risk_ratio = rist_ratio
        self.profit_ratio = profit_ratio
        self.target_price: Optional[float] = None

    def __clear_price_info(self):
        self.reference_price = None
        self.target_price = None

    def __trade_status(self, trade_history) -> bool:
        trade_data = trade_history[-1]
        return trade_data.get("tradeStatus")

    def __calculate_target_price(
        self, entry_price: float, reference_price: float, position: str
    ) -> float:
        position = position.upper()
        if position not in ["LONG", "BUY", "SELL", "SHORT"]:
            raise ValueError(f"유효하지 않은 포지션: {position}")
        if position in ["LONG", "BUY"]:
            dead_line_price = entry_price + (
                (reference_price - entry_price) * self.risk_ratio
            )
            return dead_line_price * (1 - self.profit_ratio)
        elif position in ["SHORT", "SELL"]:
            dead_line_price = entry_price - (
                (entry_price - reference_price) * self.risk_ratio
            )
            return dead_line_price * (1 + self.profit_ratio)
        else:
            raise ValueError(f"position입력오류 : {position}")

    def generate_close_signal_scenario1(
        self, nested_kline_data: list[Union[str, int]], trade_history: list
    ) -> bool:
        if not self.__trade_status(trade_history=trade_history):
            return False
        
        current_price = float(nested_kline_data[4])
        current_position = trade_history[-1].get("position")
        # Reference price 업데이트
        if not self.reference_price:
            self.reference_price = current_price
            
        if current_position in ["LONG", "BUY"]:
            self.reference_price = max(self.reference_price, current_price)
        elif current_position in ["SHORT", "SELL"]:
            self.reference_price = min(self.reference_price, current_price)

        # self.reference_price = reference_price

        # utils._std_print(self.reference_price)
        # Target price 계산
        self.target_price = self.__calculate_target_price(
            entry_price=current_price,
            reference_price=self.reference_price,
            position=current_position,
        )

        # 종료 조건
        if current_position in ["LONG", "BUY"] and current_price <= self.target_price:
            self.__clear_price_info()
            return True
        elif (
            current_position in ["SHORT", "SELL"] and current_price >= self.target_price
        ):
            self.__clear_price_info()
            return True

        return False


class Wallet:
    def __init__(self, initial_capital: float = 1_000, fee_ratio: float = 0.05):
        self.initial_capital: float = initial_capital
        self.fee_ratio: float = fee_ratio
        self.fee_value: float = 0
        self.free: float = initial_capital
        self.lock: float = 0
        self.total_balance: float = 0
        self.profit_to_loss_ratio: float = 0
        self.safety_ratio: float = 0.35
        self.available_value: float = initial_capital * (1-self.safety_ratio)

    # 청산시 오류발생, 시스템 멈춤
    def __vaildate_balance(self):
        if self.free < 0:
            raise ValueError(f"{self.free} - 청산 발생")

    # 손익비율 계산
    def __cals_profit_to_loss_ratio(self):
        total_balance = self.lock + self.free
        cals_ratio = total_balance / self.initial_capital
        return round(cals_ratio, 3)

    # 안전 자산 외 자산
    def __cals_available_value(self):
        return self.total_balance * (1 - self.safety_ratio)

    # 잔고 총액 계산
    def __cals_total_balance(self):
        return self.free + self.lock

    # 출금 처리
    def withdrawal(self, USDT: float):
        self.__vaildate_balance()
        self.fee_value += self.fee_ratio * USDT
        value = USDT - self.fee_value
        self.free = self.free - USDT
        self.lock += value
        self.total_balance = self.__cals_total_balance()
        self.available_value=self.__cals_available_value()
        self.profit_to_loss_ratio = self.__cals_profit_to_loss_ratio()
        self.__vaildate_balance()

    # 입금 처리
    def deposit(self, USDT: float):
        value = (1 - self.fee_ratio) * USDT
        self.fee_value += self.fee_ratio * USDT
        self.lock = 0
        self.free += self.lock
        self.__cals_total_balance()
        self.__cals_available_value()
        self.__cals_profit_to_loss_ratio()

    # 실시간 wallet의 lock을 업데이트 한다.
    def realtime_wallet_update(self, current_price:float, trade_history:dict):
        last_trade_history = trade_history[-1]
        leverage = last_trade_history.get('leverage')
        quantity = last_trade_history.get('quantity')
        return (current_price * quantity) / leverage
        
        
        
    # 계좌정보 반환
    def get_account_balance(self):
        return {
            "inital_money": self.initial_capital,
            "fee_ratio": self.fee_ratio,
            "fee_value": self.fee_value,
            "free": self.free,
            "lock": self.lock,
            "total_balance": self.total_balance,
            "profit_loss_ratio": self.profit_to_loss_ratio,
            "safety_ratio": self.safety_ratio,
        }


# if __name__ == "__main__":
    
#     #paramas 정보사항
#     market = 'futures'
#     start_date = '2024-1-1 00:00:00'
#     end_date = '2024-11-26 00:00:00'
#     symbols = ['BTCUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT']
#     directory = '/Users/nnn/GitHub/DataStore'
#     suffix = 'index.json'
#     # intervals = ['1m', '3m', '5m', '1d', '3d']
#     intervals = ['1m', '5m', '1h', '3d']
    
#     # dummy_data 저장 위치
#     path_data = os.path.join(directory, 'merge.json')
#     # index 매칭 데이터 저장 위치
#     path_idx = os.path.join(directory, 'indices_data.json')
    
#     #class instance
#     # dummy data 수집
#     ins_generator = DummyDataGenerator(market_type=market)
#     # dummy data index매칭
#     ins_indices = MatchingIndicesGenerator()
#     # 주문 발생시 신호 기록
#     ins_signal = SignalRecorder()
#     # 손절 또는 매각 가격 계산
#     ins_stopper = TradeStopper()
#     # 지갑정보 관련
#     ins_wallet = Wallet()
    
#     # 현재 시장 분석툴
#     ins_analy = Analysis.AnalysisManager()
    
#     # ticker 정보를 속성값에 저장한다.
#     ins_analy.symbols = symbols
    
#     # interval 값을 속성값에 저장한다.
#     ins_analy.intervals = intervals
    
    
    
    
#     # symbol별 데이터 수집 및 병합, 저장처리 (기존에 처리한 자료있으면 누락해도 됨.)
#     def data_sync():
#         for symbol in symbols:
#             symbol = symbol.upper()
#             path = os.path.join(directory, symbol+"_"+suffix)
#             data = asyncio.run(ins_generator.get_historical_kline(symbol=symbol,
#                                                                 start_date=start_date,
#                                                                 end_date=end_date,
#                                                                 intervals=intervals))
#             utils._save_to_json(file_path=path, new_data=data, overwrite=True)
            
#         merge_data = ins_generator.merge_json_files(directory_path=directory, file_suffix=suffix)
#         utils._save_to_json(file_path=path_data, new_data=merge_data, overwrite=True)

#         # dummy_data의 interval간 index 매칭 및 저장
#         indices_data = ins_indices.calculate_matching_indices(merge_data)
#         utils._save_to_json(file_path=path_idx, new_data=indices_data, overwrite=True)
        
#         # symbol별 데이터 로드, 위 코드 실행시 누락처리 가능.
    
#     # data_sync()
    
#     print('merge_data 로딩 시작.')
#     merge_data = utils._load_json(file_path=path_data)
#     print(f'merge_data 로딩완료 - {len(merge_data)}')
#     print('indices_data 로딩시작.')
#     indices_data = utils._load_json(file_path=path_idx)
#     print(f'indices_data 로딩완료 - {len(indices_data)}')
#     #class instance 추가 선언 (속성값 kline_data, index_data필요하므로...)
#     ins_kline_ex = IntervalKlineExtractor(kline_data=merge_data,
#                                           index_data=indices_data,
#                                           symbols=symbols)

    
#     # kline 시뮬레이션에 필요한 for문 range에 들어갈 값 계산 (데이터의 길이)
#     data_length = ins_kline_ex.get_data_length()
    
#     # 시뮬레이션 시작
#     # 데이터의 index값을 발생한다.
    
#     # MAX interval 분단위로 환산
#     data_range = 4320
    
#     n = 0 
#     for idx in range(data_length):
#         i = idx + data_range
#         # 데이터에 적용할 symbol값을 발생한다.
#         for symbol in symbols:
#             symbol = symbol.upper()
#             # index와 symbol값을 대입하여 값을 반환 받는다.
#             ins_analy.kline_data = ins_kline_ex.get_kline_data_by_range(end_index=i, step=data_range)
#             data_status = ins_analy.describe_data_state()
#             if not data_status.get('status'):
#                 utils._std_print(i)
#                 continue
#             # convert_data = ins_analy.convert_kline_array()
#             scenario_1 = ins_analy.scenario_1(symbol=symbol)#, convert_data=convert_data)
#             # result = ins_analy.scenario_1(symbol=symbol)
#             if scenario_1[2]>2 and scenario_1[3]>2 and scenario_1[4]>0 and scenario_1[-1]:
#                 index_ = indices_data[i][0]
#                 data_ = merge_data[intervals[0]][index_]
#                 print(symbol, scenario_1[0], data_)
#             utils._std_print(i)
from concurrent.futures import ThreadPoolExecutor
import os
import asyncio

# 데이터 동기화 및 준비 함수
def data_sync():
    for symbol in symbols:
        symbol = symbol.upper()
        path = os.path.join(directory, symbol + "_" + suffix)
        data = asyncio.run(ins_generator.get_historical_kline(
            symbol=symbol, start_date=start_date, end_date=end_date, intervals=intervals))
        utils._save_to_json(file_path=path, new_data=data, overwrite=True)

    merge_data = ins_generator.merge_json_files(directory_path=directory, file_suffix=suffix)
    utils._save_to_json(file_path=path_data, new_data=merge_data, overwrite=True)

    indices_data = ins_indices.calculate_matching_indices(merge_data)
    utils._save_to_json(file_path=path_idx, new_data=indices_data, overwrite=True)

# 심볼별 시뮬레이션 처리 함수
def process_symbol(symbol, i, kline_cache):
    symbol = symbol.upper()
    ins_analy.kline_data = kline_cache[i]
    data_status = ins_analy.describe_data_state()

    if not data_status.get('status'):
        return None

    scenario_1 = ins_analy.scenario_1(symbol=symbol)
    if scenario_1[-1] and scenario_1[2] > 2 and scenario_1[3] > 2 and scenario_1[4] > 0:
        index_ = indices_data[i][0]
        data_ = merge_data[intervals[0]][index_]
        return (symbol, scenario_1[0], data_)

    return None

# 메인 실행 코드
if __name__ == "__main__":
    # 파라미터 설정
    market = 'futures'
    start_date = '2024-1-1 00:00:00'
    end_date = '2024-11-26 00:00:00'
    symbols = ['BTCUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'SOLUSDT']
    directory = '/Users/nnn/GitHub/DataStore'
    suffix = 'index.json'
    intervals = ['1m', '5m', '1h', '3d']

    path_data = os.path.join(directory, 'merge.json')
    path_idx = os.path.join(directory, 'indices_data.json')

    ins_generator = DummyDataGenerator(market_type=market)
    ins_indices = MatchingIndicesGenerator()
    ins_analy = Analysis.AnalysisManager()
    ins_analy.symbols = symbols
    ins_analy.intervals = intervals

    # 데이터 로드
    print('merge_data 로딩 시작.')
    merge_data = utils._load_json(file_path=path_data)
    print(f'merge_data 로딩완료 - {len(merge_data)}')
    print('indices_data 로딩시작.')
    indices_data = utils._load_json(file_path=path_idx)
    print(f'indices_data 로딩완료 - {len(indices_data)}')

    ins_kline_ex = IntervalKlineExtractor(kline_data=merge_data, index_data=indices_data, symbols=symbols)
    data_length = ins_kline_ex.get_data_length()
    data_range = 4320

    kline_cache = {}

    print("시뮬레이션 시작")
    for idx in range(data_length):
        i = idx + data_range
        if i not in kline_cache:
            kline_cache[i] = ins_kline_ex.get_kline_data_by_range(end_index=i, step=data_range)

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(process_symbol, symbol, i, kline_cache) for symbol in symbols]
            for future in futures:
                result = future.result()
                if result:
                    print(*result)

        utils._std_print(i)