import os
import utils
from typing import Dict, List, Union
# from Analysis import AnalysisManager

def update_data(kline_path: str, index_path: str):
    if not os.path.exists(kline_path):
        raise ValueError(f"{kline_path} path가 올바르지 않음.")
    if not os.path.exists(index_path):
        raise ValueError(f"{index_path} path가 올바르지 않음.")
    kline_data = utils._load_json(file_path=kline_path)
    index_data = utils._load_json(file_path=index_path)
    return (kline_data, index_data)

class DataManager:
    def __init__(self, kline_data, index_data):
        self.kline_data = kline_data
        self.index_data = index_data
        self.intervals = list(kline_data.keys())
        self.__validate_data()
    
    # 데이터의 유효성을 검사한다.
    def __validate_data(self):
        """
        1. 기능 : instance 선언시 입력되는 변수값의 유효성을 검사한다.
        2. 매개변수 : 해당없음.
        """
        if not isinstance(self.kline_data, dict) or not self.kline_data:
            raise ValueError(f'kline 데이터가 유효하지 않음.')
        if not isinstance(self.index_data, list) or not self.index_data:
            raise ValueError(f'index 데이터가 유효하지 않음.')
        if len(self.kline_data.keys()) != len(self.index_data[0]):
            raise ValueError(f'kline interval값과 index 데이터의 길이가 맞지 않음.')
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
    
    # 기간별 각 interval값을 raw데이터와 동일한 형태로 반환한다.
    def get_kline_data_by_range(self, end_index: int, step: int=4320) -> Dict[str, List[List[Union[int, str]]]]:
        """
        1. 기능 : 기간별 데이터를 추출한다.
        2. 매개변수
            1) start_index : index 0 ~ x까지 값을 입력
            2) step : 데이터 기간(min : 4320
                - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
        """
        start_index = end_index - step
        if start_index < 0:
            start_index = 0

        start_indices = self.index_data[start_index]
        end_indices = self.index_data[end_index]

        start_mapped_intervals = self.__map_intervals_to_indices(index_values=start_indices)
        end_mapped_intervals = self.__map_intervals_to_indices(index_values=end_indices)

        result = {}
        for interval in self.intervals:
            interval_data = self.kline_data.get(interval)
            start_index_value = start_mapped_intervals.get(interval)
            end_index_value = end_mapped_intervals.get(interval)

            sliced_data = interval_data[start_index_value:end_index_value]
            result[interval] = sliced_data
        return result


if __name__ == "__main__":
    kline = "/Users/nnn/GitHub/DataStore/BTCUSDT.json"
    index = "/Users/nnn/GitHub/DataStore/BTCUSDT_index.json"
    
    kline_data, index_data = update_data(kline_path=kline, index_path=index)
    
    obj = DataManager(kline_data=kline_data,
                      index_data=index_data)
    print(obj.get_kline_data_by_range(end_index=15))

# class DataManager:
#     def __init__(self, symbol: str, data_directory: str = "DataStore"):
#         self.symbol = symbol.upper()
#         self.data_directory = data_directory

#         self.file_extension = ".json"
#         self.kline_data: Dict[str, List[List[Union[int, str]]]] = self.__load_kline_data()
#         self.time_intervals = self.__extract_intervals()
#         self.index_data: List[List[int]] = self.__load_index_data()
#         self.mapped_intervals: Dict[str, int] = self.__map_intervals_to_indices(index_values=self.index_data[0])

#     # 데이터 파일 경로를 반환하는 메서드
#     def __build_file_path(self, data_type: str) -> str:
#         data_type = data_type.upper()
#         if data_type == "KLINE":
#             file_name = self.symbol + self.file_extension
#         elif data_type == "INDEX":
#             file_name = self.symbol + "_index" + self.file_extension
#         current_directory = os.getcwd()
#         parent_directory = os.path.dirname(current_directory)
#         file_path = os.path.join(parent_directory, self.data_directory, file_name)

#         if not os.path.exists(file_path):
#             raise ValueError(f"파일이 존재하지 않습니다: {file_path}")
#         return file_path

