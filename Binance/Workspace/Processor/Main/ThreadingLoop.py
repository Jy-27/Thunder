import threading
import time
import asyncio


import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
from Workspace.DataStorage.StorageManager import SyncStorage
from Workspace.DataStorage.NodeStorage import MainStorage


class ThreadingWorks:
    def __init__(
        self,
        time_sleep: int,
        history_storage: MainStorage,
        real_time_storage: MainStorage,
    ):
        self.time_sleep = time_sleep
        self.thread_event = threading.Event()
        self.history_storage = history_storage
        self.real_time_storage = real_time_storage

    def create_event(self):
        """
        규칙적인 이벤트 신호를 발생시켜 분석시작의 기준을 잡는다.
        """
        print("start time loop")
        while True:
            time.sleep(self.time_sleep)
            print(f"  🚀 create event signal!!")
            self.thread_event.set()  # 데이터 동기화 신호
            self.thread_event.set()

    def kline_sync(self):
        while True:
            self.thread_event.wait()
            while self.thread_event.is_set():
                SyncStorage.sync_data(self.history_storage, self.real_time_storage)
                self.thread_event.clear()

    def start(self):
        t0 = threading.Thread(target=self.create_event, daemon=False)
        t1 = threading.Thread(target=self.kline_sync, daemon=False)
        t0.start()
        t1.start()
