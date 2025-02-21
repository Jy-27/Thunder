from .MarketWebsocket import MarketWebsocket
from typing import Union, List, Final
import asyncio
import aiohttp


class FuturesMarketWebsocket(MarketWebsocket):
    """
    ℹ️ Futures 거래내역 웹소켓이다.
    매개변수의 session은 변할일이 없을것으로 판단되어,
    의존성 생성처리 하였다.

    Alias: futures_mk_ws

    Args:
        symbols (List): 심볼 리스트
    """
    def __init__(
        self, symbols: List):
        super().__init__(
            base_url="wss://stream.binance.com:9443/ws/",
            symbols=symbols,
            session=aiohttp.ClientSession())

if __name__ == "__main__":
    import os
    import sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    from SystemConfig import Streaming
    async def main():
        """
        🚀 테스트용 실행함수
        """
        symbols = Streaming.symbols
        intervals = Streaming.intervals

        ws_receiver = FuturesMarketWebsocket(symbols)
        await ws_receiver.setup_kline_stream(intervals)
        # await ws_receiver.setup_general_stream("depth")
        print("\n")
        print("🚀 Websocket Open!!\n")
        for _ in range(3):
            data = await ws_receiver.receive_data()
            print(data)
        await ws_receiver.close()
        print("\n👍🏻 Websocket Close!!")
        
    asyncio.run(main())

    # 실행 명령어: python3 -m Workspace.Services.PublicData.Receiver.FuturesWebsocketReceiver
