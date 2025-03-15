import asyncio
from typing import Dict

import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Receiver.Futures.Public.KlineCycleFetcher import KlineCycleFetcher
from Workspace.Receiver.Futures.Public.KlineReceiverWebsocket import (
    KlineReceiverWebsocket,
)
from Workspace.Receiver.Futures.Public.StreamReceiverWebsocket import (
    StreamReceiverWebsocket,
)
from Workspace.Receiver.Futures.Private.ExecutionReceiverWebsocket import (
    ExecutionReceiverWebsocket,
)

import Workspace.Utils.TradingUtils as tr_utils
import Workspace.Utils.BaseUtils as base_utils

# 의존성 주입
from Workspace.Processor.Wallet.Wallet import Wallet
from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.DataStorage.DataCollector.aggTradeStorage import aggTradeStorage, AggTradeDeque
from Workspace.DataStorage.DataCollector.DepthStorage import DepthStorage
from Workspace.DataStorage.DataCollector.ExecutionStorage import ExecutionStorage
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import (
    FuturesTradingClient,
)
from Workspace.DataStorage.DataCollector.NodeStorage import SubStorage, MainStorage

import Workspace.DataStorage.DataCollector.StorageCollection as storage
import multiprocessing
import SystemConfig


### TEST ###
from Workspace.Analysis.AnalysisManager import TradingAnalysis


path_api = SystemConfig.Path.bianace
api_binance = base_utils.load_json(path_api)

tr_client = FuturesTradingClient(**api_binance)
obj_wallet = Wallet(tr_client)
obj_pending_order = PendingOrder(tr_client)
convert_to_interval = [f"interval_{i}" for i in SystemConfig.Streaming.intervals]
sub_storage = SubStorage(convert_to_interval)

storage_history = storage.KlineHistoryStorage().stroage
storage_real_time = storage.KlineRealTimeStorage().stroage
storage_aggTrade = AggTradeDeque()
storage_depth = DepthStorage()
storage_execution = ExecutionStorage()


class ReceiverStorageManager:
    """
    ✨ 데이터 수신 비동기식 함수들을 전부 무한 loop로 실행하고 수신된 데이터를 각 storage에 저장한다.
    """

    def __init__(self):
        self.queue_kline_fetcher = asyncio.Queue()
        self.queue_kline_ws = asyncio.Queue()
        self.queue_aggTrade_ws = asyncio.Queue()
        self.queue_depth_ws = asyncio.Queue()
        self.queue_execution_ws = asyncio.Queue()

        self.kline_cycle_fetcher = KlineCycleFetcher(self.queue_kline_fetcher)
        self.kline_receiver_ws = KlineReceiverWebsocket(self.queue_kline_ws)
        self.aggTrade_receive_ws = StreamReceiverWebsocket(
            "aggTrade", self.queue_aggTrade_ws
        )
        self.depth_receive_ws = StreamReceiverWebsocket("depth", self.queue_depth_ws)
        self.execution_receiver_ws = ExecutionReceiverWebsocket(self.queue_execution_ws)

        # 현재 상태 저장(업데이트)
        self.injection_wallet = obj_wallet
        self.injection_pending_order = obj_pending_order
        self.storage_execution = storage_execution

        # 분석 자료 저장(업데이트))
        self.storage_history = storage_history
        self.storage_real_time = storage_real_time
        self.stroage_aggTrade = storage_aggTrade
        self.storage_depth = storage_depth

        self.trading_analysis = TradingAnalysis(
            self.storage_history,
            self.storage_real_time,
            self.stroage_aggTrade,
            self.storage_depth,
        )

        self.queue_analysis: asyncio.Queue = self.trading_analysis.queue

    async def _queue_kline_fetcher(self):
        """
        📥 kline cycle fetcher 수신 데이터를 queue를 통해 storage에 저장한다.
        """
        while True:
            pack_data = await self.queue_kline_fetcher.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(pack_data)
            conver_to_interval = f"interval_{interval}"
            self.storage_history.set_data(symbol, conver_to_interval, data)
            self.queue_kline_fetcher.task_done()

    async def _queue_kline_ws(self):
        """
        📥 Webskcet(kline) 수신 데이터를 queue를 통해 storage에 저장한다.
        """
        while True:
            pack_data = await self.queue_kline_ws.get()
            # print(pack_data)
            symbol, interval, data = tr_utils.Extractor.unpack_message(pack_data)
            conver_to_interval = f"interval_{interval}"
            self.storage_real_time.set_data(symbol, conver_to_interval, data)
            self.queue_kline_ws.task_done()

    async def _queue_aggTrade_ws(self):
        """
        📥 Websocket stream(aggTrade) 수신 데이터를 queue를 통해 storage에 저장한다.
        """
        while True:
            data = await self.queue_aggTrade_ws.get()
            # print(data)
            self.stroage_aggTrade.update(data)
            self.queue_aggTrade_ws.task_done()

    async def _queue_depth_ws(self):
        """
        📥 Websocket stream(depth) 수신 데이터를 queue를 통해 storage에 저장한다.
        """
        while True:
            data = await self.queue_depth_ws.get()
            # print(data)
            self.storage_depth.add_data(data)
            self.queue_depth_ws.task_done()

    async def _queue_execution_ws(self):
        """
        📥 Websocket execution 수신 데이터를 queue를 통해 storage에 저장한다.
        """
        await self.injection_wallet.update_balance()
        await self.injection_pending_order.init_update()
        while True:
            data = await self.queue_execution_ws.get()
            # print(data)
            self.storage_execution.set_data(data)
            self.queue_execution_ws.task_done()
            await self.injection_wallet.update_balance()
            self.injection_pending_order.update_order(data)

    async def start(self):
        """
        🚀 데이터 수신 및 저장 기능의 무한 loop 함수들을 비동기식으로 실행한다.
        """
        tasks = [
            self.kline_cycle_fetcher.start(),
            self.kline_receiver_ws.start(),
            self.aggTrade_receive_ws.start(),
            self.depth_receive_ws.start(),
            self.execution_receiver_ws.start(),
            self.trading_analysis.start(),
            self._queue_kline_fetcher(),
            self._queue_kline_ws(),
            self._queue_aggTrade_ws(),
            self._queue_depth_ws(),
            self._queue_execution_ws(),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    obj = ReceiverStorageManager()
    asyncio.run(obj.start())
