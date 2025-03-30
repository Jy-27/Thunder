import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager
import Workspace.Utils.TradingUtils as tr_utils
import SystemConfig

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
                
                print(i)
                
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

    async def monitor_event_kline(self):
        while True:
            try:
                await asyncio.wait_for(self.receiver_manager.event_fired_done_kline.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            print(f"        🚨 kline 완료 신호 발생")
            break
        
    async def monitor_event_orderbook(self):
        while True:
            try:
                await asyncio.wait_for(self.receiver_manager.event_fired_done_orderbook.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            print(f"        🚨 orderbook 완료 신호 발생")
            break

    async def monitor_event_private(self):
        while True:
            try:
                await asyncio.wait_for(self.receiver_manager.event_fired_done_private.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            print(f"        🚨 private 완료 신호 발생")
            break

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
            asyncio.create_task(self.monitor_event_kline()),
            asyncio.create_task(self.monitor_event_orderbook()),
            asyncio.create_task(self.monitor_event_private()),
        ]
        await asyncio.gather(*tasks)
        
if __name__ == "__main__":
    args = []
    for _ in range(11):
        args.append(asyncio.Queue())
    for _ in range(18):
        args.append(asyncio.Event())
    args = tuple(args)

    instance = RunTestFetcher(*args)
    asyncio.run(instance.start())