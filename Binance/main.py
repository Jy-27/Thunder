import asyncio


import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Processor.Main.ThreadingLoop import ThreadingWorks
from Workspace.Processor.Main.TradingAsyncLoop import TradingAsyncLoop

import Workspace.Utils.BaseUtils as base_utils

import SystemConfig
import Workspace.DataStorage.NodeStorage as NodeStorage
import Workspace.Processor.Receiver.KlineCycle as KlineCycle
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import (
    FuturesMarketWebsocket,
)
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import (
    FuturesExecutionWebsocket,
)
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient

symbols = SystemConfig.Streaming.symbols
intervals = SystemConfig.Streaming.intervals
convert_to_interval = [f"interval_{i}" for i in intervals]

api_path = SystemConfig.Path.bianace
api = base_utils.load_json(api_path)

sub_storage = NodeStorage.SubStorage(convert_to_interval)
storage_history = NodeStorage.MainStorage(symbols, sub_storage)
storage_real_time = NodeStorage.MainStorage(symbols, sub_storage)

ins_kline_cycle = KlineCycle.KlineCycle(symbols, intervals, storage_history)
ins_exe_ws = FuturesExecutionWebsocket(**api)
async_event = asyncio.Event()

async_loop = TradingAsyncLoop(
    ins_kline_cycle, ins_exe_ws, storage_real_time, async_event
)
thread_loop = ThreadingWorks(20, storage_history, storage_real_time)

if __name__ == "__main__":
    thread_loop.start()
    print(f"🚀 Start TradingAsyncLoop")
    asyncio.run(async_loop.start())
