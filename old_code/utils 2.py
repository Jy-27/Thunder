import ast
import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Optional, TypeVar, Union, Final, Dict, List, Union, Any
from decimal import Decimal, ROUND_UP, ROUND_DOWN

T = TypeVar("T")


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
def _convert_to_datetime(date: Union[str, datetime, int]) -> datetime:
    """
    1. 기능 : 문자형 시간 또는 datetime형태의 변수를 밀리초 timestamp로 변환 및 반환
    2. 매개변수
        1) date : str(예 : 2024-01-01 17:14:00)형태 변수
    """

    MS_SECOND = 1000  # 밀리초 변환을 위한 상수

    if isinstance(date, datetime):
        return date
    elif isinstance(date, int):
        return datetime.fromtimestamp(date / 1000)
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


# # 올림함수
# def _round_up(value: Union[str, float], step: Union[str, float]) -> float:
#     """
#     1. 기능 : 주어진 값을 스텝(step) 크기에 맞게 올림 처리하는 함수.
#     2. 매개변수
#         1) value (Union[str, float]): 올림 처리할 값. 문자열 또는 실수(float)로 입력 가능.
#         2) step (Union[str, float]): 올림 기준이 되는 스텝 크기. 문자열 또는 실수(float)로 입력 가능.
#     """
#     # 입력값을 Decimal로 변환 (타입 검증 및 변환 과정)
#     try:
#         value = Decimal(value)  # value를 Decimal로 변환
#         step = Decimal(step)    # step을 Decimal로 변환
#     except (ValueError, TypeError):
#         raise ValueError("value와 step은 문자열(str) 또는 실수(float)로 변환 가능한 값이어야 합니다.")

#     # Decimal의 quantize 메서드를 사용해 올림 처리
#     return float(value.quantize(step, rounding=ROUND_UP))


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
        data_to_save = [new_data] if not isinstance(new_data, list) else new_data
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
    sys.stdout.write("\033[K")  # 현재 줄의 내용을 지움
    sys.stdout.write(f"\r{message}")  # 커서를 줄의 시작으로 이동 후 메시지 출력
    sys.stdout.flush()