import concurrent.futures
import threading
import datetime
import asyncio
from typing import List, Optional

import os
import sys

sys.path.append(os.path.abspath("../../"))
from SystemConfig import Streaming

import API.Queries.Private.PrivateAPI as private_p
import API.Queries.Public.Futures as public_api
import API.Reciver.Futures as reciver_api
import Utils.DataModels as storage
import Utils.BaseUtils as base_utils


# 힌트용
ins_public_api = public_api.API()
ins_reciver_api = reciver_api.API(
    symbols=Streaming.symbols, intervals=Streaming.intervals
)
data_storage = storage.SymbolStorage()


class WebSocketManager(Streaming):
    """
    websocket 데이터를 수신한다.

    Args:
        Streaming : SystemConfig.py
    """

    def __init__(self, ins_reciver: ins_reciver_api):
        self.ins_reciver = ins_reciver
        # 매개변수를 고정하여 유연성 제한함. 그냥 그렇게 강제하기로 했음.
        # 필요시 매개변수 입력으로 수정하면 됨.
        self.symbols: List = self.ins_reciver.symbols
        self.intervals: List = self.ins_reciver.intervals
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
                await self.ins_reciver.connect_kline_limit()
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                retry_count += 1
                print(f"⏳{base_utils.get_current_time()}: 재접속 시도중... {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print("최대 재시도 횟수 도달, WebSocket 종료.")

    async def stream_run(self, stream_type: str, max_retries: int = 10):
        self.stream_type = stream_type
        retry_count = 0
        while retry_count < max_retries:
            print(f"Stream({stream_type})")
            try:
                print(f"Date: {base_utils.get_current_time()}")
                await self.ins_reciver.connect_stream(stream_type=self.stream_type)
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                print(f"접속 오류 발생: {e}")
                retry_count += 1
                print(f"재접속 시도... {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print("최대 재시도 횟수 도달, WebSocket 종료.")


class KlineHistoryFetcher(Streaming):
    def __init__(self, symbol_storage: data_storage, ins_public: ins_public_api):
        self.symbols = Streaming.symbols
        self.intervals = Streaming.intervals
        self.kline_limit = Streaming.kline_limit
        self.storage = symbol_storage
        self.ins_public = ins_public

    def get_data(self, symbol: str, interval: str):
        return self.ins_public.fetch_klines_limit(
            symbol=symbol, interval=interval, limit=self.kline_limit
        )

    def update_data(self, symbol: str, interval: str, data: List):
        self.storage.update_data(symbol=symbol, interval=interval, data=data)

    def run(self, symbol: str, interval: str):
        data = self.get_data(symbol=symbol, interval=interval)
        self.update_data(symbol=symbol, interval=interval, data=data)
