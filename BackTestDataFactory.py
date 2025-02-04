import os
import utils
import asyncio
import numpy as np
import pickle
from typing import Union, List, Dict, Any
import ConfigSetting
import Analysis_new

class FactoryManager:
    """
    백테스트에 사용될 데이터를 수집 및 가공 편집한다. kline_data를 수집 후 np.array처리하며, index를 위한 데이터도 생성한다.
    """
    def __init__(self):
        # str타입을 list타입으로 변형한다.
        self.symbols = ConfigSetting.TestConfig.test_symbols.value
        self.intervals = ['1m'] + Analysis_new.Intervals.intervals if ['1m'] not in Analysis_new.Intervals.intervals else Analysis_new.Intervals.intervals

        # KlineData 다운로드할 기간. str(YY-MM-DD HH:mm:dd)
        self.start_date: str = ConfigSetting.TestConfig.start_datetime.value
        self.end_date: str = ConfigSetting.TestConfig.end_datetime.value

    # def create_dummy_signal(self, signal_type:str):

    # 장기간 kline data수집을 위한 date간격을 생성하여 timestamp형태로 반환한다.
    def __generate_timestamp_ranges(
        self, interval: str, start_date: str, end_date: str
    ) -> List[List[int]]:
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date

        # 시작 및 종료 날짜 문자열 처리
        # 시간 정보는 반드시 00:00:00 > 23:59:59로 세팅해야 한다. 그렇지 않을경우 수신에 문제 발생.
        start_date = start_date  # + " 00:00:00"
        end_date = end_date  # + " 23:59:59"

        # interval에 따른 밀리초 단위 스텝 가져오기
        interval_step = utils._get_interval_ms_seconds(interval)

        # Limit 값은 1,000이나 유연한 대처를 위해 999 적용
        MAX_LIMIT = 1_000

        # 시작 타임스탬프
        start_timestamp = utils._convert_to_timestamp_ms(date=start_date)
        # interval 및 MAX_LIMIT 적용으로 계산된 최대 종료 타임스탬프

        if interval_step is not None:
            max_possible_end_timestamp = (
                start_timestamp + (interval_step * MAX_LIMIT) - 1
            )
        else:
            raise ValueError(f"interval step값 없음 - {interval_step}")
        # 지정된 종료 타임스탬프
        end_timestamp = utils._convert_to_timestamp_ms(date=end_date)

        # 최대 종료 타임스탬프가 지정된 종료 타임스탬프를 초과하지 않을 경우
        if max_possible_end_timestamp >= end_timestamp:
            return [[start_timestamp, end_timestamp]]
        else:
            # 초기 데이터 설정
            initial_range = [start_timestamp, max_possible_end_timestamp]
            timestamp_ranges = [initial_range]

            # 반복문으로 추가 데이터 생성
            while True:
                # 다음 시작 및 종료 타임스탬프 계산
                next_start_timestamp = timestamp_ranges[-1][1] + 1
                next_end_timestamp = (
                    next_start_timestamp + (interval_step * MAX_LIMIT) - 1
                )

                # 다음 종료 타임스탬프가 지정된 종료 타임스탬프를 초과할 경우
                if next_end_timestamp >= end_timestamp:
                    final_range = [next_start_timestamp, end_timestamp]
                    timestamp_ranges.append(final_range)
                    return timestamp_ranges

                # 그렇지 않을 경우 범위 추가 후 반복
                else:
                    new_range = [next_start_timestamp, next_end_timestamp]
                    timestamp_ranges.append(new_range)
                    continue

    # 각 symbol별 interval별 지정된 기간동안의 kline_data를 수신 후 dict타입으로 묶어 반환한다.
    async def generate_kline_interval_data(
        self,
        symbols: Union[str, list, None] = None,
        intervals: Union[str, list, None] = None,
        start_date: Union[str, None] = None,
        end_date: Union[str, None] = None,
        save: bool = True,
    ):
        """
        1. 기능 : 장기간 kline data를 수집한다.
        2. 매개변수
            1) symbols : 쌍거래 심볼 리스트
            2) intervals : interval 리스트
            3) start_date : 시작 날짜 (년-월-일 만 넣을것.)
            4) end_date : 종료 날짜 (년-월-일 만 넣을것.)
            5) save : 저장여부
        3. 추가설명
            self.__generate_timestamp_ranges가 함수내에 호출됨.
        """
        
        # 지연임포트
        import MarketDataFetcher
        ins_market = {'Futures':MarketDataFetcher.FuturesMarket(),
                      'Spot':MarketDataFetcher.SpotMarket()}.get(ConfigSetting.SymbolConfig.market_type.value, None)
        if ins_market is None:
            raise ValueError(f'instance 로딩 오류')

        # 기본값 설정
        # API 호출 제한 설정
        MAX_API_CALLS_PER_MINUTE = 1150
        API_LIMIT_RESET_TIME = 60  # 초 단위

        api_call_count = 0
        # start_time = datetime.datetime.now()
        aggregated_results: Dict[str, Dict[str, List[Any]]] = {}

        for symbol in self.symbols:
            aggregated_results[symbol] = {}

            for interval in self.intervals:
                aggregated_results[symbol][interval] = []
                timestamp_ranges = self.__generate_timestamp_ranges(
                    interval=interval, start_date=start_date, end_date=end_date
                )

                collected_data:List[Any] = []
                for timestamps in timestamp_ranges:
                    # 타임스탬프를 문자열로 변환
                    start_timestamp_str = utils._convert_to_datetime(timestamps[0])
                    end_timestamp_str = utils._convert_to_datetime(timestamps[1])

                    # Kline 데이터 수집
                    kline_data = await ins_market.fetch_klines_date(
                        symbol=symbol,
                        interval=interval,
                        start_date=start_timestamp_str,
                        end_date=end_timestamp_str,
                    )
                    collected_data.extend(kline_data)

                # API 호출 간 간격 조정
                await asyncio.sleep(0.2)
                aggregated_results[symbol][interval] = collected_data

        if save:
            path = ConfigSetting.SystemConfig.path_kline_data.value
            utils._save_to_json(
                file_path=path, new_data=aggregated_results, overwrite=True
            )
        return aggregated_results

    # 생성한 closing_sync_data를 interval index데이터를 구성한다.(전체)
    def __generate_full_indices(self, closing_sync_data):
        # symbols를 획득
        symbols = list(closing_sync_data.keys())
        # Intervals를 획득
        intervals = list(closing_sync_data[symbols[0]])
        # 기본 데이터를 지정
        base_data = closing_sync_data[symbols[0]]
        # 마지막 index값 조회
        max_index = len(base_data[intervals[0]])

        # 인덱스 데이터를 저장할 자료를 초기화
        indices_data = {}
        # interval 루프
        for interval in intervals:
            # interval별 miute를 활용하여 step으로 지정
            interval_step = utils._get_interval_minutes(interval)
            # arange를 통해서 interval의 기준 index 지정.
            indices_data[interval] = np.arange(
                start=0, stop=max_index, step=interval_step
            )
        # 결과 반환.
        return indices_data

    # 1분봉 종가 가격을 각 interval에 반영한 테스트용 더미 데이터를 생성한다.
    def generate_kline_closing_sync(
        self, kline_data: Dict, save: bool = False
    ) -> Dict[str, Dict[str, np.ndarray]]:
        """
        1. 기능 : 백테스트시 데이터의 흐름을 구현하기 위하여 1분봉의 누적데이터를 반영 및 1분봉의 길이와 맞춘다.
        2. 매개변수
            1) kline_data : kline_data 를 numpy.array화 하여 적용
            2) save : 생성된 데이터 저장여부.

        3. 처음부터 인터별간 데이터의 길이는 다르지만, open_timestamp와 end_timestamp가 일치한다. kline_data수신기에는 이상이 없다.
            dummy_data가 불필요하다는 소리....해당 함수를 완전 재구성해야한다. 그동안 잘못된 데이터로 백테스를 수행하였다. 데이터의 신뢰성을
            먼저 확보해야만 한다.
        """

        # 심볼 및 interval 값을 리스트로 변환
        symbols_list = list(kline_data.keys())
        intervals_list = list(kline_data[symbols_list[0]].keys())
        closing_sync_data = {}

        ##=---=####=---=####=---=####=---=####=---=####=---=##
        # =-=###=----=###=---=# P O I N T #=---=###=----=###=-#
        ##=---=####=---=####=---=####=---=####=---=####=---=##
        ### indices의 arange(step)기능의 오점을 개선하고자 첫번째 데이터는 더미데이터를 넣는다.
        data_lengh = len(kline_data[symbols_list[0]][intervals_list[0]][0])
        dummy_data = [0 for _ in range(data_lengh)]

        for symbol in symbols_list:
            for interval in intervals_list:
                # print(type(kline_data[symbol][interval]))
                kline_data[symbol][interval].insert(0, dummy_data)

        kline_array = utils._convert_to_array(kline_data)

        ### np.ndarray로 구성된 dict자료형태를 Loop 순환 ###
        for symbol, symbol_data in kline_array.items():
            closing_sync_data[symbol] = {}

            ### base data 생성(각 symbol별 첫번째 interval값 기준 ###
            base_data = symbol_data[
                self.intervals[0]
            ]  # 첫번재 index데이터값 기준으로 생성함.

            ### interval Loop 대입 ###
            for interval in self.intervals:
                ### interval 첫번재 index값은 continue처리한다.(base_data값은 위에 선언 했으므로)
                if interval == self.intervals[0]:
                    closing_sync_data[symbol][interval] = base_data
                    continue

                timestamp_range = utils._get_interval_ms_seconds(interval) - 1
                ### 목표 interval 데이터값을 조회한다.###
                interval_data = kline_array[symbol][interval]

                ### 데이터를 저장할 임시 변수를 초기화 한다. ###
                temp_data = []

                ### base data를 활용하여 index를 구현하고, index별 데이터를 순환한다.###
                for index, data in enumerate(base_data):
                    open_timestamp = data[0]  # 시작 타임스템프
                    open_price = data[1]  # 시작 가격
                    high_price = data[2]  # 최고 가격
                    low_price = data[3]  # 최저 가격
                    close_price = data[4]  # 마지막 가격
                    volume = data[5]  # 거래량(단위 : coin)
                    close_timestamp = data[6]  # 종료 타임스템프
                    volume_total_usdt = data[7]  # 거래량(단위 : usdt)
                    trades_count = data[8]  # 총 거래횟수
                    taker_asset_volume = data[9]  # 시장가 주문 거래량(단위 : coin)
                    taker_quote_volume = data[10]  # 시장가 주문 거래량(단위 : usdt)

                    ### base_data가 적용되는 interval_data의 index값을 확보한다.
                    condition = np.where(
                        (interval_data[:, 0] <= open_timestamp)
                        & (interval_data[:, 6] >= close_timestamp)
                    )

                    ### interval 전체 데이터에서 해당 interval 데이터만 추출한다. ###
                    ### 용도는 start_timestap / end_timestamp추출 및 new_data에 적용을 위함. ###
                    target_data = interval_data[condition]
                    # print(target_data)

                    target_open_timestamp = target_data[0, 0]  # 단일값이 확실할 경우
                    target_close_timestamp = target_data[0, 6]  # 단일값이 확실할 경우

                    new_data_condition = np.where(
                        (base_data[:, 0] >= target_open_timestamp)
                        & (base_data[:, 6] <= close_timestamp)
                    )  # close_timestamp는 현재 data종료 시간 기준으로 해야한다.

                    new_base_data = base_data[new_data_condition]

                    timestamp_diff = new_base_data[-1, 6] - new_base_data[0, 0]
                    if timestamp_range == timestamp_diff:
                        new_data = target_data[0]
                    else:
                        new_data = [
                            target_open_timestamp,
                            new_base_data[0, 1],
                            np.max(new_base_data[:, 2]),
                            np.min(new_base_data[:, 3]),
                            new_base_data[-1, 4],
                            np.sum(new_base_data[:, 5]),
                            target_close_timestamp,
                            np.sum(new_base_data[:, 7]),
                            np.sum(new_base_data[:, 8]),
                            np.sum(new_base_data[:, 9]),
                            np.sum(new_base_data[:, 10]),
                            0,
                        ]
                    temp_data.append(new_data)
                closing_sync_data[symbol][interval] = np.array(temp_data, float)
        if save:
            path = ConfigSetting.SystemConfig.path_closing_sync_data.value
            with open(file=path, mode="wb") as file:
                pickle.dump(closing_sync_data, file)
        return closing_sync_data

    # generate_kline_closing_sync index 자료를 생성한다.
    def get_indices_data(
        self,
        closing_sync_data: Dict[str, Dict[str, np.ndarray]],
        lookback_days: int = 2,
    ) -> DataStoreage.DataContainer:
        """
        1. 기능 : generate_kline_clsing_sync 데이터의 index를 생성한다.
        2. 매개변수
            1) data_container : utils모듈에서 사용중인 container data
            2) lookback_days : index 데이터를 생성한 기간을 정한다.
        3. 추가설명
            data_container는 utils에서 호출한 instance를 사용한다. params에 적용하면 해당 변수는 전체 적용된다.
            백테스를 위한 자료이며, 실제 알고리즘 트레이딩시에는 필요 없다. 데이터의 흐름을 구현하기 위하여 만든 함수다.
        """
        # 하루의 총 분

        symbols = list(closing_sync_data.keys())
        intervals = list(closing_sync_data[symbols[0]])

        date_range = lookback_days
        timestamp_step = utils._get_interval_minutes("1d") * date_range

        indices_data = self.__generate_full_indices(closing_sync_data)
        base_indices = indices_data[intervals[0]]

        container_data = DataStoreage.DataContainer()

        for interval in intervals:
            select_indices = []
            for current_idx in base_indices:
                reference_data = indices_data[interval]
                start_idx = current_idx - timestamp_step
                if start_idx < 0:
                    start_idx
                condition = np.where(
                    (reference_data[:] >= start_idx)
                    & (reference_data[:] < current_idx)
                )
                indices = indices_data[interval][condition]
                add_indices = np.append(indices, current_idx)
                select_indices.append(add_indices)
            container_data.set_data(
                data_name=f"interval_{interval}", data=select_indices
            )

        return container_data

    # Data Manager 함수를 일괄 실행 및 정리한다.
    async def data_manager_run(self, save: bool = False):
        kline_data = await self.generate_kline_interval_data(save=save)
        kline_data_array = utils._convert_to_array(kline_data=kline_data)
        closing_sync = self.generate_kline_closing_sync(
            kline_data=kline_data_array, save=save
        )
        data_container = utils._convert_to_container(kline_data=closing_sync)
        indices_data = self.get_indices_data(
            data_container=data_container, lookback_days=2, save=save
        )
        return kline_data_array, closing_sync, indices_data
    
if __name__ == "__main__":
    import Analysis_new
    
    obj = FactoryManager()
    kline_data = asyncio.run(obj.generate_kline_interval_data())
    closing_sync_data = obj.generate_kline_closing_sync(kline_data=kline_data, save=True)
    closing_indices_data = obj.get_indices_data(closing_sync_data=closing_sync_data,
                                                lookback_days=ConfigSetting.SystemConfig.data_analysis_window_days.value)