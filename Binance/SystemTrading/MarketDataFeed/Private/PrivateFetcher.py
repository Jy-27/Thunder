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
        queue_account_balance: asyncio.Queue,
        queue_order_status: asyncio.Queue,
        event_start_signal: asyncio.Event,
        event_loop_start: asyncio.Event,
    ):
        self.queue_account_balance = queue_account_balance
        self.queue_order_status = queue_order_status
        self.event_start_signal = event_start_signal
        self.event_loop_start = event_loop_start

    async def fetch_account_balance(self):
        data = await ins_futures_tr_client.fetch_account_balance()
        await self.queue_account_balance.put(data)
        return data

    async def fetch_order_status(self, symbol: str):
        data = await ins_futures_tr_client.fetch_order_status(symbol)
        await self.queue_order_status.put(data)
        return data

    async def fetch_all_order_statuses(self):
        tasks = [
            asyncio.create_task(self.fetch_order_status(symbol)) for symbol in symbols
        ]
        await asyncio.gather(*tasks)

    async def debug(self):
        balance_data = await self.fetch_account_balance()
        order_data = await self.fetch_order_status("BTCUSDT")
        return balance_data, order_data

    async def start(self):
        print(f"  🚀 PrivateFetcher 시작.")
        while not self.event_loop_start.is_set():
            await self.event_start_signal.wait()
            await self.fetch_account_balance()
            await self.fetch_all_order_statuses()
            self.event_start_signal.clear()
        print(f"  ⁉️ PrivateFetcher 중단.")


if __name__ == "__main__":
    queues = []
    for _ in range(2):
        queues.append(asyncio.Queue())
    queues = tuple(queues)
    
    events = []
    for _ in range(2):
        events.append(asyncio.Event())
    events = tuple(events)

    obj = PrivateFetcher(*queues, *events)
    balance, order = asyncio.run(obj.debug())  # ("BTCUSDT"))#, 623593178246))
