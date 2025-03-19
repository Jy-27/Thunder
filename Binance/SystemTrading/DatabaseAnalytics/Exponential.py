import asyncio

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemTrading.TradingDataHub.MarketDataStorage import ReceiverDataStorage
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
                 queue_collect_all_storage:asyncio.Queue,
                 queue_send_results_storage:asyncio.Queue,
                 event_stop_loop:asyncio.Event,
                 event_start_exponential:asyncio.Event):
        self.queue_collect_all_storage = queue_collect_all_storage
        self.queue_send_results_storage = queue_send_results_storage

        self.event_stop_loop = event_stop_loop
        self.event_start_exponential = event_start_exponential

    async def dequeue_and_assign(self):
        get_collect_all_storage = await self.queue_collect_all_storage.get()
        len_queue = len(get_collect_all_storage)

        if len_queue != len_attrs:
            raise ValueError(f"데이터 길이가 다름: {len_queue} / {len_attrs}")

        for index, attr in enumerate(attrs):
            setattr(self, attr, get_collect_all_storage[index])
        self.queue_collect_all_storage.task_done()




    async def start(self):
        print(f"  🚀 지수 분석 실행.")
        while not self.event_stop_loop.is_set():
            self.event_start_exponential.wait()
            
            # 연산 즉시 queue로 발송시켜야 한다. 그렇지 않으면 메모리가 부족하다.
            # 그런데 어떻게 처리하지?
            
            self.event_start_exponential.clear()
            self.clear()

    def clear(self):
        """
        작업 완료 후 메모리확보를 위하여 None값으로 비움
        """
        for attr in attrs:
            setattr(self, attr, None)

if __name__ == "__main__":
    queues = [asyncio.Queue(), asyncio.Queue()]
    event = asyncio.Event()
    instance = ExponentialDataProcessor(*queues, event)
    print(instance.create_attr())
    # print(vars(instance))
    
    