#     # Kline 데이터를 불러오는 메서드
#     def __load_kline_data(self) -> Dict[str, List[List[Union[int, str]]]]:
#         """
#         1. 기능 : kline데이터를 불러온다.
#         2. 매개변수 : 해당없음.(class instance화 할때 변수값 반영)
#         """
#         file_path = self.__build_file_path(data_type="kline")
#         data = utils._load_json(file_path=file_path)
#         self.kline_data = data
#         return self.kline_data

#     # 인덱스 데이터를 불러오는 메서드
#     def __load_index_data(self) -> List[List[int]]:
#         """
#         1. 기능 : 인덱스 매칭 데이터를 불러온다.      
#         2. 매개변수 : 해당없음.(class instance화 할때 변수값 반영)
#         """
#         file_path = self.__build_file_path(data_type="index")
#         data = utils._load_json(file_path=file_path)
#         self.index_data = data
#         return self.index_data

#     # Kline 데이터에서 구간(interval)을 추출하는 메서드
#     def __extract_intervals(self) -> List[str]:
#         """
#         1. 기능 : kline 데이터의 interval 값을 추출한다. 1회 사용한다.
#         2. 매개변수 : 해당없음.(class instance화 __ㅣ할때 변수값 반영)
#         """
#         if isinstance(self.kline_data, dict):
#             return list(self.kline_data.keys())
#         else:
#             raise ValueError("Kline 데이터가 유효하지 않습니다.")

#     # 구간(interval)과 인덱스 데이터를 매핑하는 메서드
#     def __map_intervals_to_indices(self, index_values: List[int]) -> Dict[str, int]:
#         """
#         1. 기능 : interval과 index데이터를 연산이 용이하도록 매핑한다.
#         2. 매개변수
#             1) index_values : 각 구간별 index 정보
#         """
#         if len(self.time_intervals) != len(index_values):
#             raise ValueError("구간 데이터와 인덱스 데이터의 길이가 일치하지 않습니다.")

#         mapped_intervals = {}
#         for i, interval in enumerate(self.time_intervals):
#             mapped_intervals[interval] = index_values[i]

#         return mapped_intervals

#     def data_load(self, file_path: str):
#         utils._load_json(file)

#     # 특정 범위의 데이터를 추출하는 메서드
#     def get_kline_data_by_range(self, end_index: int, step: int=4320) -> Dict[str, List[List[Union[int, str]]]]:
#         """
#         1. 기능 : 기간별 데이터를 추출한다.
#         2. 매개변수
#             1) start_index : index 0 ~ x까지 값을 입력
#             2) step : 데이터 기간(min : 4320
#                 - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
#         """
#         start_index = end_index - step
#         if len(start_index) <= 1:
#             start_index = 0

#         start_indices = self.index_data[start_index]
#         end_indices = self.index_data[end_index]

#         start_mapped_intervals = self.__map_intervals_to_indices(index_values=start_indices)
#         # print(start_mapped_intervals)
#         end_mapped_intervals = self.__map_intervals_to_indices(index_values=end_indices)
#         # print(end_mapped_intervals)

#         result = {}
#         for interval in self.time_intervals:
#             interval_data = self.kline_data.get(interval)
#             start_index_value = start_mapped_intervals.get(interval)
#             end_index_value = end_mapped_intervals.get(interval)

#             sliced_data = interval_data[start_index_value:end_index_value]
#             result[interval] = sliced_data
#         return result

            
# class RecoderManager:
#     def __init__(self):
#         self.position_status = None
        
#         self.position_form = {'symbol':'btcusdt',
#                               'position':'long',
#                               'tradeStatus':'open',
#                               'tradeTimeStemp':123123,
#                               'entryPrice':0.0001,
#                               'leverage':11231,
#                               'quantity':1231,
#                               }
        
        
# if __name__ == "__main__":
#     symbol = 'btcusdt'
#     obj = DataManager(symbol=symbol)
#     analy_obj = AnalysisManager()
#     result = []
#     # for i in range(len(obj.index_data)-1):
#     #     analy_obj.kline_data = obj.get_kline_data_by_range(end_index=i)
#     #     # print(analy_obj.kline_data[-1])
#     #     # case_1 = analy_obj.case2_conditions(kline_data=analy_obj.kline_data)
#     #     # if case_1[2] and case_1[-1] and case_1[-2]>3:
#     #     #     print(f'{i} - {case_1}')
#     #     utils._std_print(len(analy_obj.kline_data))