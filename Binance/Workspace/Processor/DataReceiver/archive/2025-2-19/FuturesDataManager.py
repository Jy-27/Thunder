import concurrent.futures
import threading
import asyncio
import time
from .BaseDataManager import WebsocketReceiver
from typing import List, Dict

import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming
import Utils.BaseUtils as base_utils


class KlineDataManager(WebsocketReceiver):
    def __init__(
        self,
        ws_receiver,
        real_time_storage,
        history_storage,
        market_fetcher,
        workers=3,
        kline_limit: int = Streaming.kline_limit,
    ):
        super().__init__(ws_receiver)  # , symbols, intervals)
        self.real_time_storage = real_time_storage  # 웹소켓 데이터 최근값 저장용
        self.history_storage = history_storage  # kline data 저장용
        self.market_fetcher = market_fetcher  # kline data 수신용
        self.symbols = self.ws_receiver.symbols
        self.intervals = self.ws_receiver.intervals
        self.workers = workers
        self.kline_limit = kline_limit

        self._threading_kline_update(self.symbols, self.intervals, self.kline_limit)

    def _update_kline_data(self, symbol: str, interval: str, limit: int):
        """
        👻 kline history를 수신 후 storage에 저장한다._summary_

        Args:
            symbol (str): 단일 심볼값
            interval (str): 단일 interval값
            limit (int): 데이터 수신량 (max: 1,000)

        Return:
            수신 데이터 반환.
        """
        data = self.market_fetcher.fetch_klines_limit(symbol, interval, limit)
        self.history_storage.update_data(symbol, *(interval, data))
        return data

    def _threading_kline_update(self, symbols: List, intervals: List, limit: int):
        """
        👻 kline data 수신을 쓰레딩으로 실행한다.

        Args:
            symbols (List): 수신할 심볼 종류
            intervals (List): 수신할 interval 종류
            limit (int): 데이터 수신량 (max: 1,000)
        """
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=min(self.workers, self.MAX_WORKERS)
        ) as executor:
            futures = [
                executor.submit(
                    self._update_kline_data, symbol, interval, self.kline_limit
                )
                for symbol in self.symbols
                for interval in self.intervals
            ]
            concurrent.futures.wait(futures)

    def run_kline_cycle(self, interval_minutes: int = 1):
        """Kline 데이터를 주기적으로 가져오는 함수"""
        valid_intervals = [
            interval
            for interval in self.intervals
            if base_utils.is_time_match(interval)
        ]
        if valid_intervals:
            self._threading_kline_update(
                self.symbols, valid_intervals, self.kline_limit
            )

    # def start_threading(self):
    #     t = threading.Thread(target=self.run_kline_cycle, args=(1,))
    #     t.start()

    def storage_update(self):
        data = await self.ws_receiver.asyncio_queue.get()
        kline_data = data["k"]
        symbol = kline_data["s"]
        interval = kline_data["i"]
        self.real_time_storage.update_data(symbol, interval, data)


    async def start_async_tasks(self):
        t1 = asyncio.create_task(self.kline_limit_run())
        t2 = asyncio.create_task(self.run_real_storage_update())
        await asyncio.gather(t2, t1)

    def start(self):
        print(f"💻 DataManager 실행: {base_utils.get_current_time()}")
        asyncio.run(self.start_async_tasks())
        self.start_threading()
        print("잘된다.!!!")


if __name__ == "__main__":
    """적용예시
    최상위 프로젝트 폴더에서 실행할 것.
    """
    import SystemConfig
    import Services.Receiver.FuturesWebsocketReceiver as futures_ws_receiver
    import Processor.DataStorage.DataStorage as storage
    import Services.PublicData.FuturesMarketFetcher as futures_market

    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals

    ins_futures_market = futures_market.FuturesMarketFetcher()
    ins_ws_receiver = futures_ws_receiver.FuturesWebsocketReceiver(symbols, intervals)
    real_time_storage = storage.SymbolStorage(storage.IntervalStorage)
    history_storage = storage.SymbolStorage(storage.IntervalStorage)

    data_manager = KlineDataManager(
        ins_ws_receiver,
        real_time_storage,
        history_storage,
        ins_futures_market,
        workers=5,
    )
    data_manager.run()
