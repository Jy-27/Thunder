import concurrent.futures
import threading
import asyncio
from typing import List, Dict, Final
import time
import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming



from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher as futures_mk_fetcher
from Workspace.DataStorage.DataStorage import SymbolStorage as storage
import Utils.TradingUtils as tr_utils
import Utils.BaseUtils as base_utils

class ThreadingWorks:
    max_worker:Final[int] = 3
    interval_cycle:Final[int] = 1
    def __init__(
        self,
        history_storage:storage,
        market_fetcher:futures_mk_fetcher,
        kline_limit:int,
        workers:int=3,
    ):
        self.history_storage = history_storage  # kline data 저장용
        self.market_fetcher = market_fetcher  # kline data 수신용
        self.kline_limit = kline_limit
        self.workers = min(workers, self.max_worker)
        self.symbols = self.history_storage.symbols
        self.intervals = self.history_storage.intervals



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
            max_workers=min(self.workers, self.max_worker)
        ) as executor:
            futures = [
                executor.submit(
                    self._update_kline_data, symbol, interval, self.kline_limit
                )
                for symbol in self.symbols
                for interval in self.intervals
            ]
            concurrent.futures.wait(futures)

    def run_threading_kline_cycle(self, interval_minutes: int = 1):
        """Kline 데이터를 주기적으로 가져오는 함수"""
        while True:
            valid_intervals = [
                interval
                for interval in self.intervals
                if base_utils.is_time_match(interval)
            ]
            if valid_intervals:
                self._threading_kline_update(
                    self.symbols, valid_intervals, self.kline_limit
                )
            # 정각 타이머
            base_utils.sleep_next_minute(interval_minutes)
            # 서버 지연 보정 타임슬립. 위 함수와 순서가 바뀌면 안된다.
            time.sleep(1)

    def start(self):
        """
        멀티쓰레딩 실행 함수 (오류 발생 시 즉시 프로그램 종료).
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = [
                executor.submit(self.run_threading_kline_cycle, self.interval_cycle),
                executor.submit(self.another_threading_function)  # 추가 함수 실행 가능
            ]

            # 첫 번째 예외 발생 시 즉시 반환
            concurrent.futures.wait(futures, return_when=concurrent.futures.FIRST_EXCEPTION)

            # 개별 future의 예외 확인 후 프로그램 강제 종료
            for future in futures:
                try:
                    future.result()  # 예외 발생 시 즉시 종료
                except Exception as e:
                    print(f"[ERROR] 프로그램 오류 발생: {e}", file=sys.stderr)
                    sys.exit(1)  # 즉시 프로그램 종료


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
