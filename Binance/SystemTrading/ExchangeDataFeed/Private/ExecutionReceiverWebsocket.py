import asyncio
import aiohttp
import websockets
from typing import Optional, Dict
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import (
    FuturesExecutionWebsocket,
)
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig

path_api = SystemConfig.Path.bianace
api_key = base_utils.load_json(path_api)

class ExecutionReceiverWebsocket:
    def __init__(self,
                 api_key:Dict,
                 queue_feed_websocket_execution:asyncio.Queue,
                 event_trigger_shutdown_loop:asyncio.Event,
                 event_fired_done_exectuion_receiver_message:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_execution:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_listen_key_cycle:asyncio.Event,
                 event_fired_done_execution_receiver_websocket:asyncio.Event,
                 websocket_timeout:float=1.0,
                 listen_key_update_interval:int = 1_500):
        self.queue_feed_websocket_execution = queue_feed_websocket_execution
        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop
        self.event_fired_done_exectuion_receiver_message = event_fired_done_exectuion_receiver_message
        self.event_fired_done_shutdown_loop_websocket_execution = event_fired_done_shutdown_loop_websocket_execution
        self.event_fired_done_shutdown_loop_listen_key_cycle = event_fired_done_shutdown_loop_listen_key_cycle
        self.event_fired_done_execution_receiver_websocket = event_fired_done_execution_receiver_websocket
        self.websocket_timeout = websocket_timeout
        self.listen_key_update_interval = listen_key_update_interval
        
        self.instance_futures_execution_websocket = FuturesExecutionWebsocket(**api_key)
        
    @tr_utils.Decorator.log_complete()
    async def initialize_session(self, session:Optional[aiohttp.ClientSession]=None):
        if session is None:
            self.session = aiohttp.ClientSession()
        else:
            self.session = session
        self.instance_futures_execution_websocket.session = self.session
        
    @tr_utils.Decorator.log_complete()
    async def create_listen_key(self):
        await self.instance_futures_execution_websocket.create_listen_key()
    
    @tr_utils.Decorator.log_lifecycle()
    async def listen_key_cycle(self):
        while not self.event_trigger_shutdown_loop.is_set():
            await asyncio.sleep(self.listen_key_update_interval)
            await self.instance_futures_execution_websocket.renew_listen_key()
        self.event_fired_done_shutdown_loop_listen_key_cycle.set()

    @tr_utils.Decorator.log_lifecycle()
    async def route_message_execution(self):
        while not self.event_trigger_shutdown_loop.is_set():
            try:
                message = await asyncio.wait_for(self.instance_futures_execution_websocket.receive_message(), timeout=self.websocket_timeout)
            except asyncio.TimeoutError:
                continue
            await self.queue_feed_websocket_execution.put(message)
        self.event_fired_done_shutdown_loop_websocket_execution.set()

    @tr_utils.Decorator.log_ws_connect()
    async def connect_execution_websockets(self):
        await self.create_listen_key()
        url = f"{self.instance_futures_execution_websocket.websocket_base_url}{self.instance_futures_execution_websocket.listen_key}"
        self.instance_futures_execution_websocket.websocket_client = await websockets.connect(url)

    @tr_utils.Decorator.log_complete()
    async def disconnect_execution_websockets(self):
        await self.instance_futures_execution_websocket.close_connection()

    @tr_utils.Decorator.log_lifecycle()
    async def start(self):
        await self.connect_execution_websockets()
        tasks = [
            asyncio.create_task(self.listen_key_cycle()),
            asyncio.create_task(self.route_message_execution()),
        ]
        await asyncio.gather(*tasks)
        await self.disconnect_execution_websockets()
        

if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    
    path = SystemConfig.Path.bianace
    api = base_utils.load_json(path)
    q_ = asyncio.Queue()
    e_ = []
    for _ in range(3):
        e_.append(asyncio.Event())
    e_ = tuple(e_)
    
    test_instance = ExecutionReceiverWebsocket(api_key, q_, *e_)
    asyncio.run(test_instance.start())
