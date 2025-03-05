import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket as futures_mk_ws
from SystemConfig import Streaming

class KlineReceiverWebsocket:
    def __init__(self, queue:asyncio.Queue):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.futures_mk_ws = futures_mk_ws(self.symbols)
        self.queue = queue
    
    async def start(self):
        print(f"  ⏳ 웹소켓(kline) 연결중.")
        await self.futures_mk_ws.open_kline_connection(self.intervals)
        print(f"  🔗 웹소켓(kline) 연결 성공.")
        print(f"  🚀 KlineReceiverWebsocket 시작")
        while True:
            message = await self.futures_mk_ws.receive_message()
            await self.queue.put(message)

if __name__ == "__main__":
    q_ = asyncio.Queue()
    obj = KlineReceiverWebsocket(q_)
    asyncio.run(obj.start())