from .MarketWebsocket import MarketWebsocket
from typing import Union, List, Final
import asyncio
import aiohttp
import json

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
            base_url="wss://stream.binance.com:9443",
            symbols=symbols)

if __name__ == "__main__":
    import os
    import sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    from SystemConfig import Streaming

    async def main():
        """
        🚀 테스트용 실행 함수
        """
        # base_url = "wss://stream.binance.com:9443"  # ✅ URL 형식 변경
        symbols = Streaming.symbols
        intervals = Streaming.intervals
        ws_receiver = FuturesMarketWebsocket(symbols=symbols)

        await ws_receiver.setup_kline_stream(intervals)  # ✅ WebSocket 설정
        print("\n🚀 WebSocket 연결 성공!\n")

        try:
            for _ in range(3):
                data = await ws_receiver.receive_message()
                print(data)
                # print(json.dumps(data, indent=2, ensure_ascii=False))  # ✅ JSON 포맷 출력
        except Exception as e:
            print(f"⚠️ 오류 발생: {e}")

        await ws_receiver.close_connection()
        print("\n👍🏻 WebSocket 연결 종료!")

    asyncio.run(main())  # ✅ 메인 실행

    # 실행 명령어: python3 -m Workspace.Services.PublicData.Receiver.FuturesWebsocketReceiver
