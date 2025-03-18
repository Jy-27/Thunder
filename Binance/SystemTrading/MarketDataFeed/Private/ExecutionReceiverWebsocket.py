import asyncio

import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import (
    FuturesExecutionWebsocket,
)
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig

path_api = SystemConfig.Path.bianace
api_key = base_utils.load_json(path_api)


class ExecutionReceiverWebsocket:
    def __init__(
        self, queue: asyncio.Queue, event: asyncio.Event, loop_status: asyncio.Event
    ):
        self.futures_execution_websocket = FuturesExecutionWebsocket(**api_key)
        self.queue = queue
        self.event = event
        self.stream_type = "Execution"
        self.loop_status = loop_status

    async def start(self):
        print(f"  ⏳ ReceiverWebsocket({self.stream_type}) 연결중.")
        await self.futures_execution_websocket.open_connection()
        print(f"  🔗 ReceiverWebsocket({self.stream_type}) 연결 성공.")
        print(f"  🚀 ReceiverWebsocket({self.stream_type}) 시작")
        while not self.loop_status.is_set():
            message = await self.futures_execution_websocket.receive_message()
            await self.queue.put(message)
            await self.event.set()
        print(f"  ⁉️ ReceiverWebsocket({self.stream_type}) Loop 종료됨")
        await self.futures_execution_websocket.close_connection()
        print(f"  ⛓️‍💥 ReceiverWebsocket({self.stream_type}) 연결 해제")


if __name__ == "__main__":
    q_ = asyncio.Queue()
    obj = ExecutionReceiverWebsocket(q_)
    asyncio.run(obj.start())
