import aiohttp
import json
import asyncio
from typing import List, Optional

class MarketWebsocket:
    """
    웹소켓 실행을 위한 기본 클래스
    """

    def __init__(self, base_url: str, symbols: List[str]):
        self.base_url = base_url.rstrip("/")  # ✅ URL 끝의 / 제거
        self.symbols = symbols
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self.stream_type: Optional[str] = None
        self.interval_streams: Optional[List[str]] = None

    def _build_stream_url(self, stream_types: List[str]) -> str:
        """
        👻 WebSocket 스트림 URL을 생성한다.
        """
        endpoints = [stream for stream in stream_types]
        stream_path = "/".join(
            [
                f"{symbol.lower()}@{endpoint}"
                for symbol in self.symbols
                for endpoint in endpoints
            ]
        )
        return f"{self.base_url}/stream?streams={stream_path}"  # ✅ Binance의 올바른 WebSocket URL

    async def open_connection(self, intervals: List[str]):
        """
        🐣 'kline' 스트림 설정
        """
        self.session = aiohttp.ClientSession()  # ✅ 세션을 별도로 유지
        self.stream_type = "kline"
        self.interval_streams = [f"{self.stream_type}_{i}" for i in intervals]
        stream_url = self._build_stream_url(self.interval_streams)
        self.websocket = await self.session.ws_connect(stream_url)  # ✅ WebSocket 연결 유지

    async def receive_message(self):
        """
        🚀 WebSocket 데이터를 수신 및 반환한다.
        """
        if self.websocket is None:
            raise ConnectionError("🔴 WebSocket이 연결되지 않음!")
        
        message = await self.websocket.receive()

        if message.type == aiohttp.WSMsgType.TEXT:
            return json.loads(message.data)  # ✅ JSON 변환 후 반환

        elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
            raise ConnectionError("🔴 WebSocket 연결 오류!")

    async def close_connection(self):
        """🔌 WebSocket 연결 종료"""
        if self.websocket:
            await self.websocket.close()
        if self.session:
            await self.session.close()
        print("🔴 WebSocket 연결 종료")

# ✅ 실행 코드
if __name__ == "__main__":
    import os
    import sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    import SystemConfig

    async def main():
        """
        🚀 테스트용 실행 함수
        """
        base_url = "wss://stream.binance.com:9443"  # ✅ URL 형식 변경
        symbols = SystemConfig.Streaming.symbols
        intervals = SystemConfig.Streaming.intervals
        ws_receiver = MarketWebsocket(base_url, symbols)

        await ws_receiver.setup_kline_stream(intervals)  # ✅ WebSocket 설정
        print("\n🚀 WebSocket 연결 성공!\n")

        try:
            for _ in range(3):
                data = await ws_receiver.receive_message()
                print(json.dumps(data, indent=2, ensure_ascii=False))  # ✅ JSON 포맷 출력
        except Exception as e:
            print(f"⚠️ 오류 발생: {e}")

        await ws_receiver.close_connection()
        print("\n👍🏻 WebSocket 연결 종료!")

    asyncio.run(main())  # ✅ 메인 실행
