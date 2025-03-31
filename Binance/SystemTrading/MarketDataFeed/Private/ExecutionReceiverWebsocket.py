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
        self,
        queue_feed_execution_ws: asyncio.Queue,
        event_fired_execution_ws: asyncio.Event,
        event_trigger_stop_loop: asyncio.Event,
        event_fired_stop_loop_done_execution_ws:asyncio.Event
        ):
        self.futures_execution_websocket = FuturesExecutionWebsocket(**api_key)
        self.queue_feed_execution_ws = queue_feed_execution_ws
        self.event_fired_execution_ws = event_fired_execution_ws
        self.stream_type = "Execution"
        self.event_trigger_stop_loop = event_trigger_stop_loop
        self.event_fired_stop_loop_done_execution_ws = event_fired_stop_loop_done_execution_ws  #신호 수신시 이벤트 신를 생성한다.

    async def start(self):
        print(f"  ExecutionReceiverWebsocket: ⏳ Connecting >> {self.stream_type}")
        await self.futures_execution_websocket.open_connection()
        print(f"  ExecutionReceiverWebsocket: 🔗 Connected successfully >> {self.stream_type}")
        print(f"  ExecutionReceiverWebsocket: 🚀 Starting to receive >> {self.stream_type}")

        while not self.event_trigger_stop_loop.is_set():
            try:
                message = await asyncio.wait_for(
                    self.futures_execution_websocket.receive_message(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue  # stop_loop 이벤트 확인용 타임슬롯
            await self.queue_feed_execution_ws.put(message)
            self.event_fired_execution_ws.set()

        print(f"  ExecutionReceiverWebsocket: ✋ Loop stopped >> {self.stream_type}")
        await self.futures_execution_websocket.close_connection()
        print(f"  ExecutionReceiverWebsocket: ⛓️‍💥 Disconnected >> {self.stream_type}")
        self.event_fired_stop_loop_done_execution_ws.set()

if __name__ == "__main__":
    dummy_message_1_new = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993586598, 'E': 1742993586598, 'o': {'s': 'BTCUSDT', 'c': 'ios_ArfzDKDqp7FLwwpFUqYz', 'S': 'BUY', 'o': 'STOP_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '94326.6', 'x': 'NEW', 'X': 'NEW', 'i': 637084704043, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993586598, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'STOP_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
    dummy_message_2_new = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993586600, 'E': 1742993586600, 'o': {'s': 'BTCUSDT', 'c': 'ios_SGow7N1VNdXGXwCc0KQB', 'S': 'BUY', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '77176.3', 'x': 'NEW', 'X': 'NEW', 'i': 637084704049, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993586600, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
    dummy_message_3_new = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993624958, 'E': 1742993624959, 'o': {'s': 'BTCUSDT', 'c': 'ios_4uVhqNJ1I9vUtTPziCQ9', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.001', 'p': '104393.6', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 637084889970, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993624958, 't': 0, 'b': '0', 'a': '104.3936', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
    dummy_message_1_cancel = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993652966, 'E': 1742993652966, 'o': {'s': 'BTCUSDT', 'c': 'ios_SGow7N1VNdXGXwCc0KQB', 'S': 'BUY', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '77176.3', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 637084704049, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993652966, 't': 0, 'b': '0', 'a': '104.3936', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
    dummy_message_2_cancel = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993652966, 'E': 1742993652966, 'o': {'s': 'BTCUSDT', 'c': 'ios_4uVhqNJ1I9vUtTPziCQ9', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.001', 'p': '104393.6', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 637084889970, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993652966, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
    dummy_message_3_cancel = {'e': 'ORDER_TRADE_UPDATE', 'T': 1742993652966, 'E': 1742993652966, 'o': {'s': 'BTCUSDT', 'c': 'ios_ArfzDKDqp7FLwwpFUqYz', 'S': 'BUY', 'o': 'STOP_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '94326.6', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 637084704043, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1742993652966, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'STOP_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
    q_ = asyncio.Queue()
    events = []
    for _ in range(3):
        events.append(asyncio.Event())
    events = tuple(events)
    obj = ExecutionReceiverWebsocket(q_, *events)
    asyncio.run(obj.start())
