import asyncio
import nest_asyncio
import Services.Receiver.TestWebsocketReceiver as futures_ws
import aiohttp
from SystemConfig import Streaming
import json

nest_asyncio.apply()

symbols = Streaming.symbols
intervals = Streaming.intervals

q_ws_async = asyncio.Queue()

base_url="wss://stream.binance.com:9443/ws/"

class ws_mechine(futures_ws.WebsocketReceiver):
    def __init__(self, base_url:str, symbols:list, queue:asyncio.Queue, ):
        super().__init__(symbols = symbols, base_url = base_url)
        self.queue = queue
        self.intervals = None
        self.stream_type = None
        self.session = aiohttp.ClientSession()
        self.ws = None
        
    async def ws_setting(self, intervals):
        self.intervals = [f"kline_{i}" for i in intervals]
        self.stream_type = "kline"
        url = self._streams(self.intervals)
        self.ws = await self.session.ws_connect(url)
    
    async def receiver_ws(self):
        """
        Raises:
            ValueError: _description_
        """
        message = await self.ws.receive()
        print(message)
        if message.type == aiohttp.WSMsgType.TEXT:
            data = json.loads(message.data)
            await self.queue.put(data)
            print(data)
        elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
            raise ValueError(f"ERROR")

async def main():
    ws = ws_mechine(base_url, symbols, q_ws_async)
    await ws.ws_setting(['3m', '5m'])
    for _ in range(100):
        await ws.receiver_ws()

    await ws.ws.close()
    await ws.session.close()

if __name__ == "__main__":
    asyncio.run(main())