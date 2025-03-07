import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket as futures_mk_ws
from SystemConfig import Streaming
import Workspace.Utils.TradingUtils as tr_utils

class KlineReceiverWebsocket:
    def __init__(self, queue:asyncio.Queue):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.futures_mk_ws = futures_mk_ws(self.symbols)
        self.queue = queue
    
    async def start(self):
        print(f"  ⏳ KlineReceiverWebsocket 연결중.")
        await self.futures_mk_ws.open_kline_connection(self.intervals)
        print(f"  🔗 KlineReceiverWebsocket 연결 성공.")
        print(f"  🚀 KlineReceiverWebsocket 시작")
        while True:
            message = await self.futures_mk_ws.receive_message()
            pack_data = tr_utils.Packager.pack_kline_websocket_message(message)
            await self.queue.put(pack_data)

if __name__ == "__main__":
    q_ = asyncio.Queue()
    obj = KlineReceiverWebsocket(q_)
    asyncio.run(obj.start())