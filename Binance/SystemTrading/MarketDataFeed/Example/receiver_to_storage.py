import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager
from SystemTrading.TradingDataHub.MarketDataStorage import RecevierDataStorage

queues = []
for i in range(9):
    queues.append(asyncio.Queue())
queues = tuple(queues)
event_1 = asyncio.Event()
event_2 = asyncio.Event()


# async def timer(sec: int):
#     print(f"  ⏳ timer {sec} 초 시작.")
#     # await asyncio.sleep(sec)
#     # event_2.set()


async def main():
    ins_receiver = ReceiverManager(*queues, event_1, event_2)
    ins_storage = RecevierDataStorage(*queues, event_2)
    tasks = [
        asyncio.create_task(ins_receiver.start()),
        asyncio.create_task(ins_storage.start()),
    ]
    # asyncio.create_task(timer(10)),
    # ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
