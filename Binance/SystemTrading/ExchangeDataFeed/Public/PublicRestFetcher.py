import asyncio
import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from typing import Optional, Dict
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)


class PublicRestFetcher:
    def __init__(
        self,
        queue_feed_fetch_ticker_price: asyncio.Queue,
        queue_feed_fetch_book_tickers: asyncio.Queue,
        queue_feed_fetch_24hr_ticker: asyncio.Queue,
        queue_feed_fetch_kline_limit: asyncio.Queue,
        queue_feed_fetch_order_book: asyncio.Queue,
        queue_feed_fetch_recent_trades: asyncio.Queue,
        queue_feed_fetch_agg_trades: asyncio.Queue,
        queue_feed_fetch_server_time: asyncio.Queue,
        queue_feed_fetch_ping_balance: asyncio.Queue,
        queue_feed_fetch_exchange_info: asyncio.Queue,
        queue_feed_fetch_mark_price: asyncio.Queue,
        queue_feed_fetch_funding_rate: asyncio.Queue,
        queue_feed_fetch_open_interest: asyncio.Queue,
        
        queue_request_fetch_ticker_price: asyncio.Queue,
        queue_request_fetch_book_tickers: asyncio.Queue,
        queue_request_fetch_24hr_ticker: asyncio.Queue,
        queue_request_fetch_kline_limit: asyncio.Queue,
        queue_request_fetch_order_book: asyncio.Queue,
        queue_request_fetch_recent_trades: asyncio.Queue,
        queue_request_fetch_agg_trades: asyncio.Queue,
        queue_request_fetch_mark_price: asyncio.Queue,
        queue_request_fetch_funding_rate: asyncio.Queue,
        queue_request_fetch_open_interest: asyncio.Queue,
        
        event_trigger_shutdown_loop: asyncio.Event,
        
        event_trigger_fetch_server_time: asyncio.Event,
        event_trigger_fetch_ping_balance: asyncio.Event,
        event_trigger_fetch_exchange_info: asyncio.Event,
        
        event_fired_done_fetch_ticker_price: asyncio.Event,
        event_fired_done_fetch_book_tickers: asyncio.Event,
        event_fired_done_fetch_ticker_24hr: asyncio.Event,
        event_fired_done_fetch_kline_limit: asyncio.Event,
        event_fired_done_fetch_order_book: asyncio.Event,
        event_fired_done_fetch_recent_trades: asyncio.Event,
        event_fired_done_fetch_agg_trade: asyncio.Event,
        event_fired_done_fetch_server_time: asyncio.Event,
        event_fired_done_fetch_ping_balance: asyncio.Event,
        event_fired_done_fetch_exchange_info: asyncio.Event,
        event_fired_done_fetch_mark_price: asyncio.Event,
        event_fired_done_fetch_funding_rate: asyncio.Event,
        event_fired_done_fetch_open_interest: asyncio.Event,
        
        event_fired_done_shutdown_loop_fetch_ticker_price:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_book_tickers:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_ticker_24hr:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_kline_limit:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_order_book:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_recent_trades:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_agg_trade:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_server_time:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_ping_balance:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_exchange_info:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_mark_price:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_funding_rate:asyncio.Event,
        event_fired_done_shutdown_loop_fetch_open_interest:asyncio.Event,
        
        event_fired_done_public_rest_fetcher: asyncio.Event,
    ):

        self.queue_feed_fetch_ticker_price = queue_feed_fetch_ticker_price
        self.queue_feed_fetch_book_tickers = queue_feed_fetch_book_tickers
        self.queue_feed_fetch_24hr_ticker = queue_feed_fetch_24hr_ticker
        self.queue_feed_fetch_kline_limit = queue_feed_fetch_kline_limit
        self.queue_feed_fetch_order_book = queue_feed_fetch_order_book
        self.queue_feed_fetch_recent_trades = queue_feed_fetch_recent_trades
        self.queue_feed_fetch_agg_trades = queue_feed_fetch_agg_trades
        self.queue_feed_fetch_server_time = queue_feed_fetch_server_time
        self.queue_feed_fetch_ping_balance = queue_feed_fetch_ping_balance
        self.queue_feed_fetch_exchange_info = queue_feed_fetch_exchange_info
        self.queue_feed_fetch_mark_price = queue_feed_fetch_mark_price
        self.queue_feed_fetch_funding_rate = queue_feed_fetch_funding_rate
        self.queue_feed_fetch_open_interest = queue_feed_fetch_open_interest

        self.queue_request_fetch_ticker_price = queue_request_fetch_ticker_price
        self.queue_request_fetch_book_tickers = queue_request_fetch_book_tickers
        self.queue_request_fetch_24hr_ticker = queue_request_fetch_24hr_ticker
        self.queue_request_fetch_kline_limit = queue_request_fetch_kline_limit
        self.queue_request_fetch_order_book = queue_request_fetch_order_book
        self.queue_request_fetch_recent_trades = queue_request_fetch_recent_trades
        self.queue_request_fetch_agg_trades = queue_request_fetch_agg_trades
        self.queue_request_fetch_mark_price = queue_request_fetch_mark_price
        self.queue_request_fetch_funding_rate = queue_request_fetch_funding_rate
        self.queue_request_fetch_open_interest = queue_request_fetch_open_interest

        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop

        self.event_trigger_fetch_server_time = event_trigger_fetch_server_time
        self.event_trigger_fetch_ping_balance = event_trigger_fetch_ping_balance
        self.event_trigger_fetch_exchange_info = event_trigger_fetch_exchange_info

        self.event_fired_done_fetch_ticker_price = event_fired_done_fetch_ticker_price
        self.event_fired_done_fetch_book_tickers = event_fired_done_fetch_book_tickers
        self.event_fired_done_fetch_ticker_24hr = event_fired_done_fetch_ticker_24hr
        self.event_fired_done_fetch_kline_limit = event_fired_done_fetch_kline_limit
        self.event_fired_done_fetch_order_book = event_fired_done_fetch_order_book
        self.event_fired_done_fetch_recent_trades = event_fired_done_fetch_recent_trades
        self.event_fired_done_fetch_agg_trade = event_fired_done_fetch_agg_trade
        self.event_fired_done_fetch_server_time = event_fired_done_fetch_server_time
        self.event_fired_done_fetch_ping_balance = event_fired_done_fetch_ping_balance
        self.event_fired_done_fetch_exchange_info = event_fired_done_fetch_exchange_info
        self.event_fired_done_fetch_mark_price = event_fired_done_fetch_mark_price
        self.event_fired_done_fetch_funding_rate = event_fired_done_fetch_funding_rate
        self.event_fired_done_fetch_open_interest = event_fired_done_fetch_open_interest

        self.event_fired_done_shutdown_loop_fetch_ticker_price = event_fired_done_shutdown_loop_fetch_ticker_price
        self.event_fired_done_shutdown_loop_fetch_book_tickers = event_fired_done_shutdown_loop_fetch_book_tickers
        self.event_fired_done_shutdown_loop_fetch_ticker_24hr = event_fired_done_shutdown_loop_fetch_ticker_24hr
        self.event_fired_done_shutdown_loop_fetch_kline_limit = event_fired_done_shutdown_loop_fetch_kline_limit
        self.event_fired_done_shutdown_loop_fetch_order_book = event_fired_done_shutdown_loop_fetch_order_book
        self.event_fired_done_shutdown_loop_fetch_recent_trades = event_fired_done_shutdown_loop_fetch_recent_trades
        self.event_fired_done_shutdown_loop_fetch_agg_trade = event_fired_done_shutdown_loop_fetch_agg_trade
        self.event_fired_done_shutdown_loop_fetch_server_time = event_fired_done_shutdown_loop_fetch_server_time
        self.event_fired_done_shutdown_loop_fetch_ping_balance = event_fired_done_shutdown_loop_fetch_ping_balance
        self.event_fired_done_shutdown_loop_fetch_exchange_info = event_fired_done_shutdown_loop_fetch_exchange_info
        self.event_fired_done_shutdown_loop_fetch_mark_price = event_fired_done_shutdown_loop_fetch_mark_price
        self.event_fired_done_shutdown_loop_fetch_funding_rate = event_fired_done_shutdown_loop_fetch_funding_rate
        self.event_fired_done_shutdown_loop_fetch_open_interest = event_fired_done_shutdown_loop_fetch_open_interest
        
        self.event_fired_done_public_rest_fetcher = event_fired_done_public_rest_fetcher

        self.instance_futures_market_fetcher = FuturesMarketFetcher()

    @tr_utils.Decorator.log_lifecycle()
    async def ticker_price(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[str] = (
                await self.queue_request_fetch_ticker_price.get()
            )
            if request_message is None:
                continue
            fetched_ticker_price = (
                await self.instance_futures_market_fetcher.fetch_ticker_price(
                    request_message
                )
            )
            await self.queue_feed_fetch_ticker_price.put(fetched_ticker_price)
            self.event_fired_done_fetch_ticker_price.set()
        self.event_fired_done_shutdown_loop_fetch_ticker_price.set()

    @tr_utils.Decorator.log_lifecycle()
    async def book_tickers(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[str] = (
                await self.queue_request_fetch_book_tickers.get()
            )
            if request_message is None:
                continue
            fetched_book_tickers = (
                await self.instance_futures_market_fetcher.fetch_book_tickers(
                    request_message
                )
            )
            await self.queue_feed_fetch_book_tickers.put(fetched_book_tickers)
            self.event_fired_done_fetch_book_tickers.set()
        self.event_fired_done_shutdown_loop_fetch_book_tickers.set()

    @tr_utils.Decorator.log_lifecycle()
    async def ticker_24hr(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[str] = (
                await self.queue_request_fetch_24hr_ticker.get()
            )
            if request_message is None:
                continue
            fetched_ticker_24hr = (
                await self.instance_futures_market_fetcher.fetch_24hr_ticker(
                    request_message
                )
            )
            await self.queue_feed_fetch_24hr_ticker.put(fetched_ticker_24hr)
            self.event_fired_done_fetch_ticker_24hr.set()
        self.event_fired_done_shutdown_loop_fetch_ticker_24hr.set()

    @tr_utils.Decorator.log_lifecycle()
    async def kline_limit(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[Dict] = (
                await self.queue_request_fetch_kline_limit.get()
            )
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            interval = request_message["interval"]
            limit = request_message["limit"]
            fetched_kline_limit = (
                await self.instance_futures_market_fetcher.fetch_klines_limit(
                    symbol, interval, limit
                )
            )
            await self.queue_feed_fetch_kline_limit.put(fetched_kline_limit)
            self.event_fired_done_fetch_kline_limit.set()
        self.event_fired_done_shutdown_loop_fetch_kline_limit.set()

    @tr_utils.Decorator.log_lifecycle()
    async def order_book(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[Dict] = (
                await self.queue_request_fetch_order_book.get()
            )
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_order_book = (
                await self.instance_futures_market_fetcher.fetch_order_book(
                    symbol, limit
                )
            )
            await self.queue_feed_fetch_order_book.put(fetched_order_book)
            self.event_fired_done_fetch_order_book.set()
        self.event_fired_done_shutdown_loop_fetch_order_book.set()

    @tr_utils.Decorator.log_lifecycle()
    async def recent_trades(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[Dict] = (
                await self.queue_request_fetch_recent_trades.get()
            )
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_recent_trades = (
                await self.instance_futures_market_fetcher.fetch_recent_trades(
                    symbol, limit
                )
            )
            await self.queue_feed_fetch_recent_trades.put(fetched_recent_trades)
            self.event_fired_done_fetch_recent_trades.set()
        self.event_fired_done_shutdown_loop_fetch_recent_trades.set()

    @tr_utils.Decorator.log_lifecycle()
    async def agg_trade(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[Dict] = (
                await self.queue_request_fetch_agg_trades.get()
            )
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_agg_trade = (
                await self.instance_futures_market_fetcher.fetch_agg_trades(
                    symbol, limit
                )
            )
            await self.queue_feed_fetch_agg_trades.put(fetched_agg_trade)
            self.event_fired_done_fetch_agg_trade.set()
        self.event_fired_done_shutdown_loop_fetch_agg_trade.set()

    @tr_utils.Decorator.log_lifecycle()
    async def server_time(self):
        while not self.event_trigger_shutdown_loop.is_set():
            await self.event_trigger_fetch_server_time.wait()
            fetched_server_time = (
                await self.instance_futures_market_fetcher.fetch_server_time()
            )
            await self.queue_feed_fetch_server_time.put(fetched_server_time)
            self.event_fired_done_fetch_server_time.set()
        self.event_fired_done_shutdown_loop_fetch_server_time.set()

    @tr_utils.Decorator.log_lifecycle()
    async def ping_binance(self):
        while not self.event_trigger_shutdown_loop.is_set():
            await self.event_trigger_fetch_ping_balance.wait()
            fetched_ping_balance = (
                await self.instance_futures_market_fetcher.fetch_ping_binance()
            )
            await self.queue_feed_fetch_ping_balance.put(fetched_ping_balance)
            self.event_fired_done_fetch_ping_balance.set()
        self.event_fired_done_shutdown_loop_fetch_ping_balance.set()

    @tr_utils.Decorator.log_lifecycle()
    async def exchange_info(self):
        while not self.event_trigger_shutdown_loop.is_set():
            await self.event_trigger_fetch_exchange_info.wait()
            fetched_exchange_info = (
                await self.instance_futures_market_fetcher.fetch_exchange_info()
            )
            await self.queue_feed_fetch_exchange_info.put(fetched_exchange_info)
            self.event_fired_done_fetch_exchange_info.set()
        self.event_fired_done_shutdown_loop_fetch_exchange_info.set()

    @tr_utils.Decorator.log_lifecycle()
    async def mark_price(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[str] = (
                await self.queue_request_fetch_mark_price.get()
            )
            if request_message is None:
                continue
            fetched_mark_price = (
                await self.instance_futures_market_fetcher.fetch_mark_price(
                    request_message
                )
            )
            await self.queue_feed_fetch_mark_price.put(fetched_mark_price)
            self.event_fired_done_fetch_mark_price.set()
        self.event_fired_done_shutdown_loop_fetch_mark_price.set()

    @tr_utils.Decorator.log_lifecycle()
    async def funding_rate(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[Dict] = (
                await self.queue_request_fetch_funding_rate.get()
            )
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_funding_rate = (
                await self.instance_futures_market_fetcher.fetch_funding_rate(
                    symbol, limit
                )
            )
            await self.queue_feed_fetch_funding_rate.put(fetched_funding_rate)
            self.event_fired_done_fetch_funding_rate.set()
        self.event_fired_done_shutdown_loop_fetch_funding_rate.set()

    @tr_utils.Decorator.log_lifecycle()
    async def open_interest(self):
        while not self.event_trigger_shutdown_loop.is_set():
            request_message: Optional[str] = (
                await self.queue_request_fetch_open_interest.get()
            )
            if request_message is None:
                continue
            fetched_open_interest = (
                await self.instance_futures_market_fetcher.fetch_open_interest(
                    request_message
                )
            )
            await self.queue_feed_fetch_open_interest.put(fetched_open_interest)
            self.event_fired_done_fetch_open_interest.set()
        self.event_fired_done_shutdown_loop_fetch_open_interest.set()

    @tr_utils.Decorator.log_lifecycle()
    async def shutdown_all_loops(self):
        SHUTDOWN_SIGNAL = None
        await self.event_trigger_shutdown_loop.wait()
        await self.queue_request_fetch_ticker_price.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_book_tickers.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_24hr_ticker.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_kline_limit.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_order_book.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_recent_trades.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_agg_trades.put(SHUTDOWN_SIGNAL)
        self.event_trigger_fetch_server_time.set()
        self.event_trigger_fetch_ping_balance.set()
        self.event_trigger_fetch_exchange_info.set()
        await self.queue_request_fetch_mark_price.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_funding_rate.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_open_interest.put(SHUTDOWN_SIGNAL)
        self.event_fired_done_public_rest_fetcher.set()

    async def start(self):
        tasks = [
            asyncio.create_task(self.ticker_price()),
            asyncio.create_task(self.book_tickers()),
            asyncio.create_task(self.ticker_24hr()),
            asyncio.create_task(self.kline_limit()),
            asyncio.create_task(self.order_book()),
            asyncio.create_task(self.recent_trades()),
            asyncio.create_task(self.agg_trade()),
            asyncio.create_task(self.server_time()),
            asyncio.create_task(self.ping_binance()),
            asyncio.create_task(self.exchange_info()),
            asyncio.create_task(self.mark_price()),
            asyncio.create_task(self.funding_rate()),
            asyncio.create_task(self.open_interest()),
            asyncio.create_task(self.shutdown_all_loops()),
        ]
        await asyncio.gather(*tasks)
        print(f"  \033[91m🔴 Shutdown\033[0m >> \033[91mPublicRestFetcher.py\033[0m")




if __name__ == "__main__":
    q_count = 23
    e_count = 18

    q_ = []
    e_ = []

    for _ in range(q_count):
        q_.append(asyncio.Queue())
    for _ in range(e_count):
        e_.append(asyncio.Event())

    q_ = tuple(q_)
    e_ = tuple(e_)

    test_instance = PublicRestFetcher(*q_, *e_)

    async def timer():
        await asyncio.sleep(10)
        print(f"  🚀 Event Set!!")
        e_[0].set()

    async def main():
        tasks = [
            asyncio.create_task(test_instance.start()),
            asyncio.create_task(timer()),
        ]
        await asyncio.gather(*tasks)

    asyncio.run(main())