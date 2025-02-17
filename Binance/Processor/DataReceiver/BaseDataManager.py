import concurrent.futures
import threading
import datetime
import asyncio
from typing import List, Optional

import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming
# import Utils.DataModels as storage
import Utils.BaseUtils as base_utils

class WebsocketReceiver(Streaming):
    """
    websocket 데이터를 수신한다.

    Args:
        Streaming : SystemConfig.py
    """
    MAX_WORKERS = 5
    def __init__(self, FuturesWebsocketReceiver):
        self.ws_futures = FuturesWebsocketReceiver
        # 매개변수를 고정하여 유연성 제한함. 그냥 그렇게 강제하기로 했음.
        # 필요시 매개변수 입력으로 수정하면 됨.
        self.symbols: List = self.ws_futures.symbols
        self.intervals: List = self.ws_futures.intervals
        self.stream_type: Optional[str] = None

    async def kline_limit_run(self, max_retries: int = 10):
        """
        ⭕️ kline형태의 웹소켓을 수신한다.

        Args:
            max_retries (int, optional): 오류 횟수도달시 프로그램 종료
        """
        retry_count = 0
        while retry_count < max_retries:
            try:
                await self.ws_futures.connect_kline_limit()
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                retry_count += 1
                print(f" ⏳ Reconnection attempt... {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print(" 🚨 최대 재시도 횟수 도달, WebSocket 종료.")

    async def stream_run(self, stream_type: str, max_retries: int = 10):
        self.stream_type = stream_type
        retry_count = 0
        while retry_count < max_retries:
            try:
                await self.ws_futures.connect_stream(stream_type=self.stream_type)
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                print(f" 🚨 Connection error occurred.: {e}")
                retry_count += 1
                print(f" ⏳ Reconnection attempt... {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print(" 🚨 최대 재시도 횟수 도달, WebSocket 종료.")


class KlineHistoryFetcher(Streaming):
    def __init__(self, storage, public_futures):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.kline_limit = Streaming.kline_limit
        self.storage = storage
        self.public_futures = public_futures

    def get_data(self, symbol: str, interval: str):
        return self.public_futures.fetch_klines_limit(
            symbol=symbol, interval=interval, limit=self.kline_limit
        )

    def update_data(self, symbol: str, interval: str, data: List):
        self.storage.update_data(symbol=symbol, interval=interval, data=data)

    def run(self, symbol: str, interval: str):
        data = self.get_data(symbol=symbol, interval=interval)
        self.update_data(symbol=symbol, interval=interval, data=data)
