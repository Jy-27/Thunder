from .ReciverAPI import ReciverAPI
from typing import Union, List
import asyncio

class API(ReciverAPI):
    def __init__(self, intervals: Union[str, List]):
        super().__init__(base_url="wss://stream.binance.com:9443/ws/", intervals=intervals)
        

if __name__ == "__main__":
    symbols = ['BTCUSDT', 'TRXUSDT', 'ETHUSDT']
    intervals = ['3m', '5m']
    data_handler = API(intervals=intervals)
    
    asyncio.run(data_handler.connect_stream(symbols=symbols, stream_type=data_handler.ENDPOINT[0]))
    