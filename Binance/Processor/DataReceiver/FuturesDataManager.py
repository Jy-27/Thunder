import concurrent.futures
import threading
import asyncio

from .BaseDataManager import WebsocketReceiver, KlineHistoryFetcher
from typing import List, Dict

import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming
import Services.PublicData.FuturesMarketFetcher as public_futures
import Services.Receiver.FuturesWebsocketReceiver as ws_futures
import Utils.BaseUtils as base_utils

ins_public_futures = public_futures.FuturesMarketFetcher()
ins_ws_futures = ws_futures.FuturesWebsocketReceiver(symbols=Streaming.symbols, intervals=Streaming.intervals)


class FuturesDataManager(WebsocketReceiver, KlineHistoryFetcher):
    def __init__(
        self,
        real_storage,
        history_storage,
        public_futures: ins_public_futures,
        ws_futures: ins_ws_futures,
        max_workers: int = 3,
    ):
        WebsocketReceiver.__init__(self, ws_futures)
        KlineHistoryFetcher.__init__(
            self, history_storage, public_futures
        )
        self.real_storage = real_storage
        self.max_workers = min(max_workers, self.MAX_WORKERS)

        self.get_kline_data(symbols=self.symbols, intervals=self.intervals)

    def get_kline_data(self, symbols: List, intervals: List):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers
        ) as executor:
            futures = [
                executor.submit(self.run, symbol, interval)
                for symbol in symbols
                for interval in intervals
            ]
            # 모든 작업 완료 대기
            concurrent.futures.wait(futures)

    async def real_storage_update(self):
        print(" 🚀 Real-time storage update started")
        while True:
            if not self.ws_futures.asyncio_queue.empty():
                data = await self.ws_futures.asyncio_queue.get()
                k_data = data["k"]
                symbol = k_data["s"]
                interval = k_data["i"]
                self.real_storage.update_data(
                    symbol=symbol, interval=interval, data=k_data
                )
            else:
                await asyncio.sleep(1)

    def get_kline_cycle(self, interval_minutes: int = 1):
        """Kline 데이터를 주기적으로 가져오는 함수"""
        print(" 🚀 Kline periodic data collection started")
        while True:
            # 유효한 intervals 필터링
            valid_intervals = [
                interval
                for interval in self.intervals
                if base_utils.is_time_match(interval)
            ]

            if valid_intervals:
                self.get_kline_data(symbols=self.symbols, intervals=valid_intervals)

            # 다음 주기까지 대기
            base_utils.sleep_next_minute(minutes=interval_minutes)

    def run_threading(self):
        t = threading.Thread(target=self.get_kline_cycle, args=(1,))
        t.start()
        return t

    async def run_async_tasks(self):
        task_1 = asyncio.create_task(self.kline_limit_run())
        task_2 = asyncio.create_task(self.real_storage_update())
        await asyncio.gather(task_1, task_2)

    def run(self):
        print(f"💻 {base_utils.get_current_time()}")
        self.run_threading()
        asyncio.run(self.run_async_tasks())

if __name__ == "__main__":

    import Processor.DataStorage.DataStorage as storage
    
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_public_futures = public_futures.PublicClient()
    ins_ws_futures = ws_futures.receiverClient(symbols=symbols, intervals=intervals)
    
    real_storage = storage.SymbolStorage()  # 실시간 데이터 수집
    history_storage = storage.SymbolStorage()   # 과거 kline_data 수집
    
    ins_threading = handler.MarketDataHandler(real_storage=real_storage,
                                              history_storage=history_storage,
                                              ins_receiver=ins_ws_futures,
                                              ins_public=ins_public_futures)
    asyncio.run(ins_threading.run())