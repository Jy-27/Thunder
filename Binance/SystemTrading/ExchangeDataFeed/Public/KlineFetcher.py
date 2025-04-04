import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
import Workspace.Utils.BaseUtils as base_utils
import Workspace.Utils.TradingUtils as tr_utils
from SystemConfig import Streaming


class KlineFetcher:
    def __init__(
        self,
        queue_fetch_kline: asyncio.Queue,
        event_trigger_stop_loop: asyncio.Event,
        event_trigger_fetch_kline: asyncio.Event,
        event_fired_done_fetch_kline: asyncio.Event,
        event_fired_stop_loop_done_fetch_kline:asyncio.Event,
        limit: int = 480
    ):
        self.queue_fetch_kline = queue_fetch_kline
        self.event_trigger_fetch_kline = event_trigger_fetch_kline
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_done_fetch_kline = event_fired_done_fetch_kline
        self.event_fired_stop_loop_done_fetch_kline = event_fired_stop_loop_done_fetch_kline
        self.limit = limit
        
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.ins_futures_mk_fetcher = FuturesMarketFetcher()

    async def init_update(self):
        tasks = [
            self.fetch_and_queue(symbol, interval)
            for symbol in self.symbols
            for interval in self.intervals
        ]
        await asyncio.gather(*tasks)

    async def fetch_and_queue(self, symbol: str, interval: str):
        data = await self.ins_futures_mk_fetcher.fetch_klines_limit(
            symbol, interval, self.limit
        )
        pack_data = tr_utils.Packager.pack_kline_fetcher_message(symbol, interval, data)
        await self.queue_fetch_kline.put(pack_data)

    async def tasks(self):
        valid_intervals = [
            interval
            for interval in self.intervals
            if base_utils.is_time_match(interval)
            ]
        if valid_intervals:
            tasks = [
                asyncio.create_task(self.fetch_and_queue(symbol, interval))
                for symbol in self.symbols
                for interval in valid_intervals
                ]
            await asyncio.gather(*tasks)

    async def start(self):
        print(f"  KlineFetcher: ⏳ Receiving initial Kline data")
        await self.init_update()
        print(f"  KlineFetcher: ✅ Initial Kline data received")
        print(f"  KlineFetcher: 🚀 Starting to fetch")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_fetch_kline.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self.tasks()
            self.event_trigger_fetch_kline.clear()
            self.event_fired_done_fetch_kline.set()
        print(f"  KlineFetcher: ✋ Loop stopped")
        self.event_fired_stop_loop_done_fetch_kline.set()


if __name__ == "__main__":
    q_ = asyncio.Queue()
    e_ = []
    for _ in range(3):
        e_.append(asyncio.Event())
    class RunTest:
        def __init__(self, q1, e1, e2, e3):
            self.q1:asyncio.Queue = q1
            self.e1:asyncio.Event = e1
            self.e2:asyncio.Event = e2
            self.e3:asyncio.Event = e3
            self.instance = KlineFetcher(self.q1,
                                              self.e1,
                                              self.e2,
                                              self.e3)
        
        async def timer(self, timesleep:int):
            await asyncio.sleep(timesleep)
            print(f"  신규 업데이트")
            self.e1.set()
            await asyncio.sleep(timesleep)
            print(f"  시간 종료: {timesleep} sec")
            self.e2.set()
            
        async def start(self):
            tasks = [
                asyncio.create_task(self.instance.start()),
                asyncio.create_task(self.timer(10))
            ]
            await asyncio.gather(*tasks)
    
    test_instance = RunTest(q_, *e_)
    asyncio.run(test_instance.start())
