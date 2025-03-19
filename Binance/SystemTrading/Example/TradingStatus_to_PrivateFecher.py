import asyncio
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.TradingDataHub.AccountStatus import AccountStatus
from SystemTrading.MarketDataFeed.Private.PrivateFetcher import PrivateFetcher

queues = []
events = []

for _ in range(2):
    queues.append(asyncio.Queue())
    events.append(asyncio.Event())

queues = tuple(queues)
events = tuple(events)

ins_status = AccountStatus(*queues, events[1])
ins_private_fetcher = PrivateFetcher(*queues, *events)

async def set_event():
    while True:
        await asyncio.sleep(5)
        events[0].set()
        print("  🚀 SET 실행!!")

async def run_storage():
    while True:
        print("\n")
        print(ins_status.ins_account_balance_status)
        print(ins_status.ins_order_status)
        print(ins_status.ins_positions_status)
        await asyncio.sleep(5)

async def main():
    tasks = [
        asyncio.create_task(set_event()),
        # asyncio.create_task(run_storage()),
        asyncio.create_task(ins_status.start()),
        asyncio.create_task(ins_private_fetcher.start())
        ]
    await asyncio.gather(*tasks)
    
if __name__ == "__main__":
    """
    Websocket(execution)신호 발생시 account_position(REST)정보를 수신 후 각 스토리지에 업데이트한다.
    
    Websocket(execution)신호는 가상으로 발생시킨다.
    """
    asyncio.run(main())