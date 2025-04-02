import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import (
    FuturesMarketWebsocket as futures_mk_ws,
)
from SystemConfig import Streaming
import Workspace.Utils.TradingUtils as tr_utils


class KlineReceiverWebsocket:
    def __init__(self,
                 queue_feed_kline_ws: asyncio.Queue,
                 event_trigger_stop_loop: asyncio.Event,
                 event_fired_stop_loop_done_ws_kilne: asyncio.Event):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.futures_mk_ws = futures_mk_ws(self.symbols)
        self.queue_feed_kline_ws = queue_feed_kline_ws
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_stop_loop_done_ws_kilne = event_fired_stop_loop_done_ws_kilne

    async def start(self):
        print(f"  KlineReceiverWebsocket: ⏳ Connecting >> Kline")
        await self.futures_mk_ws.open_kline_connection(self.intervals)
        print(f"  KlineReceiverWebsocket: 🔗 Connected successfully >> Kline")
        print(f"  KlineReceiverWebsocket: 🚀 Starting to receive >> Kline")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.futures_mk_ws.receive_message()
            pack_data = tr_utils.Packager.pack_kline_websocket_message(message)
            await self.queue_feed_kline_ws.put(pack_data)
        print(f"  KlineReceiverWebsocket: ✋ Loop stopped >> Kline")
        await self.futures_mk_ws.close_connection()
        print(f"  KlineReceiverWebsocket: ⛓️‍💥 Disconnected >> Kline")
        self.event_fired_stop_loop_done_ws_kilne.set()

if __name__ == "__main__":
    q_ = asyncio.Queue()
    obj = KlineReceiverWebsocket(q_)
    asyncio.run(obj.start())
