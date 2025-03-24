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


class ReceiverDataStorage:
    """
    websocket, fetcher 등 market에서 수신된 정보를 분류 및 가공하지 않고 저장한다.
    연산이 필요할때 저장할 용도의 메인 스토리지가 된다.
    """

    def __init__(
        self,
        queue_ticker: asyncio.Queue,
        queue_trade: asyncio.Queue,
        queue_minTicker: asyncio.Queue,
        queue_depth: asyncio.Queue,
        queue_aggTrade: asyncio.Queue,
        queue_kline_ws: asyncio.Queue,
        queue_execution_ws: asyncio.Queue,
        queue_kline_fetcher: asyncio.Queue,
        queue_orderbook_fetcher: asyncio.Queue,
        queue_request_storage: asyncio.Queue,
        queue_response_storage: asyncio.Queue,
        event_stop_loop: asyncio.Event,
        event_request_receiver_data: asyncio.Event,
    ):

        self.queue_ticker = queue_ticker
        self.queue_trade = queue_trade
        self.queue_minTicker = queue_minTicker
        self.queue_depth = queue_depth
        self.queue_aggTrade = queue_aggTrade
        self.queue_kline_ws = queue_kline_ws
        self.queue_execution_ws = queue_execution_ws
        self.queue_kline_fetcher = queue_kline_fetcher
        self.queue_orderbook_fetcher = queue_orderbook_fetcher
        self.queue_request_storage = queue_request_storage
        self.queue_response_storage = queue_response_storage

        self.event_stop_loop = event_stop_loop

        self.stroage_ticker = StorageDeque(Streaming.max_lengh_ticker)
        self.storage_trade = StorageDeque(Streaming.max_lengh_trade)
        self.storage_minTicker = StorageDeque(Streaming.max_lengh_minTicker)
        self.storage_depth = StorageDeque(Streaming.max_lengh_depth)
        self.storage_aggTrade = StorageDeque(Streaming.max_lengh_aggTrade)
        self.storage_kline_ws = node_storage.storage_kline_real
        self.storage_execution_ws = node_storage.storage_execution_ws
        self.storage_kline_fetcher = node_storage.storage_kline_history
        self.storage_orderbook_fetcher = StorageDeque(Streaming.max_lengh_orderbook)

    async def ticker_update(self):
        """
        💾 websocket stream(ticker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(ticker) storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_ticker.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.stroage_ticker.add_data(symbol, data)
            self.queue_ticker.task_done()
        print(f"  ✋ ticker storage 중지")

    async def trade_update(self):
        """
        💾 websocket stream(trade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(trade) storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_trade.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_trade.add_data(symbol, data)
            self.queue_trade.task_done()
        print(f"  ✋ trade storage 중지")

    async def minTicker_update(self):
        """
        💾 websocket stream(minTicker) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(minTicker) storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_trade.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_minTicker.add_data(symbol, data)
            self.queue_trade.task_done()
        print(f"  ✋ minTicker storage 중지")

    async def depth_update(self):
        """
        💾 websocket stream(depth) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(depth) storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_trade.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_depth.add_data(symbol, data)
            self.queue_trade.task_done()
        print(f"  ✋ depth storage 중지")

    async def aggTrade_update(self):
        """
        💾 websocket stream(aggTrade) 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket stream(aggTrade) storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_trade.get()
            stream: str = message["stream"]
            symbol: str = stream.split("@")[0].upper()
            data: Dict = message["data"]
            self.storage_aggTrade.add_data(symbol, data)
            self.queue_trade.task_done()
        print(f"  ✋ aggTrade storage 중지")

    async def kline_ws_update(self):
        """
        💾 websocket kline data 타입의 데이터 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket kline data storage 시작")
        while not self.event_stop_loop.is_set():
            packing_message = await self.queue_kline_ws.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_ws.set_data(symbol, convert_to_interval, data)
            self.queue_kline_ws.task_done()
        print(f"  ✋ websocket kline data storage 중지")

    async def execution_ws_update(self):
        """
        💾 websocket 주문 관련 정보 수신시 스토리지에 저장한다.
        """
        print(f"  💾 websocket execution data storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_execution_ws.get()
            data_type = message["e"]
            if data_type == "TRADE_LITE":
                symbol = message["s"]
            elif data_type == "ORDER_TRADE_UPDATE":
                symbol = message["o"]["s"]
            elif data_type == "ACCOUNT_UPDATE":
                symbol = message["a"]["P"][0]["s"]
            if symbol in node_storage.symbols:
                self.storage_execution_ws.set_data(symbol, data_type, message)
            await self.queue_execution_ws.task_done()
        print(f"  ✋ websocket execution storage 중지")

    async def kline_fetcher_update(self):
        """
        💾 kline data 수신시 스토리지에 저장한다.
        """
        print(f"  💾 kline cycle data storage 시작")
        while not self.event_stop_loop.is_set():
            packing_message = await self.queue_kline_fetcher.get()
            symbol, interval, data = tr_utils.Extractor.unpack_message(packing_message)
            convert_to_interval = f"interval_{interval}"
            self.storage_kline_fetcher.set_data(symbol, convert_to_interval, data)
            self.queue_kline_fetcher.task_done()
        print(f"  ✋ kline cycle storage 중지")

    async def orderbook_fetcher_update(self):
        """
        💾 OrderBook자료를 저장한다. 데이터는 asyncio.Queue를 사용하여 tuple(symbol, data)형태로 수신한다.
        """
        print(f"  💾 orderbook data storage 시작")
        while not self.event_stop_loop.is_set():
            message = await self.queue_orderbook_fetcher.get()
            symbol, data = message
            self.storage_orderbook_fetcher.add_data(symbol, data)
            self.queue_orderbook_fetcher.task_done()
        print(f"  ✋ orderbook storage 중지")

    # async def send_all_storage_to_queue(self):
    #     """
    #     calculate함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
    #     """
    #     print(f"  📬 storage 데이터 발신 실행")
    #     while not self.event_stop_loop.is_set():
    #         await self.event_request_receiver_data.wait()  # 이벤트 대기 (비동기)
    #         storages = [
    #             getattr(self, attr)
    #             for attr in self.__dict__
    #             if attr.startswith("storage")  # "storage"로 시작하는 속성만 포함
    #         ]
    #         await self.queue_request_storage.put(storages)  # 비동기 큐에 추가
    #         self.event_request_receiver_data.clear()
    #     print(f"  ✋ storage 데이터 발신 중지")

    async def reply_storage(self):
        """
        calculate함수에서 신호 수신시 스토리지 데이터를 전부 queue에 담아서 보낸다.
        """
        print(f"  📬 storage 데이터 발신 실행")
        while not self.event_stop_loop.is_set():
            message = await self.queue_request_storage.get()
            storage_type = message["type"]
            attr = message["attr"]
            if storage_type == "deque":
                field = message["field"]
                data = getattr(self, attr).get_data(field)
                self.queue_fetch_storage.put(data)
            elif storage_type == "node":
                main_field = message["main_field"]
                sub_field = message["sub_field"]
                data = getattr(self, attr).get_data(main_field, sub_field)
                self.queue_response_storage.put(data)
            self.queue_request_storage.task_done()
        print(f"  ✋ storage 데이터 발신 중지")

    async def start(self):
        tasks = [
            asyncio.create_task(self.ticker_update()),
            asyncio.create_task(self.trade_update()),
            asyncio.create_task(self.minTicker_update()),
            asyncio.create_task(self.depth_update()),
            asyncio.create_task(self.aggTrade_update()),
            asyncio.create_task(self.kline_ws_update()),
            asyncio.create_task(self.execution_ws_update()),
            asyncio.create_task(self.kline_fetcher_update()),
            asyncio.create_task(self.orderbook_fetcher_update()),
            asyncio.create_task(self.send_all_storage_to_queue()),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    queues_list = [
        "queue_ticker",
        "queue_trade",
        "queue_minTicker",
        "queue_depth",
        "queue_aggTrade",
        "queue_kline_ws",
        "queue_execution_ws",
        "queue_kline_fetcher",
        "queue_orderbook_fetcher",
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
        "event_stop_loop",
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

    # kwargs = {}
    # for q_ in queues_list:
    #     kwargs[q_] = asyncio.Queue()
    # for e_ in events_list:
    #     kwargs[e_] = asyncio.Event()

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
