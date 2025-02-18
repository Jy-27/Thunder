from .WebsocketReceiver import WebsocketReceiver
from typing import Union, List, Final
import asyncio
import aiohttp

import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))


class FuturesWebsocketReceiver(WebsocketReceiver):
    def __init__(
        self, symbols: List, session: aiohttp.ClientSession, queue: asyncio.Queue
    ):
        super().__init__(
            base_url="wss://stream.binance.com:9443/ws/",
            symbols=symbols,
            session=session,
            queue=queue,
        )


if __name__ == "__main__":
    from SystemConfig import Streaming
    async def main():
        """
        🚀 테스트용 실행함수
        """
        symbols = Streaming.symbols
        intervals = Streaming.intervals
        session = aiohttp.ClientSession()
        queue = asyncio.Queue()

        ws_receiver = FuturesWebsocketReceiver(symbols, session, queue)
        # await ws_receiver.setup_kline_stream(intervals)
        await ws_receiver.setup_general_stream("depth")
        for _ in range(100):
            await ws_receiver.receive_data()
            print(await queue.get())

    asyncio.run(main())

    # 실행 명령어: python3 -m Services.Receiver.FuturesWebsocketReceiver
