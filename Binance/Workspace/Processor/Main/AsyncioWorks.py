import asyncio

import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance", "Workspace"))

# 힌트용
import multiprocessing


analyzer_start_signal = multiprocessing.Manager().Queue()  # 분석 시작 신호
analyzer_complete_signal = multiprocessing.Manager().Queue()  # 분석 완료 신호
monitoring_start_signal = multiprocessing.Manager().Queue()  # 모니터링 시작 신호
monitoring_complete_signal = multiprocessing.Manager().Queue()  # 모니터링 완료 신호

websocket_queue = asyncio.Queue()  # 웹소켓 데이터 전송
order_validation_queue = asyncio.Queue()  # 주문 검증 신호 (기존: validate_open_signal)
buy_order_queue = asyncio.Queue()  # 매수 주문 신호 (기존: open_signal_wallet)
sell_order_queue = asyncio.Queue()  # 매도 주문 신호 (기존: close_signal_wallet)

# async def async_event_consumer(shared_queue):
#     """비동기적으로 큐에서 이벤트를 감지하여 실행"""
#     loop = asyncio.get_running_loop()
#     while True:
#         event = await loop.run_in_executor(None, shared_queue.get)  # 비동기적으로 큐 감시
#         print(f"[Async Consumer] 이벤트 감지: {event}, 작업 실행!")

#         if event == "exit":
#             print("[Async Consumer] 종료 이벤트 감지, 종료")
#             break

class AsyncWor