import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.TradingDataHub.ReceiverDataStorage.MarketDataStorage import ReceiverDataStorage
from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager

q = [asyncio.Queue() for _ in range(11)]
stop_event = asyncio.Event()

q_storage = [asyncio.Queue() for _ in range(6)]

e_recv = [asyncio.Event() for _ in range(17)]
e_storage = [asyncio.Event() for _ in range(58)]

class RunTest:
    def __init__(self):
        self.ins_mk_db_storage = ReceiverDataStorage(*q, *q_storage, stop_event, *e_storage)
        self.ins_recv_manager = ReceiverManager(*q, stop_event, *e_recv)
    
    async def stop_timer(self):
        await asyncio.sleep(10)
        print(f"  ⚠️ ⏱️ stop timer 시작: 60sec")
        await asyncio.sleep(60)
        print(f"    💥 stop event 활성화")
        stop_event.set()

    async def timer_fetcher(self):
        while not stop_event.is_set():
            self.ins_mk_db_storage.event_trigger_clear_order_status.set()
            await asyncio.sleep(5)
            for event in e_recv[:3]:
                event.set()

    def start_message(self):
        print_line = "=" * 50
        print_title = "**     TEST MODE     **"
        print("\n")
        print(print_line.center(80))
        print(print_title.center(80))
        print(print_line.center(80))
        print("\n")    

    async def start(self):
        self.start_message()
        tasks = [
            asyncio.create_task(self.ins_recv_manager.start()),
            asyncio.create_task(self.ins_mk_db_storage.start()),
            asyncio.create_task(self.stop_timer()),
            asyncio.create_task(self.timer_fetcher())
        ]
        await asyncio.gather(*tasks)
        
if __name__ == "__main__":
    instance = RunTest()
    asyncio.run(instance.start())
            