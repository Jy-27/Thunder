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
    """

    def __init__(
        self,
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

        queue_request_exponential: asyncio.Queue,
        queue_response_exponential: asyncio.Queue,
        queue_request_wallet: asyncio.Queue,
        queue_response_wallet: asyncio.Queue,
        
        event_trigger_stop_loop: asyncio.Event,
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

        self.event_trigger_stop_loop = event_trigger_stop_loop

        self.stroage_ticker = StorageDeque(Streaming.max_lengh_ticker)
        self.storage_trade = StorageDeque(Streaming.max_lengh_trade)
        self.storage_miniTicker = StorageDeque(Streaming.max_lengh_miniTicker)
        self.storage_depth = StorageDeque(Streaming.max_lengh_depth)
        self.storage_aggTrade = StorageDeque(Streaming.max_lengh_aggTrade)
        self.storage_kline_ws = node_storage.storage_kline_real
        self.storage_execution_ws = node_storage.storage_execution_ws
        self.storage_kline_fetcher = node_storage.storage_kline_history
        self.storage_orderbook_fetcher = StorageDeque(Streaming.max_lengh_orderbook)
        self.storage_account_balance = StorageOverwrite([])
        self.storage_order_status = node_storage.storage_execution_ws

    async def ticker_update(self):
        """
        💾 websocket stream(ticker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(ticker) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_feed_ticker_ws.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.stroage_ticker.add_data(symbol, data)
            self.queue_feed_ticker_ws.task_done()
        print(f"  ✋ ticker storage 중지")

    async def trade_update(self):
        """
        💾 websocket stream(trade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(trade) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_feed_trade_ws.get()
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
            message = await self.queue_feed_trade_ws.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_miniTicker.add_data(symbol, data)
            self.queue_feed_trade_ws.task_done()
        print(f"  ✋ miniTicker storage 중지")

    async def depth_update(self):
        """
        💾 websocket stream(depth) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(depth) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_feed_trade_ws.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_depth.add_data(symbol, data)
            self.queue_feed_trade_ws.task_done()
        print(f"  ✋ depth storage 중지")

    async def aggTrade_update(self):
        """
        💾 websocket stream(aggTrade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(aggTrade) storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_feed_trade_ws.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_aggTrade.add_data(symbol, data)
            self.queue_feed_trade_ws.task_done()
        print(f"  ✋ aggTrade storage 중지")

    async def kline_ws_update(self):
        """
        💾 websocket kline data 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket kline data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            packing_message = await self.queue_feed_kline_ws.get()
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
            message = await self.queue_feed_execution_ws.get()
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
            packing_message = await self.queue_fetch_kline.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_fetcher.set_data(symbol, convert_to_interval, data)
            self.queue_fetch_kline.task_done()
        print(f"  ✋ kline cycle storage 중지")

    async def orderbook_fetcher_update(self):
        """
        💾 OrderBook자료를 저장한다. 데이터는 asyncio.Queue를 사용하여 tuple(symbol, data)형태로 수신한다.
        """
        print(f"  💾 orderbook data storage 시작")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_fetch_orderbook.get()
            symbol, data = message
            self.storage_orderbook_fetcher.add_data(symbol, data)
            self.queue_fetch_orderbook.task_done()
        print(f"  ✋ orderbook storage 중지")

    async def account_balance_update(self):
        print(f"  💾 account balance 시작")
        field = "account_balance"
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_fetch_account_balance.get()
            self.storage_account_balance.set_data(field, message)
            self.queue_fetch_account_balance.task_done()
        print(f"  ✋ account balance storage 중지")
        
    
    async def order_status_update(self):
        pass
    

    async def respond_to_data(self):
        """
        calculate함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_trigger_stop_loop.is_set():
            message = await self.queue_request_exponential.get()
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
            asyncio.create_task(self.respond_to_data()),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    queues_list = [
        "queue_feed_ticker_ws",
        "queue_feed_trade_ws",
        "queue_feed_miniTicker_ws",
        "queue_feed_depth_ws",
        "queue_feed_aggTrade_ws",
        "queue_feed_kline_ws",
        "queue_feed_execution_ws",
        "queue_fetch_kline",
        "queue_fetch_orderbook",
        "queue_fetch_all_storage",
        "queue_send_exponential",
        "queue_fetch_exponential",
        "queue_send_analysis",
        "queue_fetch_analysis",
        "queue_fetch_analysis",
        "queue_send_analysis",
        "queue_send_trading_status",
        "queue_fetch_trading_status",
    ]
    events_list = [
        "event_trigger_stop_loop",
        "event_timer_start",
        "event_start_exponential",
        "event_done_exeponential",
        "event_request_receiver_data",
        "event_start_analysis",
        "event_done_analysis",
        "event_request_computed_results",
        "event_start_orders",
        "event_done_orders",
        "event_request_status",
        "event_start_monitor",
        "event_done_monitor",
        "event_request_message",
        "event_start_message",
        "event_done_message",
    ]

    queues = []
    for _ in range(10):
        queues.append(asyncio.Queue())
    queues = tuple(queues)
    events = []
    for _ in range(2):
        events.append(asyncio.Event())
    events = tuple(events)

    instance = ReceiverDataStorage(*queues, *events)
    # instance = ReceiverDataStorage(**kwargs)
    asyncio.run(instance.start())
