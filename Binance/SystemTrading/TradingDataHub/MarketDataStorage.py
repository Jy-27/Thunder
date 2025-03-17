import asyncio
from typing import Dict

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.TradingDataHub.ReceiverDataStorage.StorageDeque import StorageDeque
from SystemTrading.TradingDataHub.ReceiverDataStorage.StorageOverwrite import StorageOverwrite
import SystemTrading.TradingDataHub.ReceiverDataStorage.StorageNodeManager as node_storage
import Workspace.Utils.TradingUtils as tr_utils

class RecevierDataStorage:
    """
    websocket, fetcher 등 market에서 수신된 정보를 분류 및 가공하지 않고 저장한다.
    연산이 필요할때 저장할 용도의 메인 스토리지가 된다.
    """
    def __init__(self,
                 queue_ticker:asyncio.Queue,
                 queue_trade:asyncio.Queue,
                 queue_minTicker:asyncio.Queue,
                 queue_depth:asyncio.Queue,
                 queue_aggTrade:asyncio.Queue,
                 queue_kline_ws:asyncio.Queue,
                 queue_execution_ws:asyncio.Queue,
                 queue_kline_fetcher:asyncio.Queue,
                 queue_orderbook_fetcher:asyncio.Queue,
                 max_lengh:int = 300):
        self.queue_ticker = queue_ticker
        self.queue_trade = queue_trade
        self.queue_minTicker = queue_minTicker
        self.queue_depth = queue_depth
        self.queue_aggTrade = queue_aggTrade
        self.queue_kline_ws = queue_kline_ws
        self.queue_execution_ws = queue_execution_ws
        self.queue_kline_fetcher = queue_kline_fetcher
        self.queue_orderbook_fetcher = queue_orderbook_fetcher
        self.max_lengh = max_lengh
        
        self.stroage_ticker = StorageDeque(self.max_lengh)
        self.storage_trade = StorageDeque(self.max_lengh)
        self.storage_minTicker = StorageDeque(self.max_lengh)
        self.storage_depth = StorageDeque(self.max_lengh)
        self.storage_aggTrade = StorageDeque(self.max_lengh)
        self.storage_kline_ws = node_storage.storage_kline_real
        self.storage_execution_ws = node_storage.storage_execution_ws
        self.storage_kline_fetcher = node_storage.storage_kline_history
        self.storage_orderbook_fetcher = StorageDeque(self.max_lengh)
    
    async def ticker_update(self):
        """
        💾 websocket stream(ticker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_ticker.get()
            stream:str = message["stream"]
            symbol:str = stream.split("@")[0].upper()
            data:Dict = message["data"]
            self.stroage_ticker.add_data(symbol, data)
            self.queue_ticker.task_done()
    
    async def trade_update(self):
        """
        💾 websocket stream(trade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_trade.get()
            stream:str = message["stream"]
            symbol:str = stream.split("@")[0].upper()
            data:Dict = message["data"]
            self.storage_trade.add_data(symbol, data)
            self.queue_trade.task_done()
        
    async def minTicker_update(self):
        """
        💾 websocket stream(minTicker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_trade.get()
            stream:str = message["stream"]
            symbol:str = stream.split("@")[0].upper()
            data:Dict = message["data"]
            self.storage_minTicker.add_data(symbol, data)
            self.queue_trade.task_done()
        
    async def depth_update(self):
        """
        💾 websocket stream(depth) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_trade.get()
            stream:str = message["stream"]
            symbol:str = stream.split("@")[0].upper()
            data:Dict = message["data"]
            self.storage_depth.add_data(symbol, data)
            self.queue_trade.task_done()
        
    async def aggTrade_update(self):
        """
        💾 websocket stream(aggTrade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_trade.get()
            stream:str = message["stream"]
            symbol:str = stream.split("@")[0].upper()
            data:Dict = message["data"]
            self.storage_aggTrade.add_data(symbol, data)
            self.queue_trade.task_done()

    
    async def kline_ws_update(self):
        """
        💾 websocket kline data 타입의 데이터 수신시 스토리지에 저장한다.
        """
        while True:
            packing_message = await self.queue_kline_ws.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_ws.set_data(symbol, convert_to_interval, data)
            self.queue_kline_ws.task_done()
        
    async def execution_ws_update(self):
        """
        💾 websocket 주문 관련 정보 수신시 스토리지에 저장한다.
        """
        while True:
            message = await self.queue_execution_ws.get()
            data_type = message["e"]
            if data_type == "TRADE_LITE":
                symbol = message["s"]
            elif data_type == "ORDER_TRADE_UPDATE":
                symbol = message["o"]["s"]
            elif data_type == "ACCOUNT_UPDATE":
                symbol = message['a']['P'][0]['s']
            
            if symbol in node_storage.symbols:
                self.storage_execution_ws.set_data(symbol, data_type, message)
            await self.queue_execution_ws.task_done()
        
    async def kline_fetcher_update(self):
        """
        💾 kline data 수신시 스토리지에 저장한다.
        """
        while True:
            packing_message = await self.queue_kline_fetcher.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_fetcher.set_data(symbol, convert_to_interval, data)
            self.queue_kline_fetcher.task_done()
            
    async def orderbook_fetcher_update(self):
        """
        💾 OrderBook자료를 저장한다. 데이터는 asyncio.Queue를 사용하여 tuple(symbol, data)형태로 수신한다.
        """
        while True:
            message = await self.queue_orderbook_fetcher.get()
            symbol, data = message
            self.storage_orderbook_fetcher.add_data(symbol, data)
            self.queue_orderbook_fetcher.task_done()
            
        
    async def start(self):
        tasks = [
            asyncio.create_task(self.ticker_update()),
            asyncio.create_task(self.trade_update()),
            asyncio.create_task(self.minTicker_update()),
            asyncio.create_task(self.depth_update()),
            asyncio.create_task(self.aggTrade_update()),
            asyncio.create_task(self.kline_ws_update()),
            asyncio.create_task(self.execution_ws_update()),
            asyncio.create_task(self.kline_fetcher_update()),
            asyncio.create_task(self.orderbook_fetcher_update())]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    queues = []
    for _ in range(9):
        queues.append(asyncio.Queue())
    queues = tuple(queues)
    
    instance = RecevierDataStorage(*queues)
    asyncio.run(instance.start())