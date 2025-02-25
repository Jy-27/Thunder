import aiohttp
import json
import asyncio
from typing import Dict, List, Optional, Final, Union

class MarketWebsocket:
    """
    웹소켓 실행을 위한 기본 클래스
    
    Alias: mk_ws
    """

    def __init__(
        self,
        base_url: str,
        symbols: List[str],
        session: aiohttp.ClientSession
        ):
        self.base_url = base_url
        self.symbols = symbols
        self.session = session
        self.stream_type: Optional[str] = None
        self.interval_streams: Optional[List[str]] = None
        self.websocket = None

    def _build_stream_url(self, stream_types: List) -> str:
        """
        👻 WebSocket 스트림 URL을 생성한다.

        Args:
            stream_types (Union[List[str], str]): 스트림 타입 리스트 또는 단일 타입

        Returns:
            str: 완성된 WebSocket 스트림 URL
        """
        endpoints = [stream for stream in stream_types]
        return self.base_url + "/".join(
            [
                f"{symbol.lower()}@{endpoint}"
                for symbol in self.symbols
                for endpoint in endpoints
            ]
        )

    async def setup_kline_stream(self, intervals: List[str]):
        """
        🐣 'kline' 스트림 설정

        Args:
            intervals (List[str]): 원하는 캔들스틱 인터벌 리스트
        """
        self.stream_type = "kline"
        self.interval_streams = [f"{self.stream_type}_{i}" for i in intervals]
        stream_url = self._build_stream_url(self.interval_streams)
        async with aiohttp.ClientSession() as session:  # ✅ 명확한 세션 관리
            async with session.ws_connect(stream_url) as ws:
                self.websocket = ws
        # self.websocket = await self.session.ws_connect(url)


    # async def setup_general_stream(self, stream_url):
    #     async with aiohttp.ClientSession() as session:  # ✅ 명확한 세션 관리
    #         async with session.ws_connect(stream_url) as ws:
    #             self.websocket = ws
    #             # async for message in ws:
                #     print("Received:", message.data)  # 데이터 처리 로직 추가


    async def setup_general_stream(self, stream_type: str):
        """
        🐣 'kline'이 아닌 일반 WebSocket 스트림 설정

        Args:
            stream_type (str): 스트림 타입
                - ticker: 개별 심볼에 대한 전체 티커 정보 제공
                - trade: 개별 거래 정보 제공
                - miniTicker: 심볼별 간소화된 티커 정보 제공
                - depth: 주문서 정보 제공
                - 24hrTicker: 24시간 동안 롤링 통계 정보 제공
                - aggTrade: 집계된 거래 정보 제공
        """
        self.stream_type = [stream_type]
        self.interval_streams = None
        url = self._build_stream_url(self.stream_type)
        self.websocket = await self.session.ws_connect(url)

    async def receive_data(self):
        """
        🚀 WebSocket 데이터를 수신 및 반환한다.

        Notes:
            본 함수를 반복문으로 실행해야 지속적인 데이터 수신을 유지한다.
        """
        message = await self.websocket.receive()
        if message.type == aiohttp.WSMsgType.TEXT:
            return json.loads(message.data)
        elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
            raise ConnectionError(f"websocket 연결 오류.")

    async def close(self):
        await self.session.close()


if __name__ == "__main__":
    import os
    import sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    import SystemConfig
    async def main():
        """
        🚀 테스트용 실행함수
        """
        base_url = "wss://stream.binance.com:9443/ws/"
        symbols = SystemConfig.Streaming.symbols
        intervals = SystemConfig.Streaming.intervals
        session = aiohttp.ClientSession()
        ws_receiver = MarketWebsocket(base_url, symbols, session)
        await ws_receiver.setup_kline_stream(intervals)
        print("\n")
        print("🚀 Websocket Open!!\n")
        for _ in range(3):
            data = await ws_receiver.receive_data()
            print(data)
        await ws_receiver.close()
        
        print("\n👍🏻 Websocket Close!!")

    asyncio.run(main())

    # 실행 명령어: python3 -m Workspace.Services.Receiver.WebsocketReceiver