from typing import Final

class Streaming:
    all_intervals:Final = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M",]
    symbols = ["BTCUSDT","TRXUSDT","ETHUSDT","XRPUSDT","SOLUSDT","BNBUSDT"]
    intervals = ["1m", "3m", "5m", "15m"]#, "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M",]
    kline_limit:int = 480   # MAX 1,000