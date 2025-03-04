from typing import List, Dict

import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))


#힌트 제공용
from asyncio import Queue
from aiohttp import ClientSession
from Workspace.Services.PublicData.Receiver.MarketWebsocket import MarketWebsocket

class WebsocketReceiverManager:
    """
    웹소켓 데이터를 수신할 수 있도록 코드 구현하였다.
    🔥 반드시 websocket_receiver는 setup함수를 이용하여 ws_connect에 url반영된 상태로 의존성 주입해야 한다.
    상위 함수(또는 class)에서 구현할 수 있도록 본 클라스에서는 반복 수신 기능을 구현하지 않았다.
    
    Alias: ws_recv_manager
    
    """
    def __init__(self, websocket_receiver:MarketWebsocket, queue:Queue):
        self.websocket_receiver = websocket_receiver
        self.intervals = self.websocket_receiver.interval_streams
        self.queue = Queue()
    
    async def receive_data(self):
        """
        🚀 웹소켓 데이터 수신 함수이다. 1회 실행시 1회 수신한다.
        계속 수신하려면 반복문 내에 배치하면 된다. 데이터는 Queue로 공유된다.
        """
        await self.websocket_receiver.receive_message()
    
    def clear_queue(self):
        """
        🧹 Queue데이터를 지운다. 동기식 함수가 맞다.
        """
        self.queue.get_nowait()
        
    async def get_data(self) -> Dict:
        """
        🚀 수신된 웹소켓 메시지를 queue.get을 통하여 데이터를 꺼낸다.

        Returns:
            Dict: websocket message
        """
        return await self.queue.get()            

if __name__ == "__main__":
    import SystemConfig
    import Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket as futures_wsr
    import asyncio
    
    queue = Queue()
    
    async def main():
        """
        🚀 테스트용 실행함수
        """
        symbols = SystemConfig.Streaming.symbols
        intervals = SystemConfig.Streaming.intervals
        wsr = futures_wsr.FuturesMarketWebsocket(symbols)
        await wsr.open_connection(intervals)
        
        
        
        ins_wsr = WebsocketReceiverManager(wsr, queue)
        print(" 🚀 Websocket 수신 테스트!!")
        for _ in range(3):
            print(await ins_wsr.receive_data())
        print(" 👍🏻 websocket 수신 완료\n")
        
        print(" 🚀 websocket queue 테스트")
        for _ in range(3):
            await ins_wsr.receive_data()
        print(" ℹ️ websocket 수신 완료")
        print(" ℹ️ queue 출력")
        for _ in range(3):
            message = await ins_wsr.get_data()
            print(message)
        print("\n 👍🏻queue 출력 완료")
        ins_wsr.clear_queue()
        await ins_wsr.close()
        
    asyncio.run(main())
        