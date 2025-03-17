import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.DataStorage.DataCollector.NodeStorage as node_storage
from SystemConfig import Streaming

symbols = Streaming.symbols
intervals = Streaming.intervals
convert_to_intervals = [f"interval_{i}"for i in intervals]
event_types = ["TRADE_LITE", "ORDER_TRADE_UPDATE", "ACCOUNT_UPDATE", ]

kline_sub_storage = node_storage.SubStorage(convert_to_intervals)
execution_sub_storage = node_storage.SubStorage(event_types)

storage_kline_real = node_storage.MainStorage(symbols, kline_sub_storage)
storage_kline_history = node_storage.MainStorage(symbols, kline_sub_storage)
storage_execution_ws = node_storage.MainStorage(symbols, execution_sub_storage)

if __name__ == "__main__":
    storage_kline_real = node_storage.MainStorage(symbols, kline_sub_storage)
    storage_kline_history = node_storage.MainStorage(symbols, kline_sub_storage)
    storage_execution_ws = node_storage.MainStorage(symbols, execution_sub_storage)
    