from typing import List, Dict, Optional, Any
import numpy as np
import asyncio
import os, sys
import pickle

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig
from Workspace.BackTest.Storage.StorageCollector import (
    ClosingSyncStorage,
    IndicesStorage,
)

ins_market_fetcher = FuturesMarketFetcher()


class FactoryManager:
    """
    백테스트에 사용할 시계열 데이터를 생성한다.
    """
    def __init__(self, start_date: str, end_date: str):
        self.symbol: List[str] = SystemConfig.Streaming.symbols
        self.base_interval: str = "1m"

        # 기존 intervals 리스트를 수정하지 않고 새로운 리스트로 할당
        self.intervals: List[str] = (
            [self.base_interval] + SystemConfig.Streaming.intervals
            if self.base_interval not in SystemConfig.Streaming.intervals
            else SystemConfig.Streaming.intervals
        )
        self.start_date = start_date + " 09:00:00"
        self.end_date = end_date + " 08:59:59"

        self.path_test_storage = os.path.join(home_path, "github", "TestData")
        self.path_closing = os.path.join(self.path_test_storage, "closing.pkl")
        self.path_indices = os.path.join(self.path_test_storage, "indices.pkl")

        self.storage_closing = ClosingSyncStorage()
        self.storage_indices = IndicesStorage()

    def _generate_timestamp_ranges(
        self,
        interval: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[List[int]]:
        """
        👻 kline date를 수신하기 위하여 start timestam, end timestamp를 구간별로 생성한다. 최대 수신량이 1,000개 이므로
        본 함수를 통해서 전체 기간을 분리하여 수신할 수 있도록 timestamp를 분리 한다.

        Args:
            interval (str): interval 값
            start_date (Optional[str], optional): 시작 날짜
            end_date (Optional[str], optional): 종료 날짜

        Raises:
            ValueError: interval 값 오입력시

        Returns:
            List[List[int]]: timestamp 값
        """
        start_date = self.start_date if start_date is None else start_date + " 09:00:00"
        end_date = self.end_date if end_date is None else end_date + " 08:59:59"

        interval_step = base_utils.get_interval_ms_seconds(interval)
        if interval_step is None:
            raise ValueError(f"interval step값 없음 - {interval_step}")

        MAX_LIMIT = 900
        start_ts = base_utils.convert_to_timestamp_ms(date=start_date)
        end_ts = base_utils.convert_to_timestamp_ms(date=end_date)

        timestamp_ranges = []
        while start_ts < end_ts:
            next_end_ts = min(start_ts + interval_step * MAX_LIMIT - 1, end_ts)
            timestamp_ranges.append([start_ts, next_end_ts])
            start_ts = next_end_ts + 1

        return timestamp_ranges

    def __prepend_placeholder(self, table: List[List[Any]]) -> List[List[Any]]:
        """
        👻 closing sync data 활용에 필요한 배열을 맞추기 위해 첫번째 index 데이터에 dummy값을 삽입한다.

        Args:
            table (List[List[Any]]): kline data

        Returns:
            List[List[Any]]: dummy 데이터 삽입된 kline data
        """
        num_fields = len(table[0])  # 첫 번째 행의 필드 개수
        placeholder_row = [0] * num_fields  # 0으로 채운 자리 맞춤 행 생성

        table.insert(0, placeholder_row)  # 첫 번째 위치에 삽입
        return table  # 수정된 리스트 반환

    async def fetch_klines(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        📨 symbol의 interval 값에 맞추어 지정가간동안의 kline data를 수신한다.

        Args:
            symbol (Optional[str], optional): 수신할 데이터 심볼값
            interval (Optional[str], optional): 수신할 데이터 interval 값
            start_date (Optional[str], optional): 데이터 시작 날짜
            end_date (Optional[str], optional): 데이터 종료 날짜

        Returns:
            List: 수신데이터 값
        """
        symbol = symbol if symbol is not None else self.symbol
        result = {}

        kline_data = []
        timestamp_range = self._generate_timestamp_ranges(
            interval, start_date, end_date
        )
        for start_timestamp, end_timesatmp in timestamp_range:
            fetch_data = await ins_market_fetcher.fetch_klines_date(
                symbol, interval, start_timestamp, end_timesatmp
            )
            kline_data.extend(fetch_data)
            await asyncio.sleep(0.2)
        key = f"{symbol}_{interval}"
        print(f"  📨 {key} 수신 완료")
        result[key] = kline_data
        return result

    def _parse_kline_data(
        self, data: List[List[Dict[str, Any]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        👻 kline data를 Dict형태로 변환한다.

        Args:
            data (List[List[Dict[str, Any]]]): fetch_multiple_klines 결과물

        Returns:
            Dict[str, Dict[str, Any]]: dict형태로 재구성
        """
        result = {}

        for i in data:
            for key, value in i.items():
                symbol, interval = key.split("_")  # 심볼과 인터벌 분리

                result.setdefault(symbol, {})  # 존재하지 않으면 초기화
                result[symbol][interval] = value  # 값 할당
        return result

    async def fetch_multiple_klines(
        self,
        symbols: List,
        intervals: List,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ):
        """
        📨 fetch_klines method을 활용하여 동시에 여러개 데이터를 비동기식으로 수신한다.

        Args:
            symbols (List): symbol 종류
            intervals (List): interval 종류
            start_date (Optional[str], optional): 시작 날짜
            end_date (Optional[str], optional): 종료 날짜

        Returns:
            _type_: _description_
        """
        tasks = []
        for symbol in symbols:
            for interval in intervals:
                tasks.append(
                    asyncio.create_task(
                        self.fetch_klines(symbol, interval, start_date, end_date)
                    )
                )
        result = await asyncio.gather(*tasks)
        return result

    def process_for_analysis(self, kline_dataset: List) -> Dict:
        """
        비동기식으로 수신한 데이터를 분석가능한 상태로 변환한다. symbol, interval 별로 재구성하고 더미데이터를 추가한다.
        그리고 numpy.array화 한다.

        Args:
            kline_dataset (Dict): _description_

        Returns:
            Dict: _description_
        """
        data = self._parse_kline_data(kline_dataset)
        result = {}
        for symbol, values in data.items():
            result.setdefault(symbol, {})
            for interval, value in values.items():
                result[symbol][interval] = np.array(
                    self.__prepend_placeholder(value), float
                )
        return result

    def _prepend_placeholder(self, table: List[List[Any]]) -> List[List[Any]]:
        """
        👻 kline 데이터 첫번째 인덱스에 더미 데이터를 삽입하다. index배열을 맞추기 위함이다.

        Args:
            table (List[List[Any]]): kline data interval 데이터

        Returns:
            List[List[Any]]: 더미데이터 추가된 interval data
        """
        num_fields = len(table[0])  # 첫 번째 행의 필드 개수
        placeholder_row = [0] * num_fields  # 0으로 채운 자리 맞춤 행 생성

        table.insert(0, placeholder_row)  # 첫 번째 위치에 삽입
        return table  # 수정된 리스트 반환

    def generate_indices_arange(self, interval: str, data: np.ndarray):
        """
        kline data의 특정 index값을 확보한다. 주로 1m값의 index를 생성하기 위하여 쓰인다.

        data의 interval별로 index값을 생성한다.

        Args:
            interval (str): interval값
            data (np.ndarray): index생성할 데이터값

        Returns:
            _type_: index값
        """
        step_size = base_utils.get_interval_minutes(interval)
        return np.arange(0, len(data), step_size)  # 불필요한 변수 제거

    def generate_kline_closing_sync(
        self, base_data: np.ndarray, selec_data: np.ndarray, interval: str
    ):
        """
        base data를 기준하여 closing sync data를 생성한다.
        base data의 길이에 맞게 selec_data를 재구성한다. 시계열 데이터를 사용하기 위함이다.

        Args:
            base_data (np.ndarray): 기본 데이터 (1분봉 kline data)
            selec_data (np.ndarray): 대상 데이터 (3분봉 이상 kline data)
            interval (str): interval 값

        Returns:
            _type_: 시계열 데이터 생성(1분)
        """

        result = {}
        timestamp_range = base_utils.get_interval_ms_seconds(interval) - 1
        temp_data = []

        print(f"    ℹ️ 데이터 생성 시작: {interval}")
        
        for (
            open_timestamp,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            close_timestamp,
            volume_total_usdt,
            trades_count,
            taker_asset_volume,
            taker_quote_volume,
            ignore,
        ) in zip(*base_data.T):
            # open_timestamp = 시작 타임스템프
            # open_price = 시작 가격
            # high_price = 최고 가격
            # low_price = 최저 가격
            # close_price = 마지막 가격
            # volume = 거래량(단위 : coin)
            # close_timestamp = 종료 타임스템프
            # volume_total_usdt = 거래량(단위 : usdt)
            # trades_count = 총 거래횟수
            # taker_asset_volume =  시장가 주문 거래량(단위 : coin)
            # taker_quote_volume = 시장가 주문 거래량(단위 : usdt)

            condition = np.where(
                (selec_data[:, 0] <= open_timestamp)
                & (selec_data[:, 6] >= close_timestamp)
            )

            target_data = selec_data[condition]

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
        return np.array(temp_data, float)

    def generate_indices_by_interval(
        self, base_indices, interval: str, lookback_days: int = 1
    ):
        """
        기본 데이터를 활용하여 interval별로 index값들을 생성한다. 해당 값을 활용하여 시계열 데이터를 불러올때 사용한다.

        Args:
            base_indices (_type_): _description_
            interval (str): _description_
            lookback_days (int, optional): _description_. Defaults to 1.

        Returns:
            _type_: _description_
        """
        index_step = base_utils.get_interval_minutes(interval)
        day_step = base_utils.get_interval_minutes("1d") * lookback_days
        result = []
        for current_index in base_indices:
            start_idx = max(current_index - day_step, 0)
            if start_idx == 0:
                continue
            condition = np.where(
                (base_indices >= start_idx)
                & (base_indices < current_index)
                & (base_indices % index_step == 0)
            )
            add_indices = np.append(condition, current_index)
            result.append(np.append(condition, current_index))
        return result

    def storage_save(self):
        """
        storage를 전부 저장한다 (closing, indices)
        """

        if not os.path.isdir(self.path_test_storage):
            os.makedirs(self.path_test_storage)
        with open(self.path_closing, "wb") as f:
            pickle.dump(self.storage_closing, f)
        with open(self.path_indices, "wb") as f:
            pickle.dump(self.storage_indices, f)
        print(f"  ✅ 저장 완료")

    def storage_load(self):
        """
        저장한 스토리지를 불러온다.

        Raises:
            ValueError: 폴더가 존재하지 않을 때
            ValueError: closing 파일이 존재하지 않을 때
            ValueError: indices 파일이 존재하지 않을 때

        Returns:
            _type_: closing, indices 두 storage
        """
        if not os.path.isdir(self.path_test_storage):
            raise ValueError(f"  ⚠️ 폴더가 존재하지 않음: {self.path_test_storage}")
        if not os.path.isfile(self.path_closing):
            raise ValueError(f"  ⚠️  파일이 존재하지 않음: {self.path_closing}")
        if not os.path.isfile(self.path_indices):
            raise ValueError(f"  ⚠️  파일이 존재하지 않음: {self.path_indices}")

        with open(self.path_closing, "rb") as f:
            self.storage_closing = pickle.load(f)
        with open(self.path_indices, "rb") as f:
            self.storage_indices = pickle.load(f)
        print(f"  ✅ Storage 로딩 완료")
        return self.storage_closing, self.storage_indices

    async def start(self, is_save: bool = True):
        dataset = await self.fetch_multiple_klines(self.symbol, self.intervals)
        convert_to_data = self.process_for_analysis(dataset)
        base_data = convert_to_data[self.symbol[0]][self.base_interval]
        print(f"  🚀 데이터 싱크 생성 시작")
        for i in self.intervals:
            selec_data = convert_to_data[self.symbol[0]][i]
            closing_sync_data = self.generate_kline_closing_sync(base_data, selec_data, i)
            self.storage_closing.set_data(i, closing_sync_data)
        print(f"  👍 데이터 싱크 생성 완료")
        base_data = convert_to_data[self.symbol[0]][self.base_interval]
        base_indices = self.generate_indices_arange(self.base_interval, base_data)
        for i in self.intervals:
            indices_data = self.generate_indices_by_interval(base_indices, i, 1)
            
            self.storage_indices.set_data(i, indices_data)
        if is_save:
            self.storage_save()
        return self.storage_closing, self.storage_indices

if __name__ == "__main__":
    start_date = "2025-01-01"  # 09:00:00'
    end_date = "2025-01-30"  # 08:59:59'
    intervals = SystemConfig.Streaming.intervals
    symbols = ["BTCUSDT"]  # , 'ETHUSDT']
    ins = FactoryManager(start_date, end_date)
    closing, indices = asyncio.run(ins.start())
    # closing, indices = ins.storage_load()
    
    
    data_emty = False
    index = 0
    while not data_emty:
    # while True:
        try:
            for i in ins.intervals:
                indices_data = indices.get_data(i, index)
                sync_data = closing.get_data(i, indices_data)
                print(f"  {i} - {indices_data[-1]}")
            index += 1
        except:
            data_emty = True
    
    print(f" ✅ 작업종료")
