import asyncio
from typing import Dict

import sys, os
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient
import SystemConfig
import Workspace.Utils.BaseUtils as base_utils

path_binance_api = SystemConfig.Path.bianace
api_binance = base_utils.load_json(path_binance_api)


"""
commit
25.4.1 : class skeleton 구성
    >> 각자의 역할을 구분.
"""

"""
필요 기능

main method
1. 메인 이벤트 신호 감지 (the system will use the queue to an order message)


2. 주문
3. 주문 취소
4. 주문 조회 (data is retrieved from storage system and analyzed.)


sub method
1. 데이터 요청 (request to the account balance storage system)
2. 주문 결과 전송(보고/피드백) (feed to order message into the status storage system)
"""

from typing import Optional
entry_order_message = {
    "order_intent": "entry",                   # 진입 주문
    "symbol": "BTCUSDT",
    "order_type": "LIMIT",                   # LIMIT, MARKET
    "timeInForce": "GTC",                    # market일 경우 None
    "price": 123123,                         # market일 경우 None
    "quantity": 0.002,
    "leverage": 125
}

exit_order_message = {
    "order_intent": "exit",                    # 이탈 주문
    "symbol": "BTCUSDT",
    "order_type": "LIMIT",                   # LIMIT, MARKET
    "timeInForce": "GTC",                    # market일 경우 None
    "price": 123123,                         # market일 경우 None
    "quantity": 0.002,
    "leverage": 125                          # ← 통일성을 위해 추가 추천
}

trigger_order_message = {
    "order_intent": "entry_trigger",           # 트리거 진입 주문
    "symbol": "BTCUSDT",
    "order_type": "LIMIT",                   # LIMIT, MARKET
    "timeInForce": "GTC",                    # market일 경우 None
    "trigger_price": 123124,                 # 트리거 발동 가격
    "price": 123123,                         # 지정가 (market이면 None)
    "quantity": 0.002,
    "leverage": 125
}


"""
[1] CentralEventController → (신호 발생)
       ↓
[2] Order 컴포넌트 → 분석 컴포넌트에 주문 여부 요청
       ↓
[3] 분석 컴포넌트 → 주문서(order message)를 queue로 발신
       ↓
[4] Order 컴포넌트 → queue에서 메시지 수신 -> 검토 -> 주문 생성
       ↓
[5] 주문내역 전송


validate 항목
    1. 자금 여력
        >> 예수금이 존재 해야함.
        >> 안전 자산을 초과하지 말 것.
        >> 포지션당 최대 주문 가능 금액 제한.
          안전자산의 최대 30%까지???
    2. 포지션 보유 현황
        >> 분할 매수: True
        >> hedge 여부: False
        >> 최대 보유 항목 수 제한. (예: 3종목)
    3. 최대 주문 가능 
        >> max(minQty, tragetQty)

    4. 손절은 최대 분할매수 초과시에도 ROI -50% (또는 지정)일 경우 매도처리.
        30달러 3회 90달러, -45$
주문 취소 기능
"""


class OrderManager:
    """
    주문과 관련된 작업을 수행한다.
    """
    
    def __init__(self,
                 queue_request_result:asyncio.Queue,
                 queue_response_order:asyncio.Queue,
                 queue_feed_order_status:asyncio.Queue,
                 event_tirgger_stop_loop:asyncio.Event,
                 event_fired_done_receive_order_message: asyncio.Event,
                 event_feed_stop_loop:asyncio.Event,
                 event_complete_order_signal:asyncio.Event):
        self.queue_request_result = queue_request_result
        self.queue_response_order = queue_response_order
        self.queue_feed_order_status = queue_feed_order_status
        self.event_trigger_stop_loop = event_tirgger_stop_loop
        self.event_fired_done_receive_order_message = event_fired_done_receive_order_message
        self.event_feed_stop_loop = event_feed_stop_loop
        self.event_complete_order_signal = event_complete_order_signal
        self._event_request_to_validate = asyncio.Event()
        self._queue_request_to_validate = asyncio.Queue()
        self.purchase_order_message = None
        self.trading_client = FuturesTradingClient(**api_binance)

    async def create_entry_order(self, po_message:Dict):
        """
        진입 관련 주문을 생성한다.
        """
        pass

        async def _create_entry_trigger_market(self, *args, **kwargs):
            """
            시장가/조건부 진입 주문 함수
            """
            pass

        async def _create_entry_trigger_limit(self, *args, **kwargs):
            """
            지정가/조건부 진입 주문 함수
            """
            pass

        async def _create_entry_order_market(self, *args, **kwargs):
            """
            시장가 진입 주문 함수
            """
            pass

        async def _create_entry_order_limit(self, *args, **kwargs):
            """
            지정가 진입 주문 함수
            """
            pass

    async def create_exit_order(self, po_message:Dict):
        """
        이탈 관련 주문을 생성한다.
        """
        pass
    
        async def _create_exit_order_market(self, *args, **kwargs):
            """
            시장가 종료 주문 함수
            """
            pass

        async def _create_exit_order_limit(self, *args, **kwargs):
            """
            지정가 종료 주문 함수
            """
            pass
    
    async def create_cancel_order(self, po_message:Dict):
        """
        취소 관련 함수 상위 함수
        """
        pass

        async def _cancel_all_order_force(self):
            """
            현재 걸려있는 전체 주문을 취소
            """
            pass
        
        async def _cancel_all_orders_by_symbol(self, symbol:str):
            """
            지정한 심볼에 대한 전체 주문 취소

            Args:
                symbol (str): 심볼값
            """
            pass
        
        async def _cancel_order_by_id(self, order_id:str):
            """
            특정 주문 하나만 취소

            Args:
                order_id (str): order id
            """
            pass

    async def request_order_message(self):
        """
        asyncio.Queue기반 명령을 수신하는 함수.
        """
        while not self.event_trigger_stop_loop.is_set():
            try:
                self.purchase_order_message = await asyncio.wait_for(self.event_trigger_order.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                continue
            # await 
        pass

if __name__ == "__main__":
    args = []
    for _ in range(3):
        args.append(asyncio.Queue())
    for _ in range(4):
        args.append(asyncio.Queue())
    dummy = OrderManager(*args)