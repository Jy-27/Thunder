import asyncio
from typing import Dict, Optional


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient
import Workspace.Utils.TradingUtils as tr_utils

class PrivateRestFetcher:
    """
    ℹ️ Binance Futures Market의 비공개 REST데이터를 수신한다.
    데이터 수신을 위하여 API를 반드시 매개변수로 입력해야한다.
    asyncio.Event 및 asyncio.Queue기반으로 동작하며, 함수의 실행상태, 데이터 수/발신 을 실시간으로 실행한다.
    """
    def __init__(self,
                #  queue_feed_fetch_account_balance:asyncio.Queue,
                #  queue_feed_fetch_order_status:asyncio.Queue,
                #  queue_feed_fetch_leverage_brackets:asyncio.Queue,
                #  queue_feed_fetch_order_history:asyncio.Queue,
                #  queue_feed_fetch_trade_history:asyncio.Queue,
                #  queue_feed_fetch_order_details:asyncio.Queue,
                 
                #  queue_request_fetch_order_status:asyncio.Queue,
                #  queue_request_fetch_leverage_brackets:asyncio.Queue,
                #  queue_request_fetch_order_history:asyncio.Queue,
                #  queue_request_fetch_trade_history:asyncio.Queue,
                #  queue_request_fetch_order_details:asyncio.Queue,
                 
                #  event_trigger_shutdown_loop:asyncio.Event,
                 
                #  event_trigger_fetch_account_balance:asyncio.Event,
                 
                #  event_fired_done_account_balance:asyncio.Event,
                #  event_fired_done_fetch_order_status:asyncio.Event,
                #  event_fired_done_fetch_leverage_brackets:asyncio.Event,
                #  event_fired_done_fetch_order_history:asyncio.Event,
                #  event_fired_done_fetch_trade_history:asyncio.Event,
                #  event_fired_done_fetch_order_details:asyncio.Event,
                 
                #  event_fired_done_shutdown_loop_fetch_account_balance:asyncio.Event,
                #  event_fired_done_shutdown_loop_fetch_order_status:asyncio.Event,
                #  event_fired_done_shutdown_loop_fetch_leverage_brackets:asyncio.Event,
                #  event_fired_done_shutdown_loop_fetch_order_history:asyncio.Event,
                #  event_fired_done_shutdown_loop_fetch_trade_history:asyncio.Event,
                #  event_fired_done_shutdown_loop_fetch_order_details:asyncio.Event,
                 
                 event_fired_done_private_rest_fetcher:asyncio.Event,
                 
                 api_key:Dict):
        
        self.queue_feed_fetch_account_balance = queue_feed_fetch_account_balance
        self.queue_feed_fetch_order_status = queue_feed_fetch_order_status
        self.queue_feed_fetch_leverage_brackets = queue_feed_fetch_leverage_brackets
        self.queue_feed_fetch_order_history = queue_feed_fetch_order_history
        self.queue_feed_fetch_trade_history = queue_feed_fetch_trade_history
        self.queue_feed_fetch_order_details = queue_feed_fetch_order_details
        
        self.queue_request_fetch_order_status = queue_request_fetch_order_status
        self.queue_request_fetch_leverage_brackets = queue_request_fetch_leverage_brackets
        self.queue_request_fetch_order_history = queue_request_fetch_order_history
        self.queue_request_fetch_trade_history = queue_request_fetch_trade_history
        self.queue_request_fetch_order_details = queue_request_fetch_order_details
        
        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop
        
        self.event_trigger_fetch_account_balance = event_trigger_fetch_account_balance
    
        self.event_fired_done_fetch_account_balance = event_fired_done_account_balance
        self.event_fired_done_fetch_order_status = event_fired_done_fetch_order_status
        self.event_fired_done_fetch_leverage_brackets = event_fired_done_fetch_leverage_brackets
        self.event_fired_done_fetch_order_history = event_fired_done_fetch_order_history
        self.event_fired_done_fetch_trade_history = event_fired_done_fetch_trade_history
        self.event_fired_done_fetch_order_details = event_fired_done_fetch_order_details
    
        self.event_fired_done_shutdown_loop_fetch_account_balance = event_fired_done_shutdown_loop_fetch_account_balance
        self.event_fired_done_shutdown_loop_fetch_order_status = event_fired_done_shutdown_loop_fetch_order_status
        self.event_fired_done_shutdown_loop_fetch_leverage_brackets = event_fired_done_shutdown_loop_fetch_leverage_brackets
        self.event_fired_done_shutdown_loop_fetch_order_history = event_fired_done_shutdown_loop_fetch_order_history
        self.event_fired_done_shutdown_loop_fetch_trade_history = event_fired_done_shutdown_loop_fetch_trade_history
        self.event_fired_done_shutdown_loop_fetch_order_details = event_fired_done_shutdown_loop_fetch_order_details
        self.event_fired_done_private_rest_fetcher = event_fired_done_private_rest_fetcher

        self.instance_futures_trading_client = FuturesTradingClient(**api_key)

    @tr_utils.Decorator.log_lifecycle()
    async def account_balance(self):
        """
        asyncio.Event신호 기반의 함수.
        account balance data를 수신 후 Queue에 넣는다.
        """
        while not self.event_trigger_shutdown_loop.is_set():
            await self.event_trigger_fetch_account_balance.wait()
            fetched_account_balance = await self.instance_futures_trading_client.fetch_account_balance()
            await self.queue_feed_fetch_account_balance.put(fetched_account_balance)
            self.event_fired_done_fetch_account_balance.set()
        self.event_fired_done_shutdown_loop_fetch_account_balance.set()
    
    @tr_utils.Decorator.log_lifecycle()
    async def order_status(self):
        """
        asyncio.Queue데이터(매개변수) 기반의 동작 함수.
        주문 상태를 수신 후 data를 Queue에 넣는다.
        """
        status_message = "PrivateRestFetcher(account balance)"
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[str] = await self.queue_request_fetch_order_status.get()
            if request_message is None:
                continue
            fetched_order_status = await self.instance_futures_trading_client.fetch_order_status(request_message)
            await self.queue_feed_fetch_order_status.put(fetched_order_status)
            self.event_fired_done_fetch_order_status.set()
        self.event_fired_done_shutdown_loop_fetch_order_status.set()

    @tr_utils.Decorator.log_lifecycle()
    async def leverage_brackets(self):
        """
        asyncio.Queue데이터(매개변수) 기반의 동작 함수.
        지정 symbol의 레버리지 정보를 수신 및 Queue에 넣는다.
        """
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[str] = await self.queue_request_fetch_leverage_brackets.get()
            if request_message is None:
                continue
            fetched_leverage_brackets = await self.instance_futures_trading_client.fetch_leverage_brackets(request_message)
            await self.queue_feed_fetch_leverage_brackets.put(fetched_leverage_brackets)
            self.event_fired_done_fetch_leverage_brackets.set()
        self.event_fired_done_shutdown_loop_fetch_leverage_brackets.set()

    @tr_utils.Decorator.log_lifecycle()
    async def order_history(self):
        """
        asyncio.Qeueu데이터(매개변수) 기반 동작 함수.
        지정 symbol의 주문 내역을 수신 및 Queue에 담는다.
        """
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[Dict] = await self.queue_request_fetch_order_history.get()
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_order_history = await self.instance_futures_trading_client.fetch_order_history(symbol, limit)
            await self.queue_feed_fetch_order_history.put(fetched_order_history)
            
            self.event_fired_done_fetch_order_history.set()
        self.event_fired_done_shutdown_loop_fetch_order_history.set()

    @tr_utils.Decorator.log_lifecycle()
    async def trade_history(self):
        """
        asyncio.Queue데이터(매개변수) 기반 동작 함수.
        지정 symbol 및 limit값 기준 거래내역을 수신 및 Queue에 넣는다.
        """
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[Dict] = await self.queue_request_fetch_trade_history.get()
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            limit = request_message["limit"]
            fetched_trade_history = await self.instance_futures_trading_client.fetch_trade_history(symbol, limit)
            await self.queue_feed_fetch_trade_history.put(fetched_trade_history)
            self.event_fired_done_fetch_trade_history.set()
        self.event_fired_done_shutdown_loop_fetch_trade_history.set()
            
    @tr_utils.Decorator.log_lifecycle()
    async def order_details(self):
        """
        asyncio.Queue데이터(매개변수) 기반 동작 함수.
        지정 symbol 및 order_id 기준 거래내역을 수신 및 Queue에 넣는다.
        """
        while not self.event_trigger_shutdown_loop.is_set():
            request_message:Optional[Dict] = await self.queue_request_fetch_order_details.get()
            if request_message is None:
                continue
            symbol = request_message["symbol"]
            order_id = request_message["order_id"]
            fetched_order_details = await self.instance_futures_trading_client.fetch_order_details(symbol, order_id)
            await self.queue_feed_fetch_order_details.put(fetched_order_details)
            self.event_fired_done_fetch_order_details.set()
        self.event_fired_done_shutdown_loop_fetch_order_details.set()
        
    @tr_utils.Decorator.log_lifecycle()
    async def shutdown_all_loops(self):
        """
        본 class의 무한 루프를 중단시키기 위한 Dummy signal을 생성시킨다.
        (무한 대기상태를 방지하기 위함임)
        """
        SHUTDOWN_SIGNAL = None
        await self.event_trigger_shutdown_loop.wait()
        self.event_trigger_fetch_account_balance.set()
        await self.queue_request_fetch_order_status.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_leverage_brackets.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_order_history.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_trade_history.put(SHUTDOWN_SIGNAL)
        await self.queue_request_fetch_order_details.put(SHUTDOWN_SIGNAL)
        self.event_fired_done_private_rest_fetcher.set()
    
    async def start(self):
        tasks = [
            asyncio.create_task(self.account_balance()),
            asyncio.create_task(self.order_status()),
            asyncio.create_task(self.leverage_brackets()),
            asyncio.create_task(self.order_history()),
            asyncio.create_task(self.trade_history()),
            asyncio.create_task(self.order_details()),
            asyncio.create_task(self.shutdown_all_loops()),
        ]
        await asyncio.gather(*tasks)
        print(f"  \033[91m🔴 Shutdown\033[0m >> \033[91mPrivateRestFetcher.py\033[0m")
        
