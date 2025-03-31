import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.TradingDataHub.ReceiverDataStorage.MarketDataStorage import ReceiverDataStorage
import SystemConfig

dummy_queues = []
dummy_events = []

for _ in range(10):
    dummy_queues.append(asyncio.Queue())
for _ in range(2):
    dummy_events.append(asyncio.Event())

ins_receiver_storage = ReceiverDataStorage(*dummy_queues, *dummy_events)
vars_ = vars(ins_receiver_storage)
attrs = [attr for attr in vars_ if attr.startswith("storage")]
len_attrs = len(attrs)

symbols = SystemConfig.Streaming.symbols
intervals = SystemConfig.Streaming.intervals
convert_to_intervals = [f"interval_{i}" for i in intervals]

class ExponentialDataProcessor:
    def __init__(self,
                 queue_fetch_all_storage:asyncio.Queue,
                 queue_send_exponential:asyncio.Queue,
                 event_stop_loop:asyncio.Event,
                 event_request_receiver_data:asyncio.Event,
                 event_start_exponential_cals:asyncio.Event,
                 event_done_exponential_cals:asyncio.Event):
        self.queue_fetch_all_storage = queue_fetch_all_storage
        self.queue_send_exponential = queue_send_exponential
        self.event_stop_loop = event_stop_loop
        self.event_request_receiver_data = event_request_receiver_data
        self.event_start_exponential_cals = event_start_exponential_cals
        self.event_done_exponential_cals = event_done_exponential_cals
            
        """NOTE!!

            queue_request 시 
            ticker
            trade
            miniTicker
            depth
            aggTrade
            kline_ws
            execution_ws
            kline_fetch
            orderbook_fetch
            account_balance
            order_status        
            택 1
            
        """
            
            
    async def dequeue_and_assign(self):
        """
        데이터를 수신 후 속성에 각 데이터를 저장.

        Raises:
            ValueError: _description_
        """
        get_collect_all_storage = await self.queue_fetch_all_storage.get()
        len_queue = len(get_collect_all_storage)

        if len_queue != len_attrs:
            raise ValueError(f"데이터 길이가 다름: {len_queue} / {len_attrs}")

        for index, attr in enumerate(attrs):
            setattr(self, attr, get_collect_all_storage[index])
        self.queue_fetch_all_storage.task_done()

    def calculation(self):
        pass

    def clear(self):
        """
        작업 완료 후 메모리확보를 위하여 삭제 처리함.
        """
        for attr in self.__dict__:
            delattr(self, attr)

    async def start(self):
        print(f"  🚀 지수 분석 실행.")
        while not self.event_stop_loop.is_set():
            while not self.event_start_exponential_cals.is_set():
                await self.event_start_exponential_cals.wait()
                self.event_request_receiver_data.set()
                await self.dequeue_and_assign()
                ### 연산연산연산
                
                self.event_start_exponential_cals.clear()
                self.event_done_exponential_cals.set()
                self.clear()
        

if __name__ == "__main__":
    args = []
    for _ in range(2):
        args.append(asyncio.Queue())
    for _ in range(4):
        args.append(asyncio.Event())
    instance = ExponentialDataProcessor(*args)
    asyncio.run(instance.start())