import ast
import datetime
import asyncio
from typing import Optional, TypeVar, Union, Final, Dict, List, Union


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
    try:
        return ast.literal_eval(input_value)
    except:
        return input_value


# 반환된 데이터를 리터럴값 반영
def _collections_to_literal(input_data: List[Dict[str, Union[str, int, float, bool]]]):
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
async def _wait_until_next_interval(time_unit: str, interval: int) -> datetime.datetime:
    """
    1. 기능 : 다음 지정 간격까지 대기
    2. 매개변수
        1) time_unit : 'hour', 'minute', 'second'
    """
    valid_intervals = _calculate_divisible_intervals(time_unit=time_unit)
    if interval not in valid_intervals:
        raise ValueError(f"잘못된 간격 입력: {valid_intervals} 중 하나를 선택하십시오.")

    # 시간 단위에 따른 최대값 설정 ('hour'는 24, 그 외는 60)
    max_step = 24 if time_unit == "hour" else 60

    while True:
        # 현재 시각 가져오기
        current_time = datetime.datetime.now()
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


# 지정된 시간 동안 대기 (timesleep 시간 버전)
async def _wait_time_sleep(time_unit: str, duration: int) -> datetime.datetime:
    """
    1. 기능 : 지정된 시간 동안 대기
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

    return datetime.datetime.now()


# 다음 정각까지 대기 (0초 return 발생)
async def _wait_until_exact_time(time_unit: str) -> datetime.datetime:
    """
    1. 기능 : time_unit기준 정각까지 대기
    2. 매개변수
        1) time_unit : 시간 종류
            >> 'second' : 초
            >> 'minute' : 분
            >> 'hour' : 시간
    """
    now = datetime.datetime.now()

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
    return datetime.datetime.now()


# 현재시간을 확보한다.
def _get_time_component(
    time_unit: Optional[str] = None,
) -> Union[int, datetime.datetime]:
    """
    1. 기능 : 현재시간을 반환한다.
    2. 매개변수
        1) time_unit : 시간 종류
            >> 'second' : 초
            >> 'minute' : 분
            >> 'hour' : 시간
    """
    current_time = datetime.datetime.now()
    if time_unit:
        unit_value = {
            "hour": current_time.hour,
            "minute": current_time.minute,
            "second": current_time.second,
        }.get(time_unit)
        if unit_value is None:
            raise ValueError(f"time_unit 입력 오류. {time_unit}")
        return unit_value
    return current_time

# 문자형 시간 또는 datetime.datetime 형태 타입 변수를 밀리초 timestampe로 변환 및 반환.
def _convert_to_timestamp_ms(date: Union[str, datetime.datetime]) -> int:
    """
    1. 기능 : 문자형 시간 또는 datetime.datetime형태의 변수를 밀리초 timestamp로 변환 및 반환
    2. 매개변수
        1) date : str(예 : 2024-01-01 17:14:00) 또는 datetime.datetime형태의 시간 문자열
    """

    MS_SECOND = 1000  # 밀리초 변환을 위한 상수

    if isinstance(date, datetime.datetime):
        return int(date.timestamp() * MS_SECOND)
    else:
        return int(
            datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").timestamp()
            * MS_SECOND
        )

# 문자열 시간을 datetime 형태로로 변환 및 반환.
def _convert_to_datetime(date: Union[str, datetime.datetime, int]) -> datetime.datetime:
    """
    1. 기능 : 문자형 시간 또는 datetime.datetime형태의 변수를 밀리초 timestamp로 변환 및 반환
    2. 매개변수
        1) date : str(예 : 2024-01-01 17:14:00)형태 변수
    """

    MS_SECOND = 1000  # 밀리초 변환을 위한 상수

    if isinstance(date, datetime.datetime):
        return date
    elif isinstance(date, int):
        return datetime.datetime.fromtimestamp(date / 1000)
    elif isinstance(date, str):
        return datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")