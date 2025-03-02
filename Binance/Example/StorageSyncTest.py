import asyncio
import numpy as np

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig
from Workspace.DataStorage.NodeStorage import MainStorage, SubStorage
import Workspace.Utils.BaseUtils as base_utils
import Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher as futures_mk_fetcher
import Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket as futures_mk_ws
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.DataStorage.StorageManager import SyncStorage

class StorageSyncTest:
    """
    Storage 동기화를 위한 데이터 수신 및 동기화 테스트 클라스.
    """
    def __init__(self):
        self.symbols = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        self.convert_to_intervals = [f"interval_{i}" for i in self.intervals]
        self.api_path = SystemConfig.Path.bianace
        self.api_load = base_utils.load_json(self.api_path)
        
        self.ins_market_fetcher = futures_mk_fetcher.FuturesMarketFetcher()
        self.ins_websocket = futures_mk_ws.FuturesMarketWebsocket(self.symbols)
        
        self.sub_storage = SubStorage(self.convert_to_intervals)
        self.real_time = MainStorage(self.symbols, self.sub_storage)
        self.history = MainStorage(self.symbols, self.sub_storage)

    def init_update_to_history(self):
        print(f"  🚀 kline data 기초데이터 수신 시작.")
        for symbol in self.symbols:
            for interval in self.intervals:
                data = self.ins_market_fetcher.fetch_klines_limit(symbol, interval, 200)
                convert_to_interval = f"interval_{interval}"
                self.history.set_data(symbol, convert_to_interval, data)
        print(f"  👍 kline data history storage 저장 완료.")
    
    async def ws_connection(self):
        print(f"  🚀 WebSocket 연결 시작.")
        await self.ins_websocket.open_connection(self.intervals)
        print(f"  🚀 WebSocket 연결 성공.")

    async def receive_ws_data(self):
        print(f"  🚀 WebSocket 데이터 수신 시작.")
        for _ in range(100):
            data = await self.ins_websocket.receive_message()
            symbol, interval = tr_utils.Extractor.format_websocket(data)
            klilne_data = tr_utils.Extractor.format_kline_data(data)
            self.real_time.set_data(symbol, f"interval_{interval}", klilne_data)
        print(f"  🚀 WebSocket 데이터 real time storage 저장 완료.")
    
    def data_sync(self):
        print(f"  🚀 데이터 동기화 시작.")
        SyncStorage.sync_data(self.history, self.real_time)
        print(f"  👍 데이터 동기화 완료.")
        
    async def main(self):
        self.init_update_to_history()
        await self.ws_connection()
        await self.receive_ws_data()
        self.data_sync()
        await self.ins_websocket.close_connection()
        print(f"  🚀 WebSocket 연결 해제.")
        print(f"  👌 데이터 준비 완료")
    
if __name__ == "__main__":
    obj = StorageSyncTest()
    asyncio.run(obj.main())