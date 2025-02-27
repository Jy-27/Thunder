import asyncio
import multiprocessing
import time
import threading

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Processor.Wallet.Wallet import Wallet


class TradingThreading:
    def __init__(self, event_wallet: asyncio.Event, event_analysis: multiprocessing.Event, wallet: Wallet, time_step: int = 30):
        self.event_wallet = event_wallet
        self.event_analysis = event_analysis
        self.wallet = wallet
        self.time_step = time_step
        self._asyncio_event_loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_event_loop, daemon=True)

    def _run_event_loop(self):
        """비동기 이벤트 루프를 실행하는 쓰레드"""
        asyncio.set_event_loop(self._asyncio_event_loop)
        self._asyncio_event_loop.run_forever()

    def wallet_update(self):
        """이벤트 발생 시 지갑 업데이트"""
        while True:
            futures = asyncio.run_coroutine_threadsafe(self.event_wallet.wait(), self._asyncio_event_loop)
            futures.result()
            self.wallet.update_balance()
            self.event_wallet.clear()

    def event_timer(self):
        """일정 주기로 이벤트 발생"""
        while True:
            time.sleep(self.time_step)
            self.event_analysis.set()

    def start(self):
        """트레이딩 쓰레드 시작"""
        self._loop_thread.start()  # 비동기 루프를 실행하는 쓰레드 시작

        thread_1 = threading.Thread(target=self.wallet_update, daemon=True)
        thread_2 = threading.Thread(target=self.event_timer, daemon=True)

        thread_1.start()
        thread_2.start()

if __name__ == "__main__":
    from Workspace.Processor.Wallet.Wallet import Wallet
    from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient as futures_tr_client
    import Workspace.Utils.BaseUtils as base_utils
    import SystemConfig
    
    path = SystemConfig.Path.bianace
    api = base_utils.load_json(path)

    tr_client = futures_tr_client(**api)
    async_event = asyncio.Event()
    mp_event = multiprocessing.Event()
    wallet_storage = Wallet(init_balance=5, futures_trading_client=tr_client)

    trading_thread = TradingThreading(async_event, mp_event, wallet_storage, 30)
    trading_thread.start()

    # while True:  # 메인 스레드가 종료되지 않도록 유지
    #     time.sleep(1)