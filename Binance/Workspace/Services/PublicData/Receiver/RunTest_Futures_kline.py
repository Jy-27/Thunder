import asyncio
import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))

from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import (
    FuturesMarketWebsocket as futures_mk_ws,
)
import SystemConfig

symbols = SystemConfig.Streaming.symbols
intervals = SystemConfig.Streaming.intervals

obj = futures_mk_ws(symbols)


async def run_receive():
    print(f"⏳ 웹소켓(kline) 연결중...")
    await obj.open_kline_connection(intervals)
    print(f"🔗 웹소켓(kline) 연결 완료.")
    for _ in range(10):
        message = await obj.receive_message()
        print(message)
    print(f"✅ 데이터 수신 완료.")
    await obj.close_connection()
    print(f"⛓️‍💥 웹소켓(kline) 해제 완료.")


if __name__ == "__main__":
    asyncio.run(run_receive())