if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    
    q_count = 11
    e_count = 15
    
    path = SystemConfig.Path.bianace
    api = base_utils.load_json(path)
    args = []
    for _ in range(q_count):
        args.append(asyncio.Queue())
    for _ in range(e_count):
        args.append(asyncio.Event())
    args = tuple(args)

    private_fetcher = PrivateRestFetcher(*args, api)
    
    async def put_args():
        args_order_status = "BTCUSDT"
        args_leverage_brackets = "BTCUSDT"
        args_order_history = {"symbol":"BTCUSDT",
                              "limit":10}
        args_trade_history = {"symbol":"BTCUSDT",
                              "limit":10}
        
        await private_fetcher.queue_request_fetch_order_status.put(args_order_status)
        await private_fetcher.queue_request_fetch_leverage_brackets.put(args_leverage_brackets)
        await private_fetcher.queue_request_fetch_order_history.put(args_order_history)
        await private_fetcher.queue_request_fetch_trade_history.put(args_trade_history)

    
    async def stop_siganl():
        await asyncio.sleep(5)
        print("SIGNAL")
        args[11].set()

    async def main():
        tasks = [
            asyncio.create_task(stop_siganl()),
            asyncio.create_task(private_fetcher.start()),
            asyncio.create_task(put_args())
        ]
        await asyncio.gather(*tasks)
        
        for i in range(q_count):
            data = await args[i].get()
            print(f"{i}st data: {len(data)}")
            args[i].task_done()

    asyncio.run(main())