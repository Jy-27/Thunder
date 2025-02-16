import concurrent.futures
import threading
import asyncio

from .DataHandler import WebSocketManager, KlineHistoryFetcher
from typing import List, Dict

import os
import sys

sys.path.append(os.path.abspath("../../"))
from SystemConfig import Streaming
import Client.Queries.Public.Futures as public_client
import Client.Reciver.Futures as reciver_client
import Utils.DataModels as storage
import Utils.BaseUtils as base_utils

ins_public_client = public_client.Client()
ins_reciver_client = reciver_client.Client(symbols=Streaming.symbols, intervals=Streaming.intervals)
# 타입 힌트용
data_storage = storage.SymbolStorage()


class MarketDataHandler(WebSocketManager, KlineHistoryFetcher):
    def __init__(
        self,
        real_storage: data_storage,
        history_storage: data_storage,
        public_client: ins_public_client,
        reciver_client: ins_reciver_client,
        max_workers: int = 3,
    ):
        WebSocketManager.__init__(self, reciver_client=reciver_client)
        KlineHistoryFetcher.__init__(
            self, symbol_storage=history_storage, public_client=public_client
        )
        self.real_storage = real_storage
        self.max_workers = min(max_workers, 5)

        self.get_kline_data(symbols=self.symbols, intervals=self.intervals)

    def get_kline_data(self, symbols: List, intervals: List):
        # print("🚀 kline 기초데이터 수신중...")
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

        # print("✅ Kline 데이터 수집 완료")

    # async def stream_kline_run(self):
    #     await self.kline_limit_run()

    async def real_storage_update(self):
        while True:
            if not self.reciver_client.asyncio_queue.empty():
                data = await self.reciver_client.asyncio_queue.get()
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
        while True:
            # 유효한 intervals 필터링
            valid_intervals = [
                interval
                for interval in self.intervals
                if base_utils.is_time_match(interval)
            ]

            if valid_intervals:
                # print(f"🚀 kline update: {valid_intervals}")
                self.get_kline_data(symbols=self.symbols, intervals=valid_intervals)
                # print(f"✅ update complete\n")

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
        # print("🚀 시스템 시작")
        print(base_utils.get_current_time())

        # print("⏳ kline cycle 실행")
        self.run_threading()
        # print("⏳ websocket 실행")
        asyncio.run(self.run_async_tasks())

if __name__ == "__main__":
    """
    실행예시 // 
    """
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_public_client = public_client.PublicClient()
    ins_reciver_client = reciver_client.ReciverClient(symbols=symbols, intervals=intervals)
    
    real_storage = storage.SymbolStorage()  # 실시간 데이터 수집
    history_storage = storage.SymbolStorage()   # 과거 kline_data 수집
    
    ins_threading = handler.MarketDataHandler(real_storage=real_storage,
                                              history_storage=history_storage,
                                              ins_reciver=ins_reciver_client,
                                              ins_public=ins_public_client)
    asyncio.run(ins_threading.run())