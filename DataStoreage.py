import utils
from typing import List, Union


class KlineData:
    """
    Binance에서 수신한 KlineData를 interval별 저장하기 위한 class __slots__형태의 데이터 타입

    사용시 Dict 타입으로 사용이 필요하며 그 예시는 아래와 같다.
        ### 초기 세팅
            >> data = {}
            >> kline_data = List[List[Union[int, str]]] 형태의 구성
            >> data['BTCUSDT'] = KlineData()
            >> data['BTCUSDT'].initialize_data(kline_data)

        ### 데이터 업데이트
            >> latest_data = kline_data[-1] 최종 데이터
            >> data['BTCUSDT'].update_entry(latest_data)

        ### 데이터 초기화
            >> data['BTCUSDT'].reset_data()

    본 class에 저장된 데이터를 활용하기 위하여 np.ndarray(object=data, dtype=float)처리가 필요하다.
    """

    __slots__ = [f"interval_{interval}" for interval in utils._info_kline_intervals()]

    def __init__(self):
        # 슬롯 초기화
        for interval in self.__slots__:
            setattr(self, interval, [])

    def __map_interval(self, latest_entry: List[Union[int, str]]) -> str:
        """
        주어진 Kline 엔트리에 적합한 interval 이름 반환.
        """
        close_time_index: int = 6
        open_time_index: int = 0
        ms_adjustment: int = 1
        ms_minute: int = 60_000
        
        start_timestamp: int = int(latest_entry[open_time_index])
        end_timestamp: int = int(latest_entry[close_time_index])
        if not (isinstance(start_timestamp, int) and isinstance(end_timestamp, int)):
            raise ValueError(f"kline_data 데이터 형태 불일치")

        timestamp_diff_minutes: int = (
            end_timestamp - start_timestamp + ms_adjustment
        ) // ms_minute

        return {
            1: "interval_1m",
            3: "interval_3m",
            5: "interval_5m",
            15: "interval_15m",
            30: "interval_30m",
            60: "interval_1h",
            120: "interval_2h",
            240: "interval_4h",
            360: "interval_6h",
            480: "interval_8h",
            720: "interval_12h",
            1_440: "interval_1d",
            4_320: "interval_3d",
            10_080: "interval_1w",
        }.get(timestamp_diff_minutes, "interval_1M")

    def initialize_data(self, kline_data: List[List[Union[int, str]]]):
        """
        kline_data초기 자료를 저장한다.
        """
        if not isinstance(kline_data, list) or not kline_data:
            raise ValueError("Invalid kline_data: Must be a non-empty list")

        latest_entry: List[Union[int, str]] = kline_data[-1]
        interval_name: str = self.__map_interval(latest_entry)

        setattr(self, interval_name, kline_data)

    def update_data(self, kline_data_latest: List[Union[int, str]]):
        """
        최신 Kline 데이터를 업데이트.
        """
        if not isinstance(kline_data_latest, list):
            raise ValueError("Invalid latest_entry: Must be a list")

        interval_name: str = self.__map_interval(kline_data_latest)
        interval_data: List[List[Union[int, str]]] = getattr(self, interval_name)

        # 데이터가 없는 경우
        if not interval_data:
            interval_data.append(kline_data_latest)
            # print("Interval 리스트가 비어 있어 데이터를 추가합니다.")
            return

        # 기존 데이터와 비교
        latest_start_time: int = int(kline_data_latest[0])
        latest_end_time: int = int(kline_data_latest[6])

        current_start_time: int = int(interval_data[-1][0])
        current_end_time: int = int(interval_data[-1][6])

        if (
            latest_start_time == current_start_time
            and latest_end_time == current_end_time
        ):
            interval_data[-1] = kline_data_latest
            # print("기존 데이터를 업데이트했습니다.")
        else:
            interval_data.append(kline_data_latest)
            # print("새로운 데이터를 추가했습니다.")

    def get_data(self, interval:str) -> List[List[Union[int, str]]]:
        return getattr(self, f'interval_{interval}')

    def reset_data(self):
        """
        모든 슬롯 데이터를 초기화 (빈 리스트로 재설정).
        """
        for interval in self.__slots__:
            setattr(self, interval, [])
        # print("모든 데이터를 초기화했습니다.")


# class TradeLog:
