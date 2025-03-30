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
        
        event_trigger_kline: asyncio.Event,
        event_trigger_orderbook: asyncio.Event,
        event_trigger_private: asyncio.Event,  # set 신호 발생시 PrivateFetcher를 실행한다.
        
        event_fired_execution_ws: asyncio.Event,
        event_fired_done_kline: asyncio.Event,
        event_fired_done_orderbook: asyncio.Event,
        event_fired_done_private: asyncio.Event,
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

        self.event_fired_done_kline = event_fired_done_kline
        self.event_fired_done_orderbook = event_fired_done_orderbook
        self.event_fired_done_private = event_fired_done_private

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
            self.event_fired_done_kline,
            self.event_trigger_stop_loop,
            self.event_fired_f_kline_loop,
        )
        self.fetcher_orderbook = OrderbookFechter(
            self.queue_fetch_orderbook,
            self.event_trigger_orderbook,
            self.event_fired_done_orderbook,
            self.event_trigger_stop_loop,
            self.event_fired_orderbook_loop,
        )
        self.fetcher_private = PrivateFetcher(
            self.queue_fetch_account_balance,
            self.queue_fetch_order_status,
            self.event_trigger_private,  # self.event_fired_execution_
            self.event_fired_done_private,
            self.event_trigger_stop_loop,
            self.event_fired_private_loop,
        )

    async def start(self):
        tasks = [
            asyncio.create_task(self.websocket_ticker.start()),  ##
            asyncio.create_task(self.websocket_trade.start()),  ##
            asyncio.create_task(self.websocket_miniTicker.start()),  ##
            asyncio.create_task(self.websocket_depth.start()),  ##
            asyncio.create_task(self.websocket_aggTrade.start()),  ##
            asyncio.create_task(self.websocket_kline.start()),  ##
            asyncio.create_task(self.websocket_execution.start()),
            asyncio.create_task(self.fetcher_kline.start()),
            asyncio.create_task(self.fetcher_orderbook.start()),  ##
            asyncio.create_task(self.fetcher_private.start()),
        ]
        await asyncio.gather(*tasks)
        print(f"  ℹ️ ReceiverManager Loop가 종료되어 수신이 중단됨.")

if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.TradingUtils as tr_utils

    class RunTestFetcher:
        """
        Receiver의 이벤트 기반 fetcher 함수의 기능 테스트 클라스다.
        asyncio.sleep을 이용하여 순차적으로 event를 발생시키고,
        데이터를 수신하여 queue로 전송한다. 전송된 데이터는 각 함수에서 개별 출력한다.

        Notes:
            interval값은 전체 interval값으로 오버라이드 한다.
            현재 시간에 맞는 interval 값만 처리하므로 시간에 따라 수신되는 interval값이
            다르므로 참조할 것.
        """

        def __init__(self, *args):
            self.args = args
            self.receiver_manager = ReceiverManager(*args)
            self.timesleep = 10
            # override
            self.receiver_manager.fetcher_kline.intervals = (
                SystemConfig.Streaming.all_intervals
            )

        async def timer(self):
            await asyncio.sleep(2)
            print(f"  ⏱️ timer: {self.timesleep} sec")
            await asyncio.sleep(self.timesleep)
            print(f"  🚀 kline event set")
            self.args[12].set()
            await asyncio.sleep(self.timesleep)
            print(f"  🚀 orderbook event set")
            self.args[13].set()
            await asyncio.sleep(self.timesleep)
            print(f"  🚀 private event set")
            self.args[14].set()
            await asyncio.sleep(self.timesleep)
            print(f"  🚀 stop event set")
            self.args[11].set()

        async def print_from_queue_kline(self):
            await asyncio.sleep(5)
            print(f"    🚨🧪⚠️ TEST kline 실행")
            await asyncio.sleep(1)
            while not self.receiver_manager.event_trigger_stop_loop.is_set():
                try:
                    q_data = await asyncio.wait_for(
                        self.receiver_manager.queue_fetch_kline.get(), timeout=1
                    )
                except asyncio.TimeoutError:
                    continue
                for i, v in q_data.items():
                    for n_i, n_v in v.items():
                        ...
                if self.receiver_manager.event_trigger_kline.is_set():
                    message = f"      👉🏻 kline: {i} / {n_i}"
                    print(message)
            print(f"    ✋ STOP - kline")

        async def print_from_queue_orderbook(self):
            await asyncio.sleep(5)
            print(f"    🚨🧪⚠️ TEST orderbook 실행")
            await asyncio.sleep(1)
            while not self.receiver_manager.event_trigger_stop_loop.is_set():
                try:
                    q_data = await asyncio.wait_for(
                        self.receiver_manager.queue_fetch_orderbook.get(), timeout=1
                    )
                except asyncio.TimeoutError:
                    continue
                if self.receiver_manager.event_trigger_orderbook.is_set():
                    message = f"      👉🏽 orderbook: {q_data[0]}"
                    print(message)
            print(f"    ✋ STOP - orderbook")

        async def print_from_queue_order_status(self):
            await asyncio.sleep(5)
            print(f"    🚨🧪⚠️ TEST order status 실행")
            await asyncio.sleep(1)
            while not self.receiver_manager.event_trigger_stop_loop.is_set():
                try:
                    q_data = await asyncio.wait_for(
                        self.receiver_manager.queue_fetch_order_status.get(), timeout=1
                    )
                except asyncio.TimeoutError:
                    continue
                symbol, data = q_data
                for i in data:
                    order_type = i["type"]
                    side = i["side"]
                    message = (
                        f"      👉🏿 order status: {symbol} / {order_type} / {side}"
                    )
                    print(message)
            print(f"    ✋ STOP - order status")

        async def print_from_queue_account_balance(self):
            await asyncio.sleep(5)
            print(f"    🚨🧪⚠️ TEST account balance 실행")
            await asyncio.sleep(1)
            while not self.receiver_manager.event_trigger_stop_loop.is_set():
                try:
                    q_data = await asyncio.wait_for(
                        self.receiver_manager.queue_fetch_account_balance.get(),
                        timeout=1,
                    )
                except asyncio.TimeoutError:
                    continue
                wallet_balance = tr_utils.Extractor.total_wallet_balance(q_data)
                margin_balance = tr_utils.Extractor.total_margin_balance(q_data)
                init_margin = tr_utils.Extractor.total_position_init_margin(q_data)
                unr_pnl = tr_utils.Extractor.total_unrealized_pnl(q_data)
                if any(x == 0 for x in (unr_pnl, init_margin)):
                    roi = 0
                else:
                    roi = (unr_pnl / init_margin) * 100
                print(
                    f"      👉🏽 account balance(balance): {wallet_balance:,.2f} USDT"
                )
                print(
                    f"      👉🏽 account balance(margin balance): {margin_balance:,.2f} USDT"
                )
                print(
                    f"      👉🏽 account balance(init margin): {init_margin:,.2f} USDT"
                )
                print(f"      👉🏽 account balance(unrealized): {unr_pnl:,.2f} USDT")
                print(f"      👉🏽 account balance(ROI): {roi:,.2f} %")

                positions = tr_utils.Extractor.current_positions(q_data)
                for i, v in positions.items():
                    print(f"      👉🏽 account balance(positions): {i}")
            print(f"    ✋ STOP - account_balance")

        def terminal_clear(self):
            os.system("pkill -f *.py")
            os.system("clear")

        def start_message(self):
            print_line = "=" * 50
            print_title = "**     TEST MODE     **"
            print("\n")
            print(print_line.center(80))
            print(print_title.center(80))
            print(print_line.center(80))
            print("\n")

        async def start(self):
            self.terminal_clear()
            self.start_message()
            tasks = [
                asyncio.create_task(self.receiver_manager.start()),
                asyncio.create_task(self.timer()),
                asyncio.create_task(self.print_from_queue_kline()),
                asyncio.create_task(self.print_from_queue_orderbook()),
                asyncio.create_task(self.print_from_queue_order_status()),
                asyncio.create_task(self.print_from_queue_account_balance()),
            ]
            await asyncio.gather(*tasks)

    args = []
    for _ in range(11):
        args.append(asyncio.Queue())
    for _ in range(18):
        args.append(asyncio.Event())
    args = tuple(args)

    instance = RunTestFetcher(*args)
    asyncio.run(instance.start())
