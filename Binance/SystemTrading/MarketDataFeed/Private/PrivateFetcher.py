import asyncio

import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig
import Workspace.Utils.BaseUtils as base_utils
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import (
    FuturesTradingClient,
)

symbols = SystemConfig.Streaming.symbols

path_api = SystemConfig.Path.bianace
api = base_utils.load_json(path_api)
ins_futures_tr_client = FuturesTradingClient(**api)


class PrivateFetcher:
    """
    Websocket execution신호 수신시 발생하는 asyncio.Event신호를 수신받아 
    포지션 및 주문관련 상태를 업데이트한다. 업데이트 된 데이터는 Trading Data Hub의 TradingStatus저장소에 보관한다.
    
    Notes:
        class AccountStatus 와 연결됨.
    """
    def __init__(
        self,
        queue_fetch_account_balance:asyncio.Queue,
        queue_fetch_order:asyncio.Queue,
        event_trigger_private:asyncio.Event,
        event_fired_done_private:asyncio.Event,
        event_trigger_stop_loop: asyncio.Event,
        event_fired_loop_status:asyncio.Event):
        
        self.queue_fetch_account_balance = queue_fetch_account_balance
        self.queue_fetch_order = queue_fetch_order
        self.event_trigger_private = event_trigger_private
        self.event_fired_done_private = event_fired_done_private
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_loop_status = event_fired_loop_status

    async def fetch_account_balance(self):
        data = await ins_futures_tr_client.fetch_account_balance()
        await self.queue_fetch_account_balance.put(data)
        return data

    async def fetch_order_status(self, symbol: str):
        data = await ins_futures_tr_client.fetch_order_status(symbol)
        if data:
            await self.queue_fetch_order.put(data)
        return data

    async def tasks(self):
        tasks = [
            *[asyncio.create_task(self.fetch_order_status(symbol)) for symbol in symbols],
            asyncio.create_task(self.fetch_account_balance())
        ]
        await asyncio.gather(*tasks)

    async def start(self):
        print(f"  PrivateFetcher: 🚀 Starting to fetch")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_private.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self.tasks()
            self.event_trigger_private.clear()
            self.event_fired_done_private.set()
        print(f"  PrivateFetcher: ✋ Loop stopped")
        self.event_fired_loop_status.set()

if __name__ == "__main__":
    class RunTest:
        def __init__(self, t:int = 10):
            self.t = t
            self.q_1 = asyncio.Queue()
            self.q_2 = asyncio.Queue()
            self.e_1 = asyncio.Event()
            self.e_2 = asyncio.Event()
            self.e_3 = asyncio.Event()
            self.ins_fetcher = PrivateFetcher(self.q_1,
                                              self.q_2,
                                              self.e_1,
                                              self.e_2,
                                              self.e_3)

        async def timer(self):
            print(f"  ⏳ 타이머 시작: {self.t}sec")
            await asyncio.sleep(self.t)
            self.e_1.set()
            print(f"  🚀 event 신호 생성")
            await asyncio.sleep(2)
            self.e_2.set()
            print(f"  ✋ Stop Signal 생성")
        
        async def get_account_balance(self):
            while not self.e_2.is_set():
                try:
                    message = await asyncio.wait_for(self.q_1.get(), timeout=0.5)
                    # print(message)
                    self.q_1.task_done()
                except asyncio.TimeoutError:
                    continue
            print(f"  ✋ account balance loop stop")
                
        async def get_order_status(self):
            while not self.e_2.is_set():
                try:
                    message = await asyncio.wait_for(self.q_2.get(), timeout=0.5)
                    print(message)
                    self.q_2.task_done()
                except asyncio.TimeoutError:
                    continue
            print(f"  ✋ account order status stop")
            
        async def start(self):
            tasks = [
                asyncio.create_task(self.timer()),
                asyncio.create_task(self.ins_fetcher.start()),
                asyncio.create_task(self.get_account_balance()),
                asyncio.create_task(self.get_order_status())
            ]
            await asyncio.gather(*tasks)
    
    instance = RunTest()
    asyncio.run(instance.start())