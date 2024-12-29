import ast
import asyncio
import json
import os
import sys
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, TypeVar, Union, Final, Dict, List, Union, Any
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from pprint import pformat


T = TypeVar("T")


def _info_kline_columns():
    return [
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


def _info_kline_intervals():
    return [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    ]


def _info_ticker_prices_dummy():
    return [
        {
            "symbol": "VIDTUSDT",
            "priceChange": "-0.0007000",
            "priceChangePercent": "-2.281",
            "weightedAvgPrice": "0.0307967",
            "lastPrice": "0.0299900",
            "lastQty": "2032",
            "openPrice": "0.0306900",
            "highPrice": "0.0322500",
            "lowPrice": "0.0296400",
            "volume": "523222663",
            "quoteVolume": "16113552.4409600",
            "openTime": 1735226220000,
            "closeTime": 1735312674334,
            "firstId": 38058345,
            "lastId": 38195016,
            "count": 136640,
        },
        {
            "symbol": "CETUSUSDT",
            "priceChange": "-0.0139000",
            "priceChangePercent": "-3.976",
            "weightedAvgPrice": "0.3460686",
            "lastPrice": "0.3357000",
            "lastQty": "21",
            "openPrice": "0.3496000",
            "highPrice": "0.3627700",
            "lowPrice": "0.3335400",
            "volume": "52445124",
            "quoteVolume": "18149608.3262600",
            "openTime": 1735226220000,
            "closeTime": 1735312672513,
            "firstId": 32422036,
            "lastId": 32595554,
            "count": 173516,
        },
        {
            "symbol": "BTCUSDT_250627",
            "priceChange": "5294.7",
            "priceChangePercent": "5.523",
            "weightedAvgPrice": "102639.7",
            "lastPrice": "101156.8",
            "lastQty": "0.001",
            "openPrice": "95862.1",
            "highPrice": "103780.1",
            "lowPrice": "90997.0",
            "volume": "154.021",
            "quoteVolume": "15808672.4",
            "openTime": 1735286700000,
            "closeTime": 1735312677534,
            "firstId": 1,
            "lastId": 13653,
            "count": 13653,
        },
    ]


def _info_24hr_ticker_dummy():
    return [
        {"symbol": "1000000MOGUSDT", "price": "2.2652000", "time": 1735312497433},
        {"symbol": "VANAUSDT", "price": "18.682000", "time": 1735312504022},
        {"symbol": "XAIUSDT", "price": "0.2428000", "time": 1735312502604},
        {"symbol": "ALGOUSDT", "price": "0.3395", "time": 1735312501560},
        {"symbol": "FLOWUSDT", "price": "0.723", "time": 1735312446406},
        {"symbol": "ETHWUSDT", "price": "3.427300", "time": 1735312500406},
        {"symbol": "DOGSUSDT", "price": "0.0005437", "time": 1735312502024},
        {"symbol": "BRETTUSDT", "price": "0.1292400", "time": 1735312502311},
        {"symbol": "1000XECUSDT", "price": "0.03467", "time": 1735312486481},
        {"symbol": "CFXUSDT", "price": "0.1621100", "time": 1735312499944},
        {"symbol": "KAVAUSDT", "price": "0.4613", "time": 1735312499940},
        {"symbol": "BATUSDT", "price": "0.2424", "time": 1735312498061},
        {"symbol": "ZKUSDT", "price": "0.1956400", "time": 1735312496696},
        {"symbol": "TNSRUSDT", "price": "0.4530000", "time": 1735312502049},
        {"symbol": "MEWUSDT", "price": "0.0065610", "time": 1735312500660},
        {"symbol": "XLMUSDT", "price": "0.34872", "time": 1735312498775},
        {"symbol": "NTRNUSDT", "price": "0.369600", "time": 1735312500326},
        {"symbol": "ALTUSDT", "price": "0.1157400", "time": 1735312503913},
        {"symbol": "PNUTUSDT", "price": "0.6473500", "time": 1735312502111},
        {"symbol": "OGNUSDT", "price": "0.1133", "time": 1735312479979},
        {"symbol": "SSVUSDT", "price": "24.924000", "time": 1735312501990},
        {"symbol": "GLMRUSDT", "price": "0.2592000", "time": 1715763618575},
        {"symbol": "INJUSDT", "price": "21.050000", "time": 1735312499980},
    ]


class DataContainer:
    """
    동적 데이터를 저장하고 관리한다. (변수명을 직접 등록하는게 아니라 함수로 생성함.)
    """

    def __init__(self):
        """동적 데이터를 저장하고 관리하는 컨테이너."""
        pass  # 딕셔너리 없이 속성만을 동적으로 관리

    def set_data(self, data_name, data):
        """
        1. 기능 : 속성명을 지정하고 데이터를 저장한다.
        2. 매개변수
            1) data_name : 등록할 속성명
            2) data : 저장할 data
        """
        # data_name이 숫자로 시작하는지 확인
        if data_name[0].isdigit():
            raise ValueError(f"속성명 '{data_name}'은 숫자로 시작할 수 없습니다.")

        setattr(self, data_name, data)

    def remove_data(self, data_name):
        """
        1. 기능 : 저장된 속성을 삭제한다.
        2. 매개변수
            1) data_name : 삭제할 속성명
        """
        if hasattr(self, data_name):
            delattr(self, data_name)
        else:
            raise AttributeError(f"No attribute named '{data_name}' to delete")

    def get_data(self, data_name):
        """
        1. 기능 : 저장된 속성에 대하여 데이터를 불러온다.
        2. 매개변수
            1) data_name : 불러올 속성명
        """
        if hasattr(self, data_name):
            return getattr(self, data_name)
        else:
            raise AttributeError(f"No attribute named '{data_name}'")

    def get_all_data_names(self):
        """
        1. 기능 : 현재 저장된 모든 속성명(변수명)을 반환한다.
        2. 반환값: 속성명 리스트
        """
        return list(self.__dict__.keys())

    def clear_all_data(self):
        """
        1. 기능 : 저장된 모든 속성을 초기화한다.
        """
        for attr in list(self.__dict__.keys()):
            delattr(self, attr)


# None발생시 Return 대응
def _none_or(result: Optional[T]) -> Optional[T]:
    if not result:
        return None
    return result


# str타입을 list타입으로 변환
def _str_to_list(data: Union[list, str], to_upper: bool = False) -> list:
    if isinstance(data, str):
        return [data.upper()] if to_upper else [data]

    elif isinstance(data, list):
        return [value.upper() for value in data] if to_upper else data

    else:
        raise ValueError(f"type 입력오류: '{type(data)}'는 지원되지 않는 타입입니다.")


# dict의 중첩된 값을 np.array화 한다.
def _convert_to_array(kline_data: dict, is_slice: bool = False):
    result = {}

    if is_slice:
        # 각 interval의 최소 데이터 길이를 계산
        all_intervals = set(
            interval for symbol_data in kline_data.values() for interval in symbol_data
        )

        min_lengths = {
            interval: min(
                len(kline_data[symbol][interval])
                for symbol in kline_data
                if interval in kline_data[symbol]
            )
            for interval in all_intervals
        }

        for symbol, symbol_data in kline_data.items():
            result[symbol] = {}
            for interval, interval_data in symbol_data.items():
                start_idx = -min_lengths[interval]
                sliced_data = interval_data[start_idx:]
                result[symbol][interval] = np.array(sliced_data, dtype=float)
        return result

    # Slice가 필요하지 않은 경우
    for symbol, symbol_data in kline_data.items():
        result[symbol] = {}
        for interval, interval_data in symbol_data.items():
            result[symbol][interval] = np.array(interval_data, dtype=float)
    return result


# kline_data를 container 자료형으로 반환한다.
def _convert_to_container(kline_data):
    """
    1. 기능 : np.array를 적용한 kline_data를 container데이터로 분류한다.
    2. 매개변수
        1) np.array를 적용한 kline_data
    3. 추가설명
        >> backtest할 경우 generate_kline_closing_sync처리한 데이터를 반영할것.
    """
    container_data = DataContainer()

    map_symbol = {}
    map_interval = {}

    symbols = list(kline_data.keys())
    intervals = list(kline_data[symbols[0]].keys())
    # print("START")
    for idx_i, interval in enumerate(intervals):
        map_interval[interval] = idx_i

        dummy_data = []

        for idx_s, symbol in enumerate(symbols):
            map_symbol[symbol] = idx_s

            target_data = kline_data[symbol][interval]
            dummy_data.append(target_data)
        try:
            dummy_data = np.array(dummy_data)
        except Exception as e:
            print(f"error - {e}")
            return 0, 0, False
        container_data.set_data(data_name=f"interval_{interval}", data=dummy_data)
    return map_symbol, map_interval, container_data


# 리터럴 값으로 파싱
def _convert_to_literal(input_value) -> Union[str, int, float, bool]:
    """
    1. 기능 : 문자형으로 구성된 int, float, bool 등 원래의 자료형태로 적용 및 반환.
    2. 매개변수
        1) input_value : 리터럴 처리하고자 하는 단일 값
    """
    try:
        return ast.literal_eval(input_value)
    except:
        return input_value


# List 안의 자료를 리터럴 값으로 파싱
def _convert_nested_list_to_literals(nested_list) -> List[Any]:
    """
    리스트 타입의 리스트를 입력받아, 내부 리스트의 각 요소를 리터럴 형태로 변환하여 반환합니다.

    :param nested_list: 변환할 리스트 타입의 리스트
    :return: 내부 요소들이 리터럴 형태로 변환된 리스트
    """
    converted_result = []
    for inner_list in nested_list:
        converted_list = []
        for item in inner_list:
            converted_list.append(_convert_to_literal(item))
        converted_result.append(converted_list)

    return converted_result


# 반환된 데이터를 리터럴값 반영
def _collections_to_literal(input_data: List[Dict[str, Any]]):
    result = []
    for dict_data in input_data:
        dict_ = {}
        for key, data in dict_data.items():
            dict_[key] = _convert_to_literal(data)
        result.append(dict_)
    return result


# list간 교차값 반환
def _find_common_elements(*lists) -> List:
    common_selements = set(lists[0]).intersection(*lists[1:])
    return list(common_selements)


# 시간 간격 interval 계산
def _calculate_divisible_intervals(time_unit):
    """
    1. 기능 : 시간, 분, 초 안에 들어갈 수 있는 간격 계산
    2. 매개변수
        1) time_unit : second, minute, hour 택 1
    """
    # 각 시간 단위에 대한 최대 값을 설정
    time_units = {"second": 60, "minute": 60, "hour": 24}

    # 해당 시간 단위의 최대 값을 가져옴
    max_value = time_units.get(time_unit)
    if not max_value:
        raise ValueError(
            "유효하지 않은 시간 단위입니다. 'second', 'minute', 'hour' 중 하나여야 합니다."
        )

    # 나누어떨어지는 간격 계산
    divisible_intervals = [0]
    for i in range(1, max_value):
        if max_value % i == 0:
            divisible_intervals.append(i)

    return divisible_intervals


# 다음 지정 간격까지 대기 (0초 return 발생)
async def _wait_until_next_interval(time_unit: str, interval: int) -> datetime:
    """
    1. 기능 : 다음 지정 interval시간 정각(0초) 까지 대기
    2. 매개변수
        1) time_unit : 'hour', 'minute', 'second'
        2) interval : INTERVALS값 참조
    """
    valid_intervals = _calculate_divisible_intervals(time_unit=time_unit)
    if interval not in valid_intervals:
        raise ValueError(f"잘못된 간격 입력: {valid_intervals} 중 하나를 선택하십시오.")

    # 시간 단위에 따른 최대값 설정 ('hour'는 24, 그 외는 60)
    max_step = 24 if time_unit == "hour" else 60

    while True:
        # 현재 시각 가져오기
        current_time = datetime.now()
        current_value = getattr(current_time, time_unit, None)

        # 유효한 값일 때 interval로 나누어떨어지고, 초가 0일 때 종료
        if (
            current_value is not None
            and current_value % interval == 0
            and current_time.second == 0
        ):
            return current_time

        # 1초 대기
        await asyncio.sleep(1)


# 지정된 시간 동안 대기 (timesleep버전)
async def _wait_time_sleep(time_unit: str, duration: int) -> datetime:
    """
    1. 기능 : 지정된 시간 동안 대기 (timesleep 버전)
    2. 매개변수
        1) time_unit : 시간 종류
            >> 'second' : 초
            >> 'minute' : 분
            >> 'hour' : 시간
        2) duration : 지속시간

        동작 예) unit.get() * duration
    """
    unit_seconds: Optional[int] = {"second": 1, "minute": 60, "hour": 3600}.get(
        time_unit
    )

    if not unit_seconds:
        raise ValueError(f"time_unit 입력오류: {time_unit}")

    # 각 단위를 초 단위로 변환하여 총 대기 시간 계산
    total_sleep_time = unit_seconds * duration

    # 00초 맞추기.
    # await _wait_until_next_interval(unit='minute')
    await asyncio.sleep(total_sleep_time)

    return datetime.now()


# 다음 정각까지 대기 (0초 return 발생)
async def _wait_until_exact_time(time_unit: str) -> datetime:
    """
    1. 기능 : time_unit기준 정각(0초)까지 대기
    2. 매개변수
        1) time_unit : 시간 종류
            >> 'second' : 초
            >> 'minute' : 분
            >> 'hour' : 시간
    """
    now = datetime.now()

    # 다음 각 단위로 맞추기 위해 대기할 시간 계산
    seconds_until_next_second = (
        1_000_000 - now.microsecond
    ) / 1_000_000  # 마이크로초를 초로 변환
    seconds_until_next_minute = seconds_until_next_second + (59 - now.second)
    seconds_until_next_hour = seconds_until_next_minute + ((59 - now.minute) * 60)

    # 대기 시간 설정
    interval_sleep = {
        "second": seconds_until_next_second,
        "minute": seconds_until_next_minute,
        "hour": seconds_until_next_hour,
    }

    target_sleep = interval_sleep.get(time_unit)

    # 주어진 단위가 유효하지 않은 경우 에러 발생
    if not target_sleep:
        raise ValueError(f"Invalid time unit provided: {time_unit}")

    # 지정된 단위에 맞춰 대기
    await asyncio.sleep(target_sleep)
    return datetime.now()


# 현재시간을 확보한다.
def _get_time_component(
    time_unit: Optional[str] = None,
) -> Union[int, datetime]:
    """
    1. 기능 : 현재시간을 반환한다.
    2. 매개변수
        1) time_unit : 시간 종류
            >> 'second' : 초
            >> 'minute' : 분
            >> 'hour' : 시간
    """
    current_time = datetime.now()
    if time_unit:
        unit_value = {
            "year": current_time.year,
            "month": current_time.month,
            "day": current_time.day,
            "hour": current_time.hour,
            "minute": current_time.minute,
            "second": current_time.second,
        }.get(time_unit)
        if unit_value is None:
            raise ValueError(f"time_unit 입력 오류. {time_unit}")
        return unit_value
    return current_time


# 문자형 시간 또는 datetime 형태 타입 변수를 밀리초 timestampe로 변환 및 반환.
def _convert_to_timestamp_ms(date: Union[str, datetime]) -> int:
    """
    1. 기능 : 문자형 시간 또는 datetime형태의 변수를 밀리초 timestamp로 변환 및 반환
    2. 매개변수
        1) date : str(예 : 2024-01-01 17:14:00) 또는 datetime형태의 시간 문자열
    """

    MS_SECOND = 1000  # 밀리초 변환을 위한 상수

    if isinstance(date, datetime):
        return int(date.timestamp() * MS_SECOND)
    else:
        return int(datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp() * MS_SECOND)


# 문자열 시간을 datetime 형태로로 변환 및 반환.
def _convert_to_datetime(date: Union[str, datetime, float, int]) -> datetime:
    """
    1. 기능 : str, int, datetime형태의 시간입력시 문자열 시간으로 반환한다.
    2. 매개변수
        1) date : str(예 : 2024-01-01 17:14:00)형태 변수
    """

    MS_SECOND = 1000  # 밀리초 변환을 위한 상수

    if isinstance(date, datetime):
        return date
    elif isinstance(date, (float, int)):
        return datetime.fromtimestamp(int(date / 1000)).strftime("%Y-%m-%d %H:%M:%S")
    elif isinstance(date, str):
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")


# 시작시간과 종료시간의 차이를 구하는 함수 (문자형, 타임스템프형, datetime형 자유롭기 입력)
def _get_time_delta(
    start_time: Union[int, str, datetime], end_time: Union[int, str, datetime]
) -> timedelta:
    """
    1. 기능 : 시작시간과 종료시간의 차이를 datetime형태로 반환한다.
    2. 매개변수
        1) start_time : timestamp_ms, datetime, '2024-01-01 00:00:00' 등
        2) end_time : timestamp_ms, datetime, '2024-01-01 00:00:00' 등
    """
    if not isinstance(start_time, datetime):
        start_time = _convert_to_datetime(start_time)
    if not isinstance(end_time, datetime):
        end_time = _convert_to_datetime(end_time)
    return end_time - start_time


# json파일을 로드한다.
def _load_json(file_path: str) -> Optional[Union[Dict, Any]]:
    """
    JSON 파일을 로드하여 Python 딕셔너리 또는 리스트로 반환합니다.

    :param file_path: JSON 파일의 경로 (예: 'data.json')
    :return: JSON 데이터가 포함된 Python 딕셔너리 또는 리스트
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        print(f"파일을 찾을 수 없습니다: {file_path}")
        return None
    except json.JSONDecodeError:
        print("JSON 파일을 파싱하는 데 실패했습니다.")
        return None


# 올림 함수
def _round_up(value: Union[str, float], step: Union[str, float]) -> float:
    """
    1. 기능 : 주어진 값을 스텝(step) 크기에 맞게 올림 처리하는 함수.
    2. 매개변수
        1) value (Union[str, float]): 올림 처리할 값. 문자열 또는 실수(float)로 입력 가능.
        2) step (Union[str, float]): 올림 기준이 되는 스텝 크기. 문자열 또는 실수(float)로 입력 가능.
    """
    if isinstance(value, str):
        value = float(value)
    if isinstance(step, float):
        step = str(step)
    if isinstance(value, int) or isinstance(step, int):
        raise ValueError(f"type은 str 또는 float 입력해야 함.")

    return float(Decimal(value).quantize(Decimal(step), rounding=ROUND_UP))


# 내림함수
def _round_down(value: Union[str, float], step: Union[str, float]) -> float:
    """
    1. 기능 : 주어진 값을 스텝(step) 크기에 맞게 내림 처리하는 함수.
    2. 매개변수
        1) value (Union[str, float]): 올림 처리할 값. 문자열 또는 실수(float)로 입력 가능.
        2) step (Union[str, float]): 올림 기준이 되는 스텝 크기. 문자열 또는 실수(float)로 입력 가능.
    """
    # 입력값을 Decimal로 변환 (타입 검증 및 변환 과정)
    if isinstance(value, str):
        value = float(value)
    if isinstance(step, float):
        step = str(step)
    if isinstance(value, int) or isinstance(step, int):
        raise ValueError(f"type은 str 또는 float 입력해야 함.")

    return float(Decimal(value).quantize(Decimal(step), rounding=ROUND_DOWN))


# json타입으로 데이터를 저장한다.
def _save_to_json(file_path: str, new_data: Any, overwrite: bool = False):
    """
    1. 기능 : 데이터를 json으로 덮어쓰거나, 추가 누적해서 저장한다.
    2. 매개변수
        1) file_path : 파일 저장 위치
        2) new_data : 저장하고자 하는 데이터
        3) overwrite : 덮어쓰기 여부
    """
    # 덮어쓰기 여부에 따라 동작
    if overwrite:
        # 덮어쓰는 경우: 기존 데이터를 무시하고 새 데이터로 파일 작성
        data_to_save = new_data if not isinstance(new_data, list) else new_data
    else:
        # 누적 저장의 경우: 기존 데이터를 로드하거나 빈 리스트 초기화
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as file:
                try:
                    existing_data = json.load(file)
                    if not isinstance(existing_data, list):
                        raise ValueError("JSON 파일의 데이터가 리스트가 아닙니다.")
                except (json.JSONDecodeError, ValueError):
                    existing_data = []
        else:
            existing_data = []

        # 기존 데이터에 새 데이터를 추가
        if isinstance(new_data, list):
            existing_data.extend(new_data)
        else:
            existing_data.append(new_data)

        data_to_save = existing_data

    # JSON 파일에 저장
    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data_to_save, file, ensure_ascii=False, indent=4)


# ANSI 코드를 사용하여 콘솔 줄 전체를 지운 후 상태를 출력한다.
def _std_print(message: str):
    """
    1. 기능: ANSI 코드를 사용하여 콘솔 줄 전체를 지운 후 상태를 출력한다.
    2. 매개변수:
        1) message (str): 출력할 문자열 메시지.
    3. 반환값: 없음.
    4. 오류 검증 기능: 해당 없음.
    """
    # ANSI 코드로 줄 전체 지우기
    formatted_message = pformat(message, indent=2, width=80)

    sys.stdout.write("\033[K")  # 현재 줄의 내용을 지움
    sys.stdout.write(f"\r{message}")  # 커서를 줄의 시작으로 이동 후 메시지 출력
    sys.stdout.flush()


def _convert_kline_data_array(kline_data: Dict) -> Dict[str, Dict[str, np.ndarray]]:
    result = {}
    for symbol, kline_data_symbol in kline_data.items():
        if not isinstance(kline_data_symbol, dict) or not kline_data_symbol:
            raise ValueError("kline data가 유효하지 않음.")
        result[symbol] = {}
        for interval, kline_data_interval in kline_data_symbol.items():
            if (
                not isinstance(kline_data_interval, Union[List, np.ndarray])
                or not kline_data_interval
            ):
                raise ValueError("kline data가 유효하지 않음.")
            result[symbol][interval] = np.array(
                object=kline_data_interval, dtype=np.float64
            )
    return result


def _get_interval_ms_seconds(interval: str):
    INTERVAL_MS_SECONDS: Final[dict] = {
        "1m": 60_000,
        "3m": 180_000,
        "5m": 300_000,
        "15m": 900_000,
        "30m": 1_800_000,
        "1h": 3_600_000,
        "2h": 7_200_000,
        "4h": 14_400_000,
        "6h": 21_600_000,
        "8h": 28_800_000,
        "12h": 43_200_000,
        "1d": 86_400_000,
        "3d": 259_200_000,
        "1w": 604_800_000,
        "1M": 2_592_000_000,
    }
    if not interval in INTERVAL_MS_SECONDS:
        raise ValueError(f"interval 값이 유효하지 않음: {interval}")
    return INTERVAL_MS_SECONDS[interval]
