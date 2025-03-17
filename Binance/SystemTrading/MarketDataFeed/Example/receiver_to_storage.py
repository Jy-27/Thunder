import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager
from SystemTrading.TradingDataHub.MarketDataStorage import RecevierDataStorage

queues = []
for i in range(9):
    queues.append(asyncio.Queue())
queues = tuple(queues)
event = asyncio.Event()

async def main():
    ins_receiver = ReceiverManager(*queues, event)
    ins_storage = RecevierDataStorage(*queues)
    tasks = [asyncio.create_task(ins_receiver.start()),
             asyncio.create_task(ins_storage.start())]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())