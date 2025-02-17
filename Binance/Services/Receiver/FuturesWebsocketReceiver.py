from .WebsocketReceiver import WebsocketReceiver
from typing import Union, List
import asyncio

import os
import sys
sys.path.append(os.path.abspath("../../"))
from SystemConfig import Streaming

class FuturesWebsocketReceiver(WebsocketReceiver):
    def __init__(self, symbols:List, intervals:List):
        super().__init__(base_url="wss://stream.binance.com:9443/ws/",
                         symbols=symbols)
        self.intervals = intervals