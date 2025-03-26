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
from SystemTrading.MarketDataFeed.Private.PrivateFetcher import PrivateFetcher

class ReceiverManager:
    def __init__(
        self,
        queue_feed_ticker_ws: asyncio.Queue,
        queue_feed_trade_ws: asyncio.Queue,
        queue_feed_miniTicker_ws: asyncio.Queue,
        queue_feed_depth_ws: asyncio.Queue,
        queue_feed_aggTrade_ws: asyncio.Queue,
        queue_feed_kline_ws: asyncio.Queue,
        queue_feed_execution_ws: asyncio.Queue,
        queue_fetch_kline: asyncio.Queue,
        queue_fetch_orderbook: asyncio.Queue,
        queue_fetch_account_balance:asyncio.Queue,
        queue_fetch_order_status:asyncio.Queue,
        
        event_trigger_stop_loop: asyncio.Event, # set 신호 발생시 while을 일괄 종료한다.
        event_trigger_private: asyncio.Event,   # set 신호 발생시 PrivateFetcher를 실행한다.
        
        event_fired_execution_ws: asyncio.Event,
        
        event_fired_ticker_loop: asyncio.Event,
        event_fired_trade_loop: asyncio.Event,
        event_fired_miniTicker_loop: asyncio.Event,
        event_fired_depth_loop: asyncio.Event,
        event_fired_aggTrade_loop: asyncio.Event,
        event_fired_kline_loop: asyncio.Event,
        event_fired_execution_loop: asyncio.Event,
        event_fired_f_kline_loop: asyncio.Event,
        event_fired_orderbook_loop: asyncio.Event,
        event_fired_private_loop: asyncio.Event,
    ):

        self.queue_feed_ticker_ws = queue_feed_ticker_ws
        self.queue_feed_trade_ws = queue_feed_trade_ws
        self.queue_feed_miniTicker_ws = queue_feed_miniTicker_ws
        self.queue_feed_depth_ws = queue_feed_depth_ws
        self.queue_feed_aggTrade_ws = queue_feed_aggTrade_ws
        self.queue_feed_kline_ws = queue_feed_kline_ws
        self.queue_feed_execution_ws = queue_feed_execution_ws
        self.queue_fetch_kline = queue_fetch_kline
        self.queue_fetch_orderbook = queue_fetch_orderbook
        self.queue_fetch_account_balance = queue_fetch_account_balance
        self.queue_fetch_order_status = queue_fetch_order_status

        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_trigger_private = event_trigger_private
        
        self.event_fired_execution_ws = event_fired_execution_ws
        
        self.event_fired_ticker_loop = event_fired_ticker_loop
        self.event_fired_trade_loop = event_fired_trade_loop
        self.event_fired_miniTicker_loop = event_fired_miniTicker_loop
        self.event_fired_depth_loop = event_fired_depth_loop
        self.event_fired_aggTrade_loop = event_fired_aggTrade_loop
        self.event_fired_kline_loop = event_fired_kline_loop
        self.event_fired_execution_loop = event_fired_execution_loop
        self.event_fired_f_kline_loop =  event_fired_f_kline_loop 
        self.event_fired_orderbook_loop = event_fired_orderbook_loop
        self.event_fired_private_loop =  event_fired_private_loop 
        
        self.ws_ticker = StreamReceiverWebsocket(
            "ticker", self.queue_feed_ticker_ws, self.event_trigger_stop_loop, self.event_fired_ticker_loop
        )
        self.ws_trade = StreamReceiverWebsocket(
            "trade", self.queue_feed_trade_ws, self.event_trigger_stop_loop, self.event_fired_trade_loop
        )
        self.ws_miniTicker = StreamReceiverWebsocket(
            "miniTicker", self.queue_feed_miniTicker_ws, self.event_trigger_stop_loop, self.event_fired_miniTicker_loop
        )
        self.ws_depth = StreamReceiverWebsocket(
            "depth", self.queue_feed_depth_ws, self.event_trigger_stop_loop, self.event_fired_depth_loop
        )
        self.ws_aggTrade = StreamReceiverWebsocket(
            "aggTrade", self.queue_feed_aggTrade_ws, self.event_trigger_stop_loop, self.event_fired_aggTrade_loop
        )
        self.ws_kline = KlineReceiverWebsocket(
            self.queue_feed_kline_ws, self.event_trigger_stop_loop, self.event_fired_kline_loop
        )
        self.ws_execution = ExecutionReceiverWebsocket(
            self.queue_feed_execution_ws, self.event_fired_execution_ws, self.event_trigger_stop_loop, self.event_fired_execution_loop
        )
        self.fetcher_kline = KlineCycleFetcher(
            self.queue_fetch_kline, self.event_trigger_stop_loop, self.event_fired_f_kline_loop
        )
        self.fetcher_orderbook = OrderbookCycleFechter(
            self.queue_fetch_orderbook, self.event_trigger_stop_loop, self.event_fired_orderbook_loop
        )
        self.fetcher_private = PrivateFetcher(self.queue_fetch_account_balance,
                                              self.queue_fetch_orderbook,
                                              self.event_fired_execution_ws,
                                              self.event_trigger_stop_loop,
                                              self.event_fired_execution_loop)
    async def start(self):
        tasks = [
            asyncio.create_task(self.ws_ticker.start()),
            asyncio.create_task(self.ws_trade.start()),
            asyncio.create_task(self.ws_miniTicker.start()),
            asyncio.create_task(self.ws_depth.start()),
            asyncio.create_task(self.ws_aggTrade.start()),
            asyncio.create_task(self.ws_kline.start()),
            asyncio.create_task(self.ws_execution.start()),
            asyncio.create_task(self.fetcher_kline.start()),
            asyncio.create_task(self.fetcher_orderbook.start()),
            asyncio.create_task(self.fetcher_private.start())
        ]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    args = []
    for _ in range(11):
        args.append(asyncio.Queue())
    for _ in range(13):
        args.append(asyncio.Event())
    args = tuple(args)
    instance = ReceiverManager(*args)
    asyncio.run(instance.start())
