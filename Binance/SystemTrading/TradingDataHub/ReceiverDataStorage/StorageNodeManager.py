import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.DataStorage.StorageNode as node_storage
# import Workspace.DataStorage.DataCollector.NodeStorage as node_storage
from SystemConfig import Streaming

symbols = Streaming.symbols
intervals = Streaming.intervals
convert_to_intervals = [f"interval_{i}" for i in intervals]
event_types = [
    "TRADE_LITE",
    "ORDER_TRADE_UPDATE",
    "ACCOUNT_UPDATE",
]

kline_sub_storage = node_storage.SubStorageOverwrite(convert_to_intervals)
execution_sub_storage = node_storage.SubStorageOverwrite(event_types)

storage_kline_real = node_storage.MainStorageOverwrite(symbols, kline_sub_storage)
storage_kline_history = node_storage.MainStorageOverwrite(symbols, kline_sub_storage)
storage_execution_ws = node_storage.MainStorageOverwrite(symbols, execution_sub_storage)

orders_main_fields = ["entry", "exit"]
order_sub_fields = ["limit", "trigger"]
orders_fields = [f"{m}_{s}" for m in orders_main_fields for s in order_sub_fields]

order_sub_storage = node_storage.SubStorageAppend(orders_fields)
storage_orders = node_storage.MainStorageAppend(symbols, order_sub_storage)