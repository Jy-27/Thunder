import asyncio
import ast
import time

from typing import Dict

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig
class WalletManager:
    def __init__(self,
                 queue_request_wallet:asyncio.Queue,
                 queue_response_wallet:asyncio.Queue,
                 queue_feed_wallet:asyncio.Queue,
                 event_trigger_stop_loop:asyncio.Event,
                 event_trigger_private:asyncio.Event,
                 event_fired_done_private:asyncio.Event):
        
        self.queue_request_wallet = queue_request_wallet
        self.queue_response_wallet = queue_response_wallet
        self.queue_feed_wallet = queue_feed_wallet
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_trigger_private = event_trigger_private
        self.event_fired_done_private = event_fired_done_private
        
        self._event_data_ready = asyncio.Event()
        
        self.symbols = SystemConfig.Streaming.symbols
        self.account_position = None
        self.target_keys = SystemConfig.Keys.position_keys
    
    async def convert_to_enqueue_wallet(self, account_position:Dict) -> Dict:
        result = {}
        for i, v in data.items():
            if i in self.target_keys:
                if i == "updateTime":
                    result[i] = int(time.time() * 1_000)
                else:
                    if not isinstance(v, int):
                        result[i] = ast.literal_eval(v)
                    else:
                        result[i] = v
        packing_message = ("wallet", result)
        await self.queue_feed_wallet.put(packing_message)
        return result
    
    async def convert_to_enqueue_position(self, position:Dict) -> Dict:
        result = {}
        for i, v in position.items():
            if isinstance(v, str):
                result[i] = ast.literal_eval(v)
            else:
                result[i] = v
        packing_message = ("position", result)
        await self.queue_feed_wallet.put(packing_message)
        return result

    async def send_request_to_market_storage(self):
        print(f"  🚀 WalletManager: wallet storage 데이터 요청시작.")
        message = "account_balance"
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_private.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self.queue_request_wallet.put(message)
            self.event_trigger_private.clear()
        print(f"  🖐🏻 WalletManager: wallet storage 데이터 요청 종료됨")
        
    async def receiver_response_from_stroage(self):
        print(f"  🚀 WalletManager: wallet storage 데이터 수신시작.")
        while not self.event_trigger_stop_loop.is_set():
            try:
                self.account_position = await asyncio.wait_for(self.queue_response_wallet.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.queue_response_wallet.task_done()
            self._event_data_ready.set()
        print(f"  🖐🏻 WalletManager: wallet storage 데이터 수신 종료됨")

    async def send_result_to_status_storage(self):
        print(f"  🚀 WalletManager: wallet status storage 발신 시작.")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self._event_data_ready.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            await self.convert_to_enqueue_wallet(self.account_position)
            for position in self.account_position["positions"]:
                await self.convert_to_enqueue_position(position)
            self._event_data_ready.clear()
        print(f"  🚀 WalletManager: wallet status storage 발신 종료됨")
    
    async def start(self):
        tasks = [
            asyncio.create_task(self.receiver_response_from_stroage()),
            asyncio.create_task(self.send_request_to_market_storage()),
            asyncio.create_task(self.send_result_to_status_storage())]
        await asyncio.gather(*tasks)
        print(f"  ℹ️ WalletManager가 종료되어 작업 중단됨")

if __name__ == "__main__":
    args = []
    for _ in range(3):
        args.append(asyncio.Queue())
    for _ in range(3):
        args.append(asyncio.Event())
    args = tuple(args)
    
    instance = WalletManager(*args)
    asyncio.run(instance.start())