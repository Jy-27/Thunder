import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))


from Workspace.Repository.RepositoryOverwrite import RepositoryOverwrite
from Workspace.Repository.RepositoryRecorder import RepositoryRecorder

import SystemConfig

symbols = SystemConfig.Streaming.symbols
attr_names = []

intervals = SystemConfig.Streaming.intervals

#PublicRestFetcher.py 수신 함수 리스트와 동일하게 맞출 것.(kline 함수 제외)
fetch_list = [
    "ticker_price",
    "book_tickers",
    "ticker_24hr",
    # "kline_limit",
    "order_book",
    "recent_trades",
    "agg_trade",
    "server_time",
    "ping_binance",
    "exchange_info",
    "mark_price",
    "funding_rate",
    "open_interest"]

websocket_list = [
    "ticker",
    "tread",
    "depth",
    "miniTicker",
    "aggTrade",
    # "kline"
    ]

# for symbol in symbols:
for interval in intervals:
    attr_fetch = f"fetch_kline_{interval}"
    attr_names.append(attr_fetch)
    
for function in fetch_list:
    attr = f"fetch_{function}"
    attr_names.append(attr)
for stream in websocket_list:
    attr = f"websocket_{stream}"
    attr_names.append(attr)

for interval in intervals:
    attr_stream = f"websocket_kline_{interval}"
    attr_names.append(attr_stream)

repository_data = {}
for attr in attr_names:
    if "fetch" in attr or "kline" in attr:
        repository_data[attr] = RepositoryOverwrite([])
    else:
        repository_data[attr] = RepositoryRecorder()
        
        

class PublicMarketDataRepository(RepositoryOverwrite):
    __slots__ = tuple(attr_names)
    def __init__(self):
        super().__init__(base_type=[])
        for attr in self.__slots__:
            setattr(self, attr, self.base_type)


if __name__ == "__main__":
    dummy = PublicMarketDataRepository()
