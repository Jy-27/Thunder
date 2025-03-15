from typing import Dict, List, Tuple
import multiprocessing
import asyncio
import os, sys
import datetime

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils
import Workspace.Utils.BaseUtils as base_utils

from Workspace.DataStorage.DataCollector.NodeStorage import MainStorage
from Workspace.DataStorage.DataCollector.aggTradeStorage import aggTradeStorage
from Workspace.DataStorage.DataCollector.DepthStorage import DepthStorage
from Workspace.DataStorage.DataCollector.ExecutionStorage import ExecutionStorage

import SystemConfig

def process_analysis(symbol, kline_data, agg_trade, depth):
    """멀티프로세싱으로 실행될 데이터 분석 함수"""
    return (f"{symbol}: 분석 완료\n"
            f"kline size: {len(kline_data)}\n"
            f"agg_trade size: {len(agg_trade)}\n"
            f"depth size: {len(depth)}\n")         
            # ✅ Queue를 사용하지 않고, 결과를 직접 반환

class KlineDataUpdater:
    @staticmethod
    def update_minute_kline(realtime_data: Dict[str, List], minute_data: Dict[str, List]) -> Dict[str, List]:
        """실시간 Kline 데이터를 1분 저장소에 업데이트하는 함수"""
        for symbol, history in minute_data.items():
            minute_data[symbol] = KlineDataUpdater._merge_kline(realtime_data[symbol], history)
        return minute_data

    @staticmethod
    def _is_valid_update(realtime_entry: List, last_minute_entry: List) -> bool:
        """실시간 데이터가 기존 1분 데이터의 마지막 항목과 동일한지 검사"""
        return realtime_entry[0] == last_minute_entry[0]  # 타임스탬프 비교

    @staticmethod
    def _merge_kline(realtime_entry: List, minute_history: List) -> List:
        """실시간 데이터를 기존 1분 데이터에 병합"""
        if KlineDataUpdater._is_valid_update(realtime_entry, minute_history[-1]):
            minute_history[-1] = realtime_entry
        else:
            minute_history.append(realtime_entry)
        return minute_history

class TradingAnalysis:
    def __init__(self, storage_history: MainStorage,
                 storage_real_time: MainStorage,
                 storage_aggTrade: aggTradeStorage,
                 storage_depth: DepthStorage,
                 time_cycle: int = 1):

        self.time_cycle = time_cycle
        self.storage_history = storage_history
        self.storage_real_time = storage_real_time
        self.storage_aggTrade = storage_aggTrade
        self.storage_depth = storage_depth
        self.symbols = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        self.convert_to_intervals = [f"interval_{i}" for i in self.intervals]

        self.queue = asyncio.Queue()

        self.ma_sam = {}

    def ma_sma(self):
        KlineDataUpdater._merge_kline(self.storage_real_time, self.storage_history)
        





    def get_dataset(self, symbol: str) -> Tuple[str, dict, list, list, list]:
        """프로세싱할 데이터를 가져오는 함수"""
        real_time = self.storage_real_time.to_dict(symbol)
        history = self.storage_history.to_dict(symbol)
        kline_data = KlineDataUpdater.update_minute_kline(real_time, history)
        agg_trade = self.storage_aggTrade.get_all_data()
        depth = self.storage_depth.get_all_data(symbol)
        # ✅ queue를 전달하지 않고 순수 데이터만 반환
        return symbol, kline_data, agg_trade, depth

    async def analysis_async(self):
        """비동기 루프에서 멀티프로세싱 분석 실행"""
        loop = asyncio.get_running_loop()
        dataset = [self.get_dataset(symbol) for symbol in self.symbols]  # ✅ queue 없이 데이터만 전달

        with multiprocessing.Pool(processes=4) as pool:
            results = await loop.run_in_executor(None, pool.starmap, process_analysis, dataset)

        # ✅ results 데이터를 asyncio.Queue에 저장
        for result in results:
            await self.queue.put(result)

    # TEST METHOD
    async def process_results(self):
        """비동기적으로 큐에서 데이터를 처리하는 함수"""
        while True:
            result = await self.queue.get()
            # print(result)
            # print(f"📥 결과 처리: {result}")
            self.queue.task_done()

    async def start(self):
        """비동기 루프에서 주기적으로 분석 실행"""
        print(f"  🚀 데이터 분석 시작.")
        print(f"  ⏳ {self.time_cycle} 분 간격으로 검토 설정됨.")

        # ✅ 큐 데이터를 처리하는 비동기 Task 실행 ( TEST 실행 )
        asyncio.create_task(self.process_results())

        while True:
            await base_utils.sleep_next_minute(self.time_cycle)
            # await asyncio.sleep(20)
            # print(datetime.datetime.now())
            await self.analysis_async()
