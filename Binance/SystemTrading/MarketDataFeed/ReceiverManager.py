import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.MarketDataFeed.Public.StreamReceiverWebsocket import (
    StreamReceiverWebsocket,
)
from SystemTrading.MarketDataFeed.Public.KlineReceiverWebsocket import (
    KlineReceiverWebsocket,
)
from SystemTrading.MarketDataFeed.Private.ExecutionReceiverWebsocket import (
    ExecutionReceiverWebsocket,
)
from SystemTrading.MarketDataFeed.Public.KlineCycleFetcher import KlineCycleFetcher
from SystemTrading.MarketDataFeed.Public.OrderBookCycleFetcher import (
    OrderbookCycleFechter,
)


class ReceiverManager:
    def __init__(
        self,
        queue_ticker: asyncio.Queue,
        queue_trade: asyncio.Queue,
        queue_minTicker: asyncio.Queue,
        queue_depth: asyncio.Queue,
        queue_aggTrade: asyncio.Queue,
        queue_kline_ws: asyncio.Queue,
        queue_execution_ws: asyncio.Queue,
        queue_kline_fetcher: asyncio.Queue,
        queue_orderbook_fetcher: asyncio.Queue,
        event_executuion_ws: asyncio.Event,
        event_loop_status: asyncio.Event,
    ):

        self.queue_ticker = queue_ticker
        self.queue_trade = queue_trade
        self.queue_minTicker = queue_minTicker
        self.queue_depth = queue_depth
        self.queue_aggTrade = queue_aggTrade
        self.queue_kline_ws = queue_kline_ws
        self.queue_execution_ws = queue_execution_ws
        self.queue_kline_fetcher = queue_kline_fetcher
        self.queue_orderbook_fetcher = queue_orderbook_fetcher
        self.event_executuion_ws = event_executuion_ws
        self.event_loop_status = event_loop_status

        self.ws_ticker = StreamReceiverWebsocket(
            "ticker", self.queue_ticker, self.event_loop_status
        )
        self.ws_trade = StreamReceiverWebsocket(
            "trade", self.queue_trade, self.event_loop_status
        )
        self.ws_minTicker = StreamReceiverWebsocket(
            "minTicker", self.queue_minTicker, self.event_loop_status
        )
        self.ws_depth = StreamReceiverWebsocket(
            "depth", self.queue_depth, self.event_loop_status
        )
        self.ws_aggTrade = StreamReceiverWebsocket(
            "aggTrade", self.queue_aggTrade, self.event_loop_status
        )
        self.ws_kline = KlineReceiverWebsocket(
            self.queue_kline_ws, self.event_loop_status
        )
        self.ws_execution = ExecutionReceiverWebsocket(
            self.queue_execution_ws, self.event_executuion_ws, self.event_loop_status
        )
        self.fetcher_kline = KlineCycleFetcher(
            self.queue_kline_fetcher, self.event_loop_status
        )
        self.fetcher_orderbook = OrderbookCycleFechter(
            self.queue_orderbook_fetcher, self.event_loop_status
        )

    async def start(self):
        tasks = [
            asyncio.create_task(self.ws_ticker.start()),
            asyncio.create_task(self.ws_trade.start()),
            asyncio.create_task(self.ws_minTicker.start()),
            asyncio.create_task(self.ws_depth.start()),
            asyncio.create_task(self.ws_aggTrade.start()),
            asyncio.create_task(self.ws_kline.start()),
            asyncio.create_task(self.ws_execution.start()),
            asyncio.create_task(self.fetcher_kline.start()),
            asyncio.create_task(self.fetcher_orderbook.start()),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    queues = []
    for _ in range(9):
        queues.append(asyncio.Queue())
    queues = tuple(queues)
    event_executuion = asyncio.Event()
    event_loop_status = asyncio.Event()

    instance = ReceiverManager(*queues, event_executuion, event_loop_status)
    asyncio.run(instance.start())
