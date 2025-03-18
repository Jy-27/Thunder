import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.BaseUtils as base_utils

import SystemConfig
from SystemTrading.TradingDataHub.TradingStatus.AccountBalanceStatus import AccountBalanceStatus
from SystemTrading.TradingDataHub.TradingStatus.OrderStatus import OrderStatus
from SystemTrading.TradingDataHub.TradingStatus.PositionsStatus import PositionsStatus

queues = []
for _ in range(2):
    queues.append(asyncio.Queue())
queues = (queues)
event = asyncio.Event()

class AccountStatus:
    def __init__(
        self,
        queue_account_balance: asyncio.Queue,
        queue_order_status: asyncio.Queue,
        event_loop_start: asyncio.Event,
    ):
        self.queue_account_balance = queue_account_balance
        self.queue_order_status = queue_order_status
        self.event_loop_start = event_loop_start

        self.ins_account_balance_status = AccountBalanceStatus()
        self.ins_order_status = OrderStatus()
        self.ins_positions_status = PositionsStatus()

    async def update_wallet_and_positions(self):
        print(f"  🚀  wallet & positions 정보 저장소 실행.")
        while not self.event_loop_start.is_set():
            message = await self.queue_account_balance.get()
            
            ### DEBUG ###
            # print(message)
            
            self.ins_positions_status.clear()
            
            convert_to_account = base_utils.convert_dict_to_literal(message)
            self.ins_account_balance_status.set_data(**convert_to_account)
            
            for positions in message["positions"]:
                symbol = positions["symbol"]
                if symbol not in SystemConfig.Streaming.symbols:
                    continue
                conver_to_position = base_utils.convert_dict_to_literal(positions)
                
                self.ins_positions_status.set_data(conver_to_position)
            self.queue_account_balance.task_done()
        print(f"  ⁉️ wallet 정보 저장소 종료됨.")
        
    async def update_order_status(self):
        print(f"  🚀  미치결 주문 정보 저장소 실행.")
        while not self.event_loop_start.is_set():
            message = await self.queue_order_status.get()
            
            self.ins_order_status.clear()
            
            for order in message:
                convert_to_order = base_utils.convert_dict_to_literal(order)
                self.ins_order_status.set_data(convert_to_order)
                print(convert_to_order)
            self.queue_order_status.task_done()
        print(f"  ⁉️  미치결 주문 정보 저장소 종료됨.")

        
    async def start(self):
        tasks = [
            asyncio.create_task(self.update_wallet_and_positions()),
            asyncio.create_task(self.update_order_status()),
        ]
        await asyncio.gather(*tasks)
        