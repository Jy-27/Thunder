import asyncio
import os
import sys
from typing import Dict

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming
import SystemTrading.TradingDataHub.ReceiverDataStorage.StorageNodeManager as node_storage
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.DataStorage.StorageDeque import StorageDeque
from Workspace.DataStorage.StorageOverwrite import StorageOverwrite

class ReceiverDataStorage:
    """
    websocket, fetch 등 market에서 수신한 데이터를 storage에 저장한다.
    event, queue 기반으로 동작하며 덮어쓰기 or 추가하기 방식으로 저장한다.
    """

    def __init__(
        self,
        # receiver 데이터 수신용
        queue_feed_ticker_ws: asyncio.Queue,
        queue_feed_trade_ws: asyncio.Queue,
        queue_feed_miniTicker_ws: asyncio.Queue,
        queue_feed_depth_ws: asyncio.Queue,
        queue_feed_aggTrade_ws: asyncio.Queue,
        queue_feed_kline_ws: asyncio.Queue,
        queue_feed_execution_ws: asyncio.Queue,
        queue_fetch_kline: asyncio.Queue,
        queue_fetch_orderbook: asyncio.Queue,
        queue_fetch_account_balance: asyncio.Queue,
        queue_fetch_order_status: asyncio.Queue,

        # 요청사항 수신 및 응답 queue
        queue_request_exponential: asyncio.Queue,
        queue_response_exponential: asyncio.Queue,
        queue_request_wallet: asyncio.Queue,
        queue_response_wallet: asyncio.Queue,
        queue_request_orders: asyncio.Queue,
        queue_response_orders: asyncio.Queue,
        
        # while 중단 신호
        event_trigger_stop_loop: asyncio.Event,
        
        # storage clear 실행 trigger
        event_trigger_clear_ticker: asyncio.Event,
        event_trigger_clear_trade: asyncio.Event,
        event_trigger_clear_miniTicker: asyncio.Event,
        event_trigger_clear_depth: asyncio.Event,
        event_trigger_clear_aggTrade: asyncio.Event,
        event_trigger_clear_kline_ws: asyncio.Event,
        event_trigger_clear_execution_ws: asyncio.Event,
        event_trigger_clear_kline_fetch: asyncio.Event,
        event_trigger_clear_orderbook_fetch: asyncio.Event,
        event_trigger_clear_account_balance: asyncio.Event,
        event_trigger_clear_order_status: asyncio.Event,
        
        # storage 데이터 발신 신호
        event_fired_response_done_ticker: asyncio.Event,
        event_fired_response_done_trade: asyncio.Event,
        event_fired_response_done_miniTicker: asyncio.Event,
        event_fired_response_done_depth: asyncio.Event,
        event_fired_response_done_aggTrade: asyncio.Event,
        event_fired_response_done_kline_ws: asyncio.Event,
        event_fired_response_done_execution_ws: asyncio.Event,
        event_fired_response_done_kline_fetch: asyncio.Event,
        event_fired_response_done_orderbook_fetch: asyncio.Event,
        event_fired_response_done_account_balance: asyncio.Event,
        event_fired_response_done_order_status: asyncio.Event,
        
        # clear 완료 신호
        event_fired_clear_done_ticker: asyncio.Event,
        event_fired_clear_done_trade: asyncio.Event,
        event_fired_clear_done_miniTicker: asyncio.Event,
        event_fired_clear_done_depth: asyncio.Event,
        event_fired_clear_done_aggTrade: asyncio.Event,
        event_fired_clear_done_kline_ws: asyncio.Event,
        event_fired_clear_done_execution_ws: asyncio.Event,
        event_fired_clear_done_kline_fetch: asyncio.Event,
        event_fired_clear_done_orderbook_fetch: asyncio.Event,
        event_fired_clear_done_account_balance: asyncio.Event,
        event_fired_clear_done_order_status: asyncio.Event,
        
        # event 신호 피드백
        #  >> update method stop loop
        event_fired_stop_loop_done_update_ticker: asyncio.Event,
        event_fired_stop_loop_done_update_trade: asyncio.Event,
        event_fired_stop_loop_done_update_miniTicker: asyncio.Event,
        event_fired_stop_loop_done_update_depth: asyncio.Event,
        event_fired_stop_loop_done_update_aggTrade: asyncio.Event,
        event_fired_stop_loop_done_update_kline_ws: asyncio.Event,
        event_fired_stop_loop_done_update_execution_ws: asyncio.Event,
        event_fired_stop_loop_done_update_kline_fetch: asyncio.Event,
        event_fired_stop_loop_done_update_orderbook_fetch: asyncio.Event,
        event_fired_stop_loop_done_update_account_balance: asyncio.Event,
        event_fired_stop_loop_done_update_orders_status: asyncio.Event,
        #  >> cleaner method stop loop
        event_fired_stop_loop_done_clear_ticker_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_trade_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_miniTicker_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_depth_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_aggTrade_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_kline_ws_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_execution_ws_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_kline_fetch_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_orderbook_fetch_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_account_balance_storage: asyncio.Event,
        event_fired_stop_loop_done_clear_order_status_storage: asyncio.Event,
        event_fired_stop_loop_done_respond_to_exponential: asyncio.Event,
        event_fired_stop_loop_done_respond_to_orders: asyncio.Event,
        event_fired_stop_loop_done_respond_to_wallet: asyncio.Event,
    ):
        # receiver 데이터 수신용
        self.queue_feed_ticker_ws = queue_feed_ticker_ws
        self.queue_feed_trade_ws = queue_feed_trade_ws
        self.queue_feed_miniTicker_ws = queue_feed_miniTicker_ws
        self.queue_feed_depth_ws = queue_feed_depth_ws
        self.queue_feed_aggTrade_ws = queue_feed_aggTrade_ws
        self.queue_feed_kline_ws = queue_feed_kline_ws
        self.queue_feed_execution_ws = queue_feed_execution_ws
        self.queue_fetch_kline = queue_fetch_kline
        self.queue_fetch_orderbook = queue_fetch_orderbook
        self.queue_fetch_account_balance = queue_fetch_account_balance
        self.queue_fetch_order_status = queue_fetch_order_status

        # 요청사항 수신 및 응답 queue
        self.queue_request_exponential = queue_request_exponential
        self.queue_response_exponential = queue_response_exponential
        self.queue_request_wallet = queue_request_wallet
        self.queue_response_wallet = queue_response_wallet
        self.queue_request_orders = queue_request_orders
        self.queue_response_orders = queue_response_orders

        # while 중단 신호
        self.event_trigger_stop_loop = event_trigger_stop_loop

        # storage clear 실행 trigger
        self.event_trigger_clear_ticker = event_trigger_clear_ticker
        self.event_trigger_clear_trade = event_trigger_clear_trade
        self.event_trigger_clear_miniTicker = event_trigger_clear_miniTicker
        self.event_trigger_clear_depth = event_trigger_clear_depth
        self.event_trigger_clear_aggTrade = event_trigger_clear_aggTrade
        self.event_trigger_clear_kline_ws = event_trigger_clear_kline_ws
        self.event_trigger_clear_execution_ws = event_trigger_clear_execution_ws
        self.event_trigger_clear_kline_fetch = event_trigger_clear_kline_fetch
        self.event_trigger_clear_orderbook_fetch = event_trigger_clear_orderbook_fetch
        self.event_trigger_clear_account_balance = event_trigger_clear_account_balance
        self.event_trigger_clear_order_status = event_trigger_clear_order_status

        # storage 데이터 발신 신호
        self.event_fired_response_done_ticker = event_fired_response_done_ticker
        self.event_fired_response_done_trade = event_fired_response_done_trade
        self.event_fired_response_done_miniTicker = event_fired_response_done_miniTicker
        self.event_fired_response_done_depth = event_fired_response_done_depth
        self.event_fired_response_done_aggTrade = event_fired_response_done_aggTrade
        self.event_fired_response_done_kline_ws = event_fired_response_done_kline_ws
        self.event_fired_response_done_execution_ws = event_fired_response_done_execution_ws
        self.event_fired_response_done_kline_fetch = event_fired_response_done_kline_fetch
        self.event_fired_response_done_orderbook_fetch = event_fired_response_done_orderbook_fetch
        self.event_fired_response_done_account_balance = event_fired_response_done_account_balance
        self.event_fired_response_done_order_status = event_fired_response_done_order_status

        # clear 완료 신호
        self.event_fired_clear_done_ticker = event_fired_clear_done_ticker
        self.event_fired_clear_done_trade = event_fired_clear_done_trade
        self.event_fired_clear_done_miniTicker = event_fired_clear_done_miniTicker
        self.event_fired_clear_done_depth = event_fired_clear_done_depth
        self.event_fired_clear_done_aggTrade = event_fired_clear_done_aggTrade
        self.event_fired_clear_done_kline_ws = event_fired_clear_done_kline_ws
        self.event_fired_clear_done_execution_ws = event_fired_clear_done_execution_ws
        self.event_fired_clear_done_kline_fetch = event_fired_clear_done_kline_fetch
        self.event_fired_clear_done_orderbook_fetch = event_fired_clear_done_orderbook_fetch
        self.event_fired_clear_done_account_balance = event_fired_clear_done_account_balance
        self.event_fired_clear_done_order_status = event_fired_clear_done_order_status

        # event 신호 피드백
        #  >> update method stop loop
        self.event_fired_stop_loop_done_update_ticker = event_fired_stop_loop_done_update_ticker
        self.event_fired_stop_loop_done_update_trade = event_fired_stop_loop_done_update_trade
        self.event_fired_stop_loop_done_update_miniTicker = event_fired_stop_loop_done_update_miniTicker
        self.event_fired_stop_loop_done_update_depth = event_fired_stop_loop_done_update_depth
        self.event_fired_stop_loop_done_update_aggTrade = event_fired_stop_loop_done_update_aggTrade
        self.event_fired_stop_loop_done_update_kline_ws = event_fired_stop_loop_done_update_kline_ws
        self.event_fired_stop_loop_done_update_execution_ws = event_fired_stop_loop_done_update_execution_ws
        self.event_fired_stop_loop_done_update_kline_fetch = event_fired_stop_loop_done_update_kline_fetch
        self.event_fired_stop_loop_done_update_orderbook_fetch = event_fired_stop_loop_done_update_orderbook_fetch
        self.event_fired_stop_loop_done_update_account_balance = event_fired_stop_loop_done_update_account_balance
        self.event_fired_stop_loop_done_update_orders_status = event_fired_stop_loop_done_update_orders_status

        #  >> cleaner method stop loop
        self.event_fired_stop_loop_done_clear_ticker_storage = event_fired_stop_loop_done_clear_ticker_storage
        self.event_fired_stop_loop_done_clear_trade_storage = event_fired_stop_loop_done_clear_trade_storage
        self.event_fired_stop_loop_done_clear_miniTicker_storage = event_fired_stop_loop_done_clear_miniTicker_storage
        self.event_fired_stop_loop_done_clear_depth_storage = event_fired_stop_loop_done_clear_depth_storage
        self.event_fired_stop_loop_done_clear_aggTrade_storage = event_fired_stop_loop_done_clear_aggTrade_storage
        self.event_fired_stop_loop_done_clear_kline_ws_storage = event_fired_stop_loop_done_clear_kline_ws_storage
        self.event_fired_stop_loop_done_clear_execution_ws_storage = event_fired_stop_loop_done_clear_execution_ws_storage
        self.event_fired_stop_loop_done_clear_kline_fetch_storage = event_fired_stop_loop_done_clear_kline_fetch_storage
        self.event_fired_stop_loop_done_clear_orderbook_fetch_storage = event_fired_stop_loop_done_clear_orderbook_fetch_storage
        self.event_fired_stop_loop_done_clear_account_balance_storage = event_fired_stop_loop_done_clear_account_balance_storage
        self.event_fired_stop_loop_done_clear_order_status_storage = event_fired_stop_loop_done_clear_order_status_storage
        self.event_fired_stop_loop_done_respond_to_exponential = event_fired_stop_loop_done_respond_to_exponential
        self.event_fired_stop_loop_done_respond_to_orders = event_fired_stop_loop_done_respond_to_orders
        self.event_fired_stop_loop_done_respond_to_wallet = event_fired_stop_loop_done_respond_to_wallet

        # Storage instance
        self.storage_ticker = StorageDeque(Streaming.max_lengh_ticker)#
        self.storage_trade = StorageDeque(Streaming.max_lengh_trade)#
        self.storage_miniTicker = StorageDeque(Streaming.max_lengh_miniTicker)#
        self.storage_depth = StorageDeque(Streaming.max_lengh_depth)#
        self.storage_aggTrade = StorageDeque(Streaming.max_lengh_aggTrade)#
        self.storage_kline_ws = node_storage.storage_kline_real#
        self.storage_execution_ws = node_storage.storage_execution_ws#
        self.storage_kline_fetch = node_storage.storage_kline_history#
        self.storage_orderbook_fetch = StorageDeque(Streaming.max_lengh_orderbook)#
        self.storage_account_balance = StorageOverwrite([])
        self.storage_orders_status = node_storage.storage_orders

    async def update_ticker(self):
        """
        💾 websocket stream(ticker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(ticker) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_ticker_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_ticker.add_data(symbol, data)
            self.queue_feed_ticker_ws.task_done()
        self.event_fired_stop_loop_done_update_ticker.set()
        print(f"  ✋ ticker storage 중지")

    async def update_trade(self):
        """
        💾 websocket stream(trade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(trade) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_trade_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_trade.add_data(symbol, data)
            self.queue_feed_trade_ws.task_done()
        self.event_fired_stop_loop_done_update_trade.set()
        print(f"  ✋ trade storage 중지")

    async def update_miniTicker(self):
        """
        💾 websocket stream(miniTicker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(miniTicker) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_miniTicker_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_miniTicker.add_data(symbol, data)
            self.queue_feed_miniTicker_ws.task_done()
        self.event_fired_stop_loop_done_update_miniTicker.set()
        print(f"  ✋ miniTicker storage 중지")

    async def update_depth(self):
        """
        💾 websocket stream(depth) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(depth) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_depth_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_depth.add_data(symbol, data)
            self.queue_feed_depth_ws.task_done()
        self.event_fired_stop_loop_done_update_depth.set()
        print(f"  ✋ depth storage 중지")

    async def update_aggTrade(self):
        """
        💾 websocket stream(aggTrade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(aggTrade) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_aggTrade_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_aggTrade.add_data(symbol, data)
            self.queue_feed_aggTrade_ws.task_done()
        self.event_fired_stop_loop_done_update_aggTrade.set()
        print(f"  ✋ aggTrade storage 중지")

    async def update_kline_ws(self):
        """
        💾 websocket kline data 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket kline data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                packing_message = await asyncio.wait_for(self.queue_feed_kline_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_ws.set_data(symbol, convert_to_interval, data)
            self.queue_feed_kline_ws.task_done()
        self.event_fired_stop_loop_done_update_kline_ws.set()
        print(f"  ✋ websocket kline data storage 중지")

    async def update_execution_ws(self):
        """
        💾 websocket 주문 관련 정보 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket execution data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_feed_execution_ws.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            data_type = message["e"]
            if data_type == "TRADE_LITE":
                symbol = message["s"]
            elif data_type == "ORDER_TRADE_UPDATE":
                symbol = message["o"]["s"]
            elif data_type == "ACCOUNT_UPDATE":
                symbol = message["a"]["P"][0]["s"]
            if symbol in node_storage.symbols:
                self.storage_execution_ws.set_data(symbol, data_type, message)
            await self.queue_feed_execution_ws.task_done()
        self.event_fired_stop_loop_done_update_execution_ws.set()
        print(f"  ✋ websocket execution storage 중지")

    async def update_kline_fetch(self):
        """
        💾 kline data 수신시 스토리지에 저장한다.
        """
        print(f"  💾 kline fetch data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                packing_message = await asyncio.wait_for(self.queue_fetch_kline.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_fetch.set_data(symbol, convert_to_interval, data)
            self.queue_fetch_kline.task_done()
        self.event_fired_stop_loop_done_update_kline_fetch.set()
        print(f"  ✋ kline fetch storage 중지")

    async def update_orderbook_fetch(self):
        """
        💾 OrderBook자료를 저장한다. 데이터는 asyncio.Queue를 사용하여 tuple(symbol, data)형태로 수신한다.
        """
        print(f"  💾 orderbook fetch data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_orderbook.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, data = message
            self.storage_orderbook_fetch.add_data(symbol, data)
            self.queue_fetch_orderbook.task_done()
        self.event_fired_stop_loop_done_update_orderbook_fetch.set()
        print(f"  ✋ orderbook fetch storage 중지")

    async def update_account_balance(self):
        print(f"  💾 account balance fetch data storage 시작")
        field = "account_balance"
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_account_balance.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_account_balance.set_data(field, message)
            # print(self.storage_account_balance.get_data(field))
            self.queue_fetch_account_balance.task_done()
        self.event_fired_stop_loop_done_update_account_balance.set()
        print(f"  ✋ account balance fetch storage 중지")

    async def update_orders_status(self):
        print(f"  💾 order status storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_order_status.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            for data in message:
                symbol = data["symbol"]
                reduceOnly = data["reduceOnly"]
                origType = data["origType"]
                
                if reduceOnly:  # 매도 주문
                    if origType == "LIMIT": #take profit 대용
                        sub_field = f"exit_limit"
                    else:   #stop loss 대용
                        sub_field = f"exit_trigger"
                else:   # 매수 주문
                    if origType == "LIMIT": # limit 매수 대용
                        sub_field = f"entry_limit"
                    else:   # 돌파 동일 방향 매수 대용
                        sub_field = f"entry_trigger"
                self.storage_orders_status.add_data(symbol, sub_field, data)
            self.queue_fetch_order_status.task_done()
        self.event_fired_stop_loop_done_update_orders_status.set()
        print(f"  ✋ order status storage 중지")

    async def clear_ticker_storage(self):
        print(f"  🧹 storage(ticker) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_ticker.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_ticker.clear_all()
            self.event_trigger_clear_ticker.clear()
            self.event_fired_clear_done_ticker.set()
        self.event_fired_stop_loop_done_clear_ticker_storage.set()
        print(f"  ✋ storage(ticker) cleaner 중지")

    async def clear_trade_storage(self):
        print(f"  🧹 storage(trade) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_trade.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_trade.clear()
            self.event_fired_clear_done_trade.set()
        self.event_fired_stop_loop_done_clear_trade_storage.set()
        print(f"  ✋ storage(trade) cleaner 중지")

    async def clear_miniTicker_storage(self):
        print(f"  🧹 storage(miniTicker) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_miniTicker.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_miniTicker.clear_all()
            self.event_trigger_clear_miniTicker.clear()
            self.event_fired_clear_done_miniTicker.set()
        self.event_fired_stop_loop_done_clear_miniTicker_storage.set()
        print(f"  ✋ storage(miniTicker) cleaner 중지")

    async def clear_depth_storage(self):
        print(f"  🧹 storage(depth) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_depth.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_depth.clear_all()
            self.event_trigger_clear_depth.clear()
            self.event_fired_clear_done_depth.set()
        self.event_fired_stop_loop_done_clear_depth_storage.set()
        print(f"  ✋ storage(depth) cleaner 중지")

    async def clear_aggTrade_storage(self):
        print(f"  🧹 storage(aggTrade) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_aggTrade.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_aggTrade.clear_all()
            self.event_trigger_clear_aggTrade.clear()
            self.event_fired_clear_done_aggTrade.set()
        self.event_fired_stop_loop_done_clear_aggTrade_storage.set()
        print(f"  ✋ storage(aggTrade) cleaner 중지")

    async def clear_kline_ws_storage(self):
        print(f"  🧹 storage(kline ws) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_kline_ws.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_kline_ws.clear_all()
            self.event_trigger_clear_kline_ws.clear()
            self.event_fired_clear_done_kline_ws.set()
        self.event_fired_stop_loop_done_clear_kline_ws_storage.set()
        print(f"  ✋ storage(kline ws) cleaner 중지")

    async def clear_execution_ws_storage(self):
        print(f"  🧹 storage(execution_ws) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_execution_ws.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_execution_ws.clear_all()
            self.event_trigger_clear_execution_ws.clear()
            self.event_fired_clear_done_execution_ws.set()
        self.event_fired_stop_loop_done_clear_execution_ws_storage.set()
        print(f"  ✋ storage(execution ws) cleaner 중지")

    async def clear_kline_fetch_storage(self):
        print(f"  🧹 storage(kline fetch) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_kline_fetch.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_kline_fetch.clear_all()
            self.event_trigger_clear_kline_fetch.clear()
            self.event_fired_clear_done_kline_fetch.set()
        self.event_fired_stop_loop_done_clear_kline_fetch_storage.set()
        print(f"  ✋ storage(kline fetch) cleaner 중지")

    async def clear_orderbook_fetch_storage(self):
        print(f"  🧹 storage(orderbook fetch) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_orderbook_fetch.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_orderbook_fetch.clear_all()
            self.event_trigger_clear_orderbook_fetch.clear()
            self.event_fired_clear_done_orderbook_fetch.set()
        self.event_fired_stop_loop_done_clear_orderbook_fetch_storage.set()
        print(f"  ✋ storage(orderbook fetch) cleaner 중지")

    async def clear_account_balance_storage(self):
        print(f"  🧹 storage(account balance) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_account_balance.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_account_balance.clear_all()
            self.event_trigger_clear_account_balance.clear()
            self.event_fired_clear_done_account_balance.set()
        self.event_fired_stop_loop_done_clear_account_balance_storage.set()
        print(f"  ✋ storage(account balance) cleaner 중지")

    async def clear_order_status_storage(self):
        print(f"  🧹 storage(order status fetch) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_order_status.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_orders_status.clear_all()
            self.event_trigger_clear_order_status.clear()
            self.event_fired_clear_done_order_status.set()
        self.event_fired_stop_loop_done_clear_order_status_storage.set()
        print(f"  ✋ storage(order status) cleaner 중지")

    async def respond_to_exponential(self):
        """
        📬 calculate함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_request_exponential.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            attr = message["attr"]
            main_field = message["main_field"]
            sub_field = message["sub_field"]
            if sub_field is None:
                data = getattr(self, f"storage_{attr}").get_data(main_field)
            else:
                data = getattr(self, f"storage_{attr}").get_data(main_field, sub_field)
            await self.queue_response_exponential.put(data)
            self.queue_request_exponential.task_done()
            event_signal:asyncio.Event = getattr(self, f"event_fired_response_done_{attr}")
            event_signal.set()
        self.event_fired_stop_loop_done_respond_to_exponential.set()
        print(f"  ✋ 연산용 storage 데이터 발신 중지")

    async def respond_to_orders(self):
        """
        📬 orders 함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_request_orders.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            # symbol, order type 필요.
            data = self.storage_orders_status.get_data(*message)
            await self.queue_response_orders.put(data)
            self.queue_request_orders.task_done()
            self.event_fired_response_done_order_status.set()
        self.event_fired_stop_loop_done_respond_to_orders.set()
        print(f"  ✋ 주문용 storage 데이터 발신 중지")

    async def respond_to_wallet(self):
        """
        📬 orders 함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_request_wallet.get(), timeout=1.0)
                #기본값: "account_balance"
            except asyncio.TimeoutError:
                continue
            await self.queue_response_wallet.put(self.storage_account_balance.get_data(message))
            self.queue_request_wallet.task_done()
            self.event_fired_response_done_account_balance.set()
        self.event_fired_stop_loop_done_respond_to_wallet.set()
        print(f"  ✋ 지갑관리용 storage 데이터 발신 중지")

    async def start(self):
        tasks = [
            asyncio.create_task(self.update_ticker()),
            asyncio.create_task(self.update_trade()),
            asyncio.create_task(self.update_miniTicker()),
            asyncio.create_task(self.update_depth()),
            asyncio.create_task(self.update_aggTrade()),
            asyncio.create_task(self.update_kline_ws()),
            asyncio.create_task(self.update_execution_ws()),
            asyncio.create_task(self.update_kline_fetch()),
            asyncio.create_task(self.update_orderbook_fetch()),
            asyncio.create_task(self.update_account_balance()),
            asyncio.create_task(self.update_orders_status()),
            asyncio.create_task(self.clear_ticker_storage()),
            asyncio.create_task(self.clear_trade_storage()),
            asyncio.create_task(self.clear_miniTicker_storage()),
            asyncio.create_task(self.clear_depth_storage()),
            asyncio.create_task(self.clear_aggTrade_storage()),
            asyncio.create_task(self.clear_kline_ws_storage()),
            asyncio.create_task(self.clear_execution_ws_storage()),
            asyncio.create_task(self.clear_kline_fetch_storage()),
            asyncio.create_task(self.clear_orderbook_fetch_storage()),
            asyncio.create_task(self.clear_account_balance_storage()),
            asyncio.create_task(self.clear_order_status_storage()),
            asyncio.create_task(self.respond_to_exponential()),
            asyncio.create_task(self.respond_to_orders()),
            asyncio.create_task(self.respond_to_wallet())
        ]
        await asyncio.gather(*tasks)
        print(f"  ℹ️ MarketDataStorage가 종료되어 저장 중단됨.")

if __name__ == "__main__":
    from SystemTrading.MarketDataFeed.ReceiverManager import ReceiverManager
    q_1 = []
    for _ in range(11):
        q_1.append(asyncio.Queue())
    q_1 = tuple(q_1)
    
    stop_event = asyncio.Event()
    receiver_event = [asyncio.Event() for _ in range(17)]
    
    e_1 = []
    for _ in range(17):
        e_1.append(asyncio.Event())
    e_1 = tuple(e_1)
    
    q_2 = []
    for _ in range(4):
        q_2.append(asyncio.Queue())
    q_2 = tuple(q_2)
    
    e_2 = []
    for _ in range(22):
        e_2.append(asyncio.Event())
    
    ins_receiver = ReceiverManager(*q_1, stop_event, *e_1)
    ins_storage = ReceiverDataStorage(*q_1, *q_2, stop_event, *e_2)
    
    async def stop_timer():
        await asyncio.sleep(10)
        e_1[3].set()
        print(f"  🚀 Private Event 활성화")
        print(f"  ⏱️ wait for 10 seconds")
        await asyncio.sleep(10)
        print(f"  🚀 Active the event")
        stop_event.set()
        
        
    async def main():
        tasks = [
            asyncio.create_task(stop_timer()),
            asyncio.create_task(ins_receiver.start()),
            asyncio.create_task(ins_storage.start())
        ]
        await asyncio.gather(*tasks)
        
    asyncio.run(main())