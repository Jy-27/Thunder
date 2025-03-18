import asyncio
import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import (
    FuturesMarketWebsocket as futures_mk_ws,
)
from SystemConfig import Streaming


class StreamReceiverWebsocket:
    """
    🐣 WebSocket 스트림

    Args:
        stream_type (str): 스트림 타입
            - ticker: 개별 심볼에 대한 전체 티커 정보 제공
            - trade: 개별 거래 정보 제공
            - miniTicker: 심볼별 간소화된 티커 정보 제공
            - depth: 주문서 정보 제공
            - 24hrTicker: 24시간 동안 롤링 통계 정보 제공
            - aggTrade: 집계된 거래 정보 제공
    """

    def __init__(
        self, stream_type: str, queue: asyncio.Queue, event_loop_status: asyncio.Event
    ):
        self.symbols = Streaming.symbols
        self.stream_type = stream_type
        self.futures_mk_ws = futures_mk_ws(self.symbols)
        self.queue = queue
        self.event_loop_status = event_loop_status

    async def start(self):
        print(f"  ⏳ ReceiverWebsocket({self.stream_type}) 연결중.")
        await self.futures_mk_ws.open_stream_connection(self.stream_type)
        print(f"  🔗 ReceiverWebsocket({self.stream_type}) 연결 성공.")
        print(f"  🚀 ReceiverWebsocket({self.stream_type}) 시작")
        while not self.event_loop_status.is_set():
            message = await self.futures_mk_ws.receive_message()
            await self.queue.put(message)
        print(f"  ⁉️ ReceiverWebsocket({self.stream_type}) Loop 종료됨")
        await self.futures_mk_ws.close_connection()
        print(f"  ⛓️‍💥 ReceiverWebsocket({self.stream_type}) 연결 해제")


if __name__ == "__main__":
    q_ = asyncio.Queue()
    e_ = asyncio.Event()
    obj = StreamReceiverWebsocket("trade", q_, e_)
    asyncio.run(obj.start())
