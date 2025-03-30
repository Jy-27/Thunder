import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
from SystemConfig import Streaming

class OrderbookFechter:
    def __init__(
        self,
        queue_fetch: asyncio.Queue,
        event_trigger_orderbook: asyncio.Event,
        event_fired_done_orderbook: asyncio.Event,
        event_trigger_stop_loop: asyncio.Event,
        event_fired_loop_status: asyncio.Event,
        limit: int = Streaming.orderbook_limit,
    ):
        self.queue_fetch = queue_fetch
        self.event_trigger_orderbook = event_trigger_orderbook
        self.event_fired_done_orderbook = event_fired_done_orderbook
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_loop_status = event_fired_loop_status
        self.limit = limit
        
        self.symbols = Streaming.symbols
        self.ins_futures_mk_fetcher = FuturesMarketFetcher()

    async def init_update(self):
        tasks = [
            self.fetch_and_queue(symbol)
            for symbol in Streaming.symbols
        ]
        await asyncio.gather(*tasks)

    async def fetch_and_queue(self, symbol: str):
        data = await self.ins_futures_mk_fetcher.fetch_order_book(symbol, self.limit)
        pack_data = (symbol, data)
        await self.queue_fetch.put(pack_data)

    async def tasks(self):
        tasks = [
            asyncio.create_task(self.fetch_and_queue(symbol))
            for symbol in self.symbols
            ]
        await asyncio.gather(*tasks)

    async def start(self):
        print(f"  OrderbookFetcher: ⏳ Receiving initial orderbook data")
        await self.init_update()
        print(f"  OrderbookFetcher: ✅ Initial orderbook data received")
        print(f"  OrderbookFetcher: 🚀 Starting to fetch")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_orderbook.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self.tasks()
            self.event_trigger_orderbook.clear()
            self.event_fired_done_orderbook.set()
        print(f"  OrderbookFetcher: ✋ Loop stopped")
        self.event_fired_loop_status.set()

if __name__ == "__main__":
    q_ = asyncio.Queue()
    e_ = []
    for _ in range(3):
        e_.append(asyncio.Event())
    instance = OrderbookFechter(q_, *e_)
    asyncio.run(instance.start())
