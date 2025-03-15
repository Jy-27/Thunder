import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher
import Workspace.Utils.BaseUtils as base_utils
import Workspace.Utils.TradingUtils as tr_utils
from SystemConfig import Streaming


class KlineCycleFetcher:
    def __init__(self, queue:asyncio.Queue, limit:int=480):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.queue = queue
        self.ins_futures_mk_fetcher = FuturesMarketFetcher()
        self.limit = limit
        
    async def init_update(self):
        tasks = [self.fetch_and_queue(symbol, interval) for symbol in self.symbols for interval in self.intervals]
        await asyncio.gather(*tasks)

    async def fetch_and_queue(self, symbol:str, interval:str):
        data = await self.ins_futures_mk_fetcher.fetch_klines_limit(symbol, interval, self.limit)
        pack_data = tr_utils.Packager.pack_kline_fetcher_message(symbol, interval, data)
        await self.queue.put(pack_data)

    async def start(self):
        print(f"  ⏳ kline data 전체 수신중")    
        await self.init_update()
        print(f"  ✅ kline data 수신 완료.")
        print(f"  🚀 KlineCycleFetcher 시작")
        while True:
            valid_intervals = [interval for interval in self.intervals if base_utils.is_time_match(interval)]
            if valid_intervals:
                tasks = [
                    asyncio.create_task(self.fetch_and_queue(symbol, interval))
                    for symbol in self.symbols for interval in valid_intervals]
                await asyncio.gather(*tasks)
            await base_utils.sleep_next_minute(minutes=1, buffer_time_sec=0.5)
            
if __name__ == "__main__":
    q_ = asyncio.Queue()
    obj = KlineCycleFetcher(q_)
    asyncio.run(obj.start())