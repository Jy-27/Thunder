import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager
from SystemTrading.TradingDataHub.MarketDataStorage import ReceiverDataStorage

queues = []
for i in range(10):
    queues.append(asyncio.Queue())
queues = tuple(queues)
events = []
for i in range(2):
    events.append(asyncio.Event())

async def stop_timer(time:int=5):
    await asyncio.sleep(time)
    print(f"  🚨 신호 발생")
    events[0].set()

async def main():
    ins_receiver = ReceiverManager(*queues, events[0])
    ins_storage = ReceiverDataStorage(*queues, *events)
    tasks = [
        asyncio.create_task(stop_timer()),
        asyncio.create_task(ins_receiver.start()),
        asyncio.create_task(ins_storage.start()),
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    """
    데이터 수신 후 스토리지에 저장기능을 테스트한다.
    """
    asyncio.run(main())
