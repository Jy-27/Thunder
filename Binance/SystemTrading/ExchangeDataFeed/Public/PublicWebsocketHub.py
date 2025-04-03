from typing import List, Dict, Optional
import aiohttp

import asyncio
import sys, os
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Workspace.Utils.TradingUtils as tr_utils

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket

class PublicWebsocketHub:
    def __init__(self, symbols:List[str], intervals:List[str]):
        self.symbols = symbols
        self.intervals = intervals
        self.session:aiohttp.ClientSession = None
        self.websocket_ticker = FuturesMarketWebsocket(self.symbols)
        self.websocket_trade = FuturesMarketWebsocket(self.symbols)
        self.websocket_miniTicker = FuturesMarketWebsocket(self.symbols)
        self.websocket_depth = FuturesMarketWebsocket(self.symbols)
        self.websocket_aggTrade = FuturesMarketWebsocket(self.symbols)
        self.websocket_kline = FuturesMarketWebsocket(self.symbols)

    async def initialize_session(self, session:Optional[aiohttp.ClientSession]=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_ticker(self):
        stream = "ticker"
        await self.websocket_ticker.open_stream_connection(stream, self.session)

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_tread(self):
        stream = "trade"
        await self.websocket_trade.open_stream_connection(stream, self.session)

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_miniTicker(self):
        stream = "miniTicker"
        await self.websocket_miniTicker.open_stream_connection(stream, self.session)

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_depth(self):
        stream = "depth"
        await self.websocket_depth.open_stream_connection(stream, self.session)

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_aggTrade(self):
        stream = "aggTrade"
        await self.websocket_aggTrade.open_stream_connection(stream, self.session)

    @tr_utils.Decorator.log_ws_connect()
    async def connect_websocket_kline(self):
        await self.websocket_kline.open_kline_connection(self.intervals, self.session)

    async def connect_all_websockets(self):
        await self.initialize_session()
        tasks = [
            asyncio.create_task(self.connect_websocket_ticker()),
            asyncio.create_task(self.connect_websocket_tread()),
            asyncio.create_task(self.connect_websocket_miniTicker()),
            asyncio.create_task(self.connect_websocket_depth()),
            asyncio.create_task(self.connect_websocket_aggTrade()),
            asyncio.create_task(self.connect_websocket_kline()),
        ]
        await asyncio.gather(*tasks)
    
if __name__ == "__main__":
    symbols = ["BTCUSDT", "XRPUSDT"]
    intervals = ["1m", "3m"]
    dummy = PublicWebsocketHub(symbols, intervals)
    asyncio.run(dummy.main())