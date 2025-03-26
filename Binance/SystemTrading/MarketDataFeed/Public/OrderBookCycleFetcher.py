import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
from SystemConfig import Streaming


class OrderbookCycleFechter:
    def __init__(
        self,
        queue_fetch: asyncio.Queue,
        event_trigger_stop_loop: asyncio.Event,
        event_fired_loop_status = asyncio.Event,
        limit: int = Streaming.orderbook_limit,
        timesleep: int = Streaming.orderbook_timesleep,
    ):
        self.symbols = Streaming.symbols
        self.queue_fetch = queue_fetch
        self.ins_futures_mk_fetcher = FuturesMarketFetcher()
        self.limit = limit
        self.timesleep = timesleep
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_loop_status = event_fired_loop_status

    async def fetch_and_queue(self, symbol: str):
        data = await self.ins_futures_mk_fetcher.fetch_order_book(symbol, self.limit)
        pack_data = (symbol, data)
        await self.queue_fetch.put(pack_data)

    async def start(self):
        print(f"  🚀 OrderBook 수신 시작")
        while not self.event_trigger_stop_loop.is_set():
            tasks = []
            for symbol in self.symbols:
                task = asyncio.create_task(self.fetch_and_queue(symbol))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(self.timesleep)
        print(f"  ⁉️ OrderBook Loop 종료됨.")
        self.event_fired_loop_status.set()


if __name__ == "__main__":
    q_ = asyncio.Queue()
    instance = OrderbookCycleFechter(queue=q_)
    asyncio.run(instance.start())
