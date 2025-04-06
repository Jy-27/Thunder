import asyncio
from typing import Dict, Optional
import yfinance as yf

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils

class YahooFinanceFetcher:
    def __init__(self,
                 queue_feed_fetch_yfinance_indices:asyncio.Queue,
                 queue_request_fetch_yfinance_indices:asyncio.Queue,
                 event_trigger_shutdown_loop:asyncio.Event,
                 event_fired_done_fetch_yfinance_indices:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_yfinance_indices:asyncio.Event,
                 
                 event_fired_done_public_yahoo_finance_fetcher:asyncio.Event
                 ):
        self.queue_feed_fetch_yfinance_indices = queue_feed_fetch_yfinance_indices
        self.queue_request_fetch_yfinance_indices = queue_request_fetch_yfinance_indices
        
        self.event_fired_done_fetch_yfinance_indices = event_fired_done_fetch_yfinance_indices
        
        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop
        self.event_fired_done_shutdown_loop_fetch_yfinance_indices = event_fired_done_shutdown_loop_fetch_yfinance_indices
        
        self.event_fired_done_public_yahoo_finance_fetcher = event_fired_done_public_yahoo_finance_fetcher  # 🔧 이 줄이 빠져 있음

    async def yfinance_index_query(self, symbol:str, period:str, interval:str):
        return await asyncio.to_thread(lambda: yf.Ticker(symbol).history(period=period, interval=interval))

    @tr_utils.Decorator.log_lifecycle()
    async def yfinance_indices(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[Dict] = await self.queue_request_fetch_yfinance_indices.get()
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            period = request_message["period"]
            interval = request_message["interval"]
            fetched_yfinance_indices = await self.yfinance_index_query(symbol, period, interval)
            await self.queue_feed_fetch_yfinance_indices.put(fetched_yfinance_indices)
            self.event_fired_done_fetch_yfinance_indices.set()
        self.event_fired_done_shutdown_loop_fetch_yfinance_indices.set()
    
    @tr_utils.Decorator.log_complete()
    async def shutdown_all_loops(self):
        SHUTDOWN_SIGNAL = None
        await self.event_trigger_shutdown_loop.wait()
        await self.queue_request_fetch_yfinance_indices.put(SHUTDOWN_SIGNAL)
        self.event_fired_done_public_yahoo_finance_fetcher.set()
    
    async def start(self):
        tasks = [
            asyncio.create_task(self.yfinance_indices()),
            asyncio.create_task(self.shutdown_all_loops())
        ]
        await asyncio.gather(*tasks)
        print(f"  \033[91m🔴 Shutdown\033[0m >> \033[91mPublicYahooFinanceFetcher.py\033[0m")
    
if __name__ == "__main__":
    import Workspace.Utils.BaseUtils as base_utils

    q_ = tuple(asyncio.Queue() for _ in range(2))
    e_ = tuple(asyncio.Event() for _ in range(4))
    main_instance = YahooFinanceFetcher(*q_, *e_)
    class RunTest:
        def __init__(self,
                     instance:YahooFinanceFetcher,
                     stop_timer:int,
                     create_event_timer:int):
            self.instance = instance
            self.stop_timer = stop_timer
            self.create_event_timer = create_event_timer
        
        async def stopper(self):
            await asyncio.sleep(self.stop_timer)
            self.instance.event_trigger_shutdown_loop.set()
            print(f"     ✋ Timer")
    
        async def send_request_message(self):
            await asyncio.sleep(self.create_event_timer)
            message = {
                "symbol":"^GSPC",
                "period":"1mo",
                "interval":"1d"
            }
            await self.instance.queue_request_fetch_yfinance_indices.put(message)
            print(f"   🚀 send request message")
        
        async def main(self):
            tasks = [
                asyncio.create_task(self.stopper()),
                asyncio.create_task(self.send_request_message()),
                asyncio.create_task(self.instance.start())
            ]
            await asyncio.gather(*tasks)
    
    test_instance = RunTest(main_instance, 10, 3)
    asyncio.run(test_instance.main())