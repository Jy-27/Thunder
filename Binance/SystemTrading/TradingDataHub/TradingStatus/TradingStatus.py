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
    websocket, fetcher 등 market에서 수신된 정보를 분류 및 가공하지 않고 저장한다.
    연산이 필요할때 저장할 용도의 메인 스토리지가 된다.
    event 기반 clear기능도 함께 수행된다. 일부 덮어쓰기용 데이터의 경우 기본 자료를 초기화 해야한다.(데이터가 순차적으로 전송되므로)
    """

    def __init__(
        self,
        queue_fetch_account_balance: asyncio.Queue,
        queue_fetch_order_status: asyncio.Queue,
        
        queue_request_wallet: asyncio.Queue,
        queue_response_wallet: asyncio.Queue,
        queue_request_orders: asyncio.Queue,
        queue_response_orders: asyncio.Queue,
        
        event_trigger_stop_loop: asyncio.Event,
        
        event_trigger_clear_account_balance: asyncio.Event,
        event_trigger_clear_order_status: asyncio.Event,
        
        event_fired_clear_account_balance: asyncio.Event,
        event_fired_clear_order_status: asyncio.Event,
    ):

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
        
        self.queue_request_exponential = queue_request_exponential
        self.queue_response_exponential = queue_response_exponential
        self.queue_request_wallet = queue_request_wallet
        self.queue_response_wallet = queue_response_wallet

        self.event_trigger_stop_loop = event_trigger_stop_loop

        self.event_trigger_clear_ticker = event_trigger_clear_ticker
        self.event_trigger_clear_trade = event_trigger_clear_trade
        self.event_trigger_clear_miniTicker = event_trigger_clear_miniTicker
        self.event_trigger_clear_depth = event_trigger_clear_depth
        self.event_trigger_clear_aggTrade = event_trigger_clear_aggTrade
        self.event_trigger_clear_kline_ws = event_trigger_clear_kline_ws
        self.event_trigger_clear_execution_ws = event_trigger_clear_execution_ws
        self.event_trigger_clear_kline_fetcher = event_trigger_clear_kline_fetcher
        self.event_trigger_clear_orderbook_fetcher = event_trigger_clear_orderbook_fetcher
        self.event_trigger_clear_account_balance = event_trigger_clear_account_balance
        self.event_trigger_clear_order_status = event_trigger_clear_order_status
        
        self.event_fired_clear_ticker = event_fired_clear_ticker
        self.event_fired_clear_trade = event_fired_clear_trade
        self.event_fired_clear_miniTicker = event_fired_clear_miniTicker
        self.event_fired_clear_depth = event_fired_clear_depth
        self.event_fired_clear_aggTrade = event_fired_clear_aggTrade
        self.event_fired_clear_kline_ws = event_fired_clear_kline_ws
        self.event_fired_clear_execution_ws = event_fired_clear_execution_ws
        self.event_fired_clear_kline_fetcher = event_fired_clear_kline_fetcher
        self.event_fired_clear_orderbook_fetcher = event_fired_clear_orderbook_fetcher
        self.event_fired_clear_account_balance = event_fired_clear_account_balance
        self.event_fired_clear_order_status = event_fired_clear_order_status

        self.storage_ticker = StorageDeque(Streaming.max_lengh_ticker)#
        self.storage_trade = StorageDeque(Streaming.max_lengh_trade)#
        self.storage_miniTicker = StorageDeque(Streaming.max_lengh_miniTicker)#
        self.storage_depth = StorageDeque(Streaming.max_lengh_depth)#
        self.storage_aggTrade = StorageDeque(Streaming.max_lengh_aggTrade)#
        self.storage_kline_ws = node_storage.storage_kline_real#
        self.storage_execution_ws = node_storage.storage_execution_ws#
        self.storage_kline_fetcher = node_storage.storage_kline_history#
        self.storage_orderbook_fetcher = StorageDeque(Streaming.max_lengh_orderbook)#
        self.storage_account_balance = StorageOverwrite([])
        self.storage_orders_status = node_storage.storage_orders

    async def ticker_update(self):
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
        print(f"  ✋ ticker storage 중지")

    async def trade_update(self):
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
        print(f"  ✋ trade storage 중지")

    async def miniTicker_update(self):
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
        print(f"  ✋ miniTicker storage 중지")

    async def depth_update(self):
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
        print(f"  ✋ depth storage 중지")

    async def aggTrade_update(self):
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
        print(f"  ✋ aggTrade storage 중지")

    async def kline_ws_update(self):
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
        print(f"  ✋ websocket kline data storage 중지")

    async def execution_ws_update(self):
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
        print(f"  ✋ websocket execution storage 중지")

    async def kline_fetcher_update(self):
        """
        💾 kline data 수신시 스토리지에 저장한다.
        """
        print(f"  💾 kline cycle data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                packing_message = await asyncio.wait_for(self.queue_fetch_kline.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_fetcher.set_data(symbol, convert_to_interval, data)
            self.queue_fetch_kline.task_done()
        print(f"  ✋ kline fetcher storage 중지")

    async def orderbook_fetcher_update(self):
        """
        💾 OrderBook자료를 저장한다. 데이터는 asyncio.Queue를 사용하여 tuple(symbol, data)형태로 수신한다.
        """
        print(f"  💾 orderbook data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_orderbook.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            symbol, data = message
            self.storage_orderbook_fetcher.add_data(symbol, data)
            self.queue_fetch_orderbook.task_done()
        print(f"  ✋ orderbook fetcher storage 중지")

    async def account_balance_update(self):
        print(f"  💾 account balance storage 시작")
        field = "account_balance"
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_account_balance.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_account_balance.set_data(field, message)
            # print(self.storage_account_balance.get_data(field))
            self.queue_fetch_account_balance.task_done()
        print(f"  ✋ account balance fetcher storage 중지")


    async def order_status_update(self):
        print(f"  💾 order status storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_fetch_order_status.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            
            symbol = message["symbol"]
            reduceOnly = message["reduceOnly"]
            origType = message["origType"]
            
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
            self.storage_orders_status.add_data(symbol, sub_field, message)
            self.queue_fetch_order_status.task_done()
        print(f"  ✋ order status storage 중지")

    async def ticker_storage_clear(self):
        print(f"  🧹 storage(ticker) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_ticker.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_ticker.clear_all()
            self.event_trigger_clear_ticker.clear()
            self.event_fired_clear_ticker.set()
        print(f"  ✋ storage(ticker) cleaner 중지")
    
    async def trade_storage_clear(self):
        print(f"  🧹 storage(trade) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_trade.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_trade.clear()
            self.event_fired_clear_trade.set()
        print(f"  ✋ storage(trade) cleaner 중지")
    
    async def miniTicker_storage_clear(self):
        print(f"  🧹 storage(miniTicker) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_miniTicker.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_miniTicker.clear()
            self.event_fired_clear_miniTicker.set()
        print(f"  ✋ storage(miniTicker) cleaner 중지")
    
    async def depth_storage_clear(self):
        print(f"  🧹 storage(depth) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_depth.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_depth.clear()
            self.event_fired_clear_depth.set()
        print(f"  ✋ storage(depth) cleaner 중지")
    
    async def aggTrade_storage_clear(self):
        print(f"  🧹 storage(aggTrade) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_aggTrade.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_aggTrade.clear()
            self.event_fired_clear_aggTrade.set()
        print(f"  ✋ storage(aggTrade) cleaner 중지")
    
    async def kline_ws_storage_clear(self):
        print(f"  🧹 storage(kline ws) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_kline_ws.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_kline_ws.clear()
            self.event_fired_clear_kline_ws.set()
        print(f"  ✋ storage(kline ws) cleaner 중지")
    
    async def execution_ws_storage_clear(self):
        print(f"  🧹 storage(execution_ws) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_execution_ws.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_execution_ws.clear()
            self.event_fired_clear_execution_ws.set()
        print(f"  ✋ storage(execution ws) cleaner 중지")
    
    async def kline_fetcher_storage_clear(self):
        print(f"  🧹 storage(kline fetcher) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_kline_fetcher.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_kline_fetcher.clear()
            self.event_fired_clear_kline_fetcher.set()
        print(f"  ✋ storage(kline fetcher) cleaner 중지")
    
    async def orderbook_fetcher_storage_clear(self):
        print(f"  🧹 storage(orderbook fetcher) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_orderbook_fetcher.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_orderbook_fetcher.clear()
            self.event_fired_clear_orderbook_fetcher.set()
        print(f"  ✋ storage(orderbook fetcher) cleaner 중지")
    
    async def account_balance_storage_clear(self):
        print(f"  🧹 storage(account balance) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_account_balance.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_account_balance.clear()
            self.event_fired_clear_account_balance.set()
        print(f"  ✋ storage(account balance) cleaner 중지")

    async def order_status_storage_clear(self):
        print(f"  🧹 storage(order status fetcher) cleaner 시작")
        while not self.event_trigger_stop_loop.is_set():
            try:
                await asyncio.wait_for(self.event_trigger_clear_order_status.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            self.storage_trade.clear_all()
            self.event_trigger_clear_order_status.clear()
            self.event_fired_clear_order_status.set()
        print(f"  ✋ storage(order status) cleaner 중지")

    async def respond_to_data(self):
        """
        calculate함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(self.queue_request_exponential.get(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            # message = await self.queue_request_exponential.get()
            attr = message["attr"]
            main_field = message["main_field"]
            sub_field = message["sub_field"]
            if sub_field is None:
                data = getattr(self, attr).get_data(field)
                self.queue_fetch_storage.put(data)
            else:
                data = getattr(self, attr).get_data(main_field, sub_field)
                self.queue_response_exponential.put(data)
            self.queue_request_exponential.task_done()
        print(f"  ✋ storage 데이터 발신 중지")

    async def start(self):
        tasks = [
            asyncio.create_task(self.ticker_update()),
            asyncio.create_task(self.trade_update()),
            asyncio.create_task(self.miniTicker_update()),
            asyncio.create_task(self.depth_update()),
            asyncio.create_task(self.aggTrade_update()),
            asyncio.create_task(self.kline_ws_update()),
            asyncio.create_task(self.execution_ws_update()),
            asyncio.create_task(self.kline_fetcher_update()),
            asyncio.create_task(self.orderbook_fetcher_update()),
            asyncio.create_task(self.account_balance_update()),
            asyncio.create_task(self.order_status_update()),
            asyncio.create_task(self.ticker_storage_clear()),
            asyncio.create_task(self.trade_storage_clear()),
            asyncio.create_task(self.miniTicker_storage_clear()),
            asyncio.create_task(self.depth_storage_clear()),
            asyncio.create_task(self.aggTrade_storage_clear()),
            asyncio.create_task(self.kline_ws_storage_clear()),
            asyncio.create_task(self.execution_ws_storage_clear()),
            asyncio.create_task(self.kline_fetcher_storage_clear()),
            asyncio.create_task(self.orderbook_fetcher_storage_clear()),
            asyncio.create_task(self.account_balance_storage_clear()),
            asyncio.create_task(self.order_status_storage_clear()),
            asyncio.create_task(self.respond_to_data()),
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