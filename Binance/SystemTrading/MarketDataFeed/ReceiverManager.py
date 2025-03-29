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
from SystemTrading.MarketDataFeed.Public.KlineFetcher import KlineFetcher
from SystemTrading.MarketDataFeed.Public.OrderbookFetcher import (
    OrderbookFechter,
)
from SystemTrading.MarketDataFeed.Private.PrivateFetcher import PrivateFetcher


class ReceiverManager:
    """
    Market의 공개/비공개 데이터를 수신한다. 주료 웹소켓, 개인 계좌 정보, 거래내역 등 내역을 수신하여
    각 항목에 맞는 Queue에 반영하여 전송한다. Websocket Execution의 경우 주문 발생시에만 데이터가 수신되므로
    수신 발생시 Event신호를 활성화 하여 중앙 이벤트 처리 시스템에서 상황을 인식할 수 있도록 한다.
    
    Notes:
        매개변수 순서를 반드시 보장해야한다. 순서는 SystemConfig.py값을 참조할 것.
    """

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
        queue_fetch_account_balance: asyncio.Queue,
        queue_fetch_order_status: asyncio.Queue,
        
        event_trigger_stop_loop: asyncio.Event,  # set 신호 발생시 while을 일괄 종료한다.
        event_trigger_kline:asyncio.Event,
        event_trigger_orderbook:asyncio.Event,
        event_trigger_private: asyncio.Event,  # set 신호 발생시 PrivateFetcher를 실행한다.
        
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
        self.event_trigger_kline = event_trigger_kline
        self.event_trigger_orderbook = event_trigger_orderbook
        self.event_trigger_private = event_trigger_private

        self.event_fired_execution_ws = event_fired_execution_ws

        self.event_fired_ticker_loop = event_fired_ticker_loop
        self.event_fired_trade_loop = event_fired_trade_loop
        self.event_fired_miniTicker_loop = event_fired_miniTicker_loop
        self.event_fired_depth_loop = event_fired_depth_loop
        self.event_fired_aggTrade_loop = event_fired_aggTrade_loop
        self.event_fired_kline_loop = event_fired_kline_loop
        self.event_fired_execution_loop = event_fired_execution_loop
        self.event_fired_f_kline_loop = event_fired_f_kline_loop
        self.event_fired_orderbook_loop = event_fired_orderbook_loop
        self.event_fired_private_loop = event_fired_private_loop

        self.websocket_ticker = StreamReceiverWebsocket(
            "ticker",
            self.queue_feed_ticker_ws,
            self.event_trigger_stop_loop,
            self.event_fired_ticker_loop,
        )
        self.websocket_trade = StreamReceiverWebsocket(
            "trade",
            self.queue_feed_trade_ws,
            self.event_trigger_stop_loop,
            self.event_fired_trade_loop,
        )
        self.websocket_miniTicker = StreamReceiverWebsocket(
            "miniTicker",
            self.queue_feed_miniTicker_ws,
            self.event_trigger_stop_loop,
            self.event_fired_miniTicker_loop,
        )
        self.websocket_depth = StreamReceiverWebsocket(
            "depth",
            self.queue_feed_depth_ws,
            self.event_trigger_stop_loop,
            self.event_fired_depth_loop,
        )
        self.websocket_aggTrade = StreamReceiverWebsocket(
            "aggTrade",
            self.queue_feed_aggTrade_ws,
            self.event_trigger_stop_loop,
            self.event_fired_aggTrade_loop,
        )
        self.websocket_kline = KlineReceiverWebsocket(
            self.queue_feed_kline_ws,
            self.event_trigger_stop_loop,
            self.event_fired_kline_loop,
        )
        self.websocket_execution = ExecutionReceiverWebsocket(
            self.queue_feed_execution_ws,
            self.event_fired_execution_ws,  # 이벤트 중앙처리 시스템을 향함. 해당 이벤트 발생시 wallet 정보를 업데이트함.
            self.event_trigger_stop_loop,
            self.event_fired_execution_loop,    
        )
        self.fetcher_kline = KlineFetcher(
            self.queue_fetch_kline,
            self.event_trigger_kline,
            self.event_trigger_stop_loop,
            self.event_fired_f_kline_loop,
        )
        self.fetcher_orderbook = OrderbookFechter(
            self.queue_fetch_orderbook,
            self.event_trigger_orderbook,
            self.event_trigger_stop_loop,
            self.event_fired_orderbook_loop,
        )
        self.fetcher_private = PrivateFetcher(
            self.queue_fetch_account_balance,
            self.queue_fetch_orderbook,
            self.event_trigger_private,  # self.event_fired_execution_
            self.event_trigger_stop_loop,
            self.event_fired_private_loop,
        )

    async def start(self):
        tasks = [
            asyncio.create_task(self.websocket_ticker.start()),##
            asyncio.create_task(self.websocket_trade.start()),##
            asyncio.create_task(self.websocket_miniTicker.start()),##
            asyncio.create_task(self.websocket_depth.start()),##
            asyncio.create_task(self.websocket_aggTrade.start()),##
            asyncio.create_task(self.websocket_kline.start()),##
            asyncio.create_task(self.websocket_execution.start()),
            asyncio.create_task(self.fetcher_kline.start()),
            asyncio.create_task(self.fetcher_orderbook.start()),##
            asyncio.create_task(self.fetcher_private.start()),
        ]
        await asyncio.gather(*tasks)
        print(f"  ℹ️ ReceiverManager Loop가 종료되어 수신이 중단됨.")


if __name__ == "__main__":
    args = []
    for _ in range(11):
        args.append(asyncio.Queue())
    for _ in range(15):
        args.append(asyncio.Event())
    args = tuple(args)
    
    class RunTest:
        def __init__(self, *args):
            self.args = args
            self.receiver_manager = ReceiverManager(*args)
            self.timesleep = 10
        
        async def timer(self):
            print(f"  ⏱️ timer: {self.timesleep}")
            await asyncio.sleep(self.timesleep)
            print(f"  ✋ STOP!!")
            self.args[-3].set()
            self.args[-2].set()
        
        async def start(self):
            tasks = [
                asyncio.create_task(self.receiver_manager.start()),
                asyncio.create_task(self.timer())
            ]
            await asyncio.gather(*tasks)
    
    instance = RunTest(*args)
    asyncio.run(instance.start())
            