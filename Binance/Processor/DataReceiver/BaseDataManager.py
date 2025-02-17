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

    def __init__(self, ws_receiver):  # , symbols:List, intervals:List):
        self.ws_receiver = ws_receiver

    async def kline_limit_run(self, max_retries: int = 10):
        """
        ⭕️ kline형태의 웹소켓을 수신한다.

        Args:
            max_retries (int, optional): 오류 횟수도달시 프로그램 종료
        """
        print("  👉🏻 🚀 웹소켓(캔들) 함수 시작.")
        retry_count = 0
        while retry_count < max_retries:
            try:
                await self.ws_receiver.connect_kline_limit()
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                print(f"    🚨 연결오류 발생: {e}")
                retry_count += 1
                print(f"    ⏳ 재접속 중... {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print("    💥 최대 재시도 횟수 도달, WebSocket 종료.")
        raise ValueError(f"복구 불가, 강제종료")

    async def stream_run(self, stream_type: str, max_retries: int = 10):
        retry_count = 0
        while retry_count < max_retries:
            try:
                await self.ws_receiver.connect_stream(stream_type)
                retry_count = 0  # 성공 시 초기화
            except Exception as e:
                print(f"    🚨 연결오류 발생: {e}")
                retry_count += 1
                print(f"    ⏳  재접속 중...  {retry_count}/{max_retries}")
                await asyncio.sleep(5)
        print("    💥 최대 재시도 횟수 도달, WebSocket 종료.")
        raise ValueError(f"복구 불가, 강제종료")
