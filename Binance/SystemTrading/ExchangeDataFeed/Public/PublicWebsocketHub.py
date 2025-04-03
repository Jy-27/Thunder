from typing import List, Dict, Optional
import aiohttp

import asyncio
import sys, os
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Workspace.Utils.TradingUtils as tr_utils

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket

class PublicWebsocketHub:
    def __init__(self,
                 symbols:List[str],
                 intervals:List[str],
                 queue_feed_websocket_ticker:asyncio.Queue,
                 queue_feed_websocket_trade:asyncio.Queue,
                 queue_feed_websocket_miniTicker:asyncio.Queue,
                 queue_feed_websocket_depth:asyncio.Queue,
                 queue_feed_websocket_aggTrade:asyncio.Queue,
                 queue_feed_websocket_kline:asyncio.Queue,
                 
                 event_trigger_shutdown_loop:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_websocket_ticker:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_trade:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_miniTicker:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_depth:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_aggTrade:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_kline:asyncio.Event,
                 
                 event_fired_done_public_websocket_hub:asyncio.Event,
                 websocket_timeout:float = 1.0
                 ):
        
        self.symbols = symbols
        self.intervals = intervals
        self.queue_feed_websocket_ticker = queue_feed_websocket_ticker
        self.queue_feed_websocket_trade = queue_feed_websocket_trade
        self.queue_feed_websocket_miniTicker = queue_feed_websocket_miniTicker
        self.queue_feed_websocket_depth = queue_feed_websocket_depth
        self.queue_feed_websocket_aggTrade = queue_feed_websocket_aggTrade
        self.queue_feed_websocket_kline = queue_feed_websocket_kline
        
        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop
        
        self.event_fired_done_shutdown_loop_websocket_ticker = event_fired_done_shutdown_loop_websocket_ticker
        self.event_fired_done_shutdown_loop_websocket_trade = event_fired_done_shutdown_loop_websocket_trade
        self.event_fired_done_shutdown_loop_websocket_miniTicker = event_fired_done_shutdown_loop_websocket_miniTicker
        self.event_fired_done_shutdown_loop_websocket_depth = event_fired_done_shutdown_loop_websocket_depth
        self.event_fired_done_shutdown_loop_websocket_aggTrade = event_fired_done_shutdown_loop_websocket_aggTrade
        self.event_fired_done_shutdown_loop_websocket_kline = event_fired_done_shutdown_loop_websocket_kline

        self.event_fired_done_public_websocket_hub = event_fired_done_public_websocket_hub

        self.websocket_timeout = websocket_timeout

        self.session:aiohttp.ClientSession = None
        self.websocket_ticker = FuturesMarketWebsocket(self.symbols)
        self.websocket_trade = FuturesMarketWebsocket(self.symbols)
        self.websocket_miniTicker = FuturesMarketWebsocket(self.symbols)
        self.websocket_depth = FuturesMarketWebsocket(self.symbols)
        self.websocket_aggTrade = FuturesMarketWebsocket(self.symbols)
        self.websocket_kline = FuturesMarketWebsocket(self.symbols)

    @tr_utils.Decorator.log_complete()
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

    @tr_utils.Decorator.log_lifecycle()
    async def route_message_ticker(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_ticker.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_ticker.put(message)
        self.event_fired_done_shutdown_loop_websocket_ticker.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def route_message_tread(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_trade.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_trade.put(message)
        self.event_fired_done_shutdown_loop_websocket_trade.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def route_message_miniTicker(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_miniTicker.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_miniTicker.put(message)
        self.event_fired_done_shutdown_loop_websocket_miniTicker.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def route_message_depth(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_depth.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_depth.put(message)
        self.event_fired_done_shutdown_loop_websocket_depth.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def route_message_aggTrage(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_aggTrade.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_aggTrade.put(message)
        self.event_fired_done_shutdown_loop_websocket_depth.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def route_message_kline(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.websocket_kline.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_kline.put(message)
        self.event_fired_done_shutdown_loop_websocket_depth.set()

    @tr_utils.Decorator.log_complete()
    async def connect_all_websockets(self):
        await self.connect_websocket_ticker()
        await self.connect_websocket_tread()
        await self.connect_websocket_miniTicker()
        await self.connect_websocket_depth()
        await self.connect_websocket_aggTrade()
        await self.connect_websocket_kline()
    
    @tr_utils.Decorator.log_complete()
    async def disconnect_all_websockets(self):
        await self.session.close()

    async def start(self):
        await self.connect_all_websockets()
        tasks = [
            asyncio.create_task(self.route_message_ticker()),
            asyncio.create_task(self.route_message_tread()),
            asyncio.create_task(self.route_message_miniTicker()),
            asyncio.create_task(self.route_message_depth()),
            asyncio.create_task(self.route_message_aggTrage()),
            asyncio.create_task(self.route_message_kline()),
        ]
        await asyncio.gather(*tasks)
        await self.disconnect_all_websockets()
        self.event_fired_done_public_websocket_hub.set()
        print(f"  \033[91m🔴 Shutdown\033[0m >> \033[91mPublicWebsocketHub.py\033[0m")
    
if __name__ == "__main__":
    symbols = ["BTCUSDT", "XRPUSDT"]
    intervals = ["1m", "3m"]
    q_ = []
    e_ = []
    for _ in range(6):
        q_.append(asyncio.Queue())
    for _ in range(7):
        e_.append(asyncio.Event())
    q_ = tuple(q_)
    e_ = tuple(e_)
    dummy = PublicWebsocketHub(symbols, intervals, *q_, *e_)
    asyncio.run(dummy.start())