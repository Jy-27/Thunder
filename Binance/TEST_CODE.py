import nest_asyncio
import asyncio
import json
import websockets
import numpy as np
from collections import deque

nest_asyncio.apply()

SYMBOL = "trxusdt"
URL = f"wss://fstream.binance.com/ws/{SYMBOL}@depth10@100ms"

max_len = 300

# ✅ 최근 3000개의 데이터만 유지 (누적 분석을 위해 deque 사용)
depth_data = deque(maxlen=max_len)




async def process_order_book():
    async with websockets.connect(URL, ping_interval=10, ping_timeout=30) as ws:
        while True:
            data = await ws.recv()
            order_book = json.loads(data)

            # ✅ 매수·매도 호가를 np.array 변환 (오버헤드 최소화)
            bid_prices, bid_qtys = np.array(order_book["b"], dtype=float).T
            ask_prices, ask_qtys = np.array(order_book["a"], dtype=float).T

            # ✅ 기존 데이터에서 이전 주문 정보 가져오기
            if depth_data:
                prev_bids = depth_data[-1]["bids"]
                prev_asks = depth_data[-1]["asks"]
            else:
                prev_bids = (np.array([]), np.array([]))
                prev_asks = (np.array([]), np.array([]))

            # ✅ 신규 주문 및 취소 주문 계산 함수
            def calc_order_changes(prev_orders, new_orders):
                prev_prices, prev_qtys = prev_orders
                new_prices, new_qtys = new_orders

                prev_dict = {p: q for p, q in zip(prev_prices, prev_qtys)}
                new_dict = {p: q for p, q in zip(new_prices, new_qtys)}

                # 신규 주문: 새로운 가격이 생기거나, 기존 가격에서 수량 증가
                new_orders = {p: q for p, q in new_dict.items() if p not in prev_dict or new_dict[p] > prev_dict[p]}
                new_order_value = sum(p * q for p, q in new_orders.items())

                # 취소 주문: 기존에 있었지만 수량이 0이 되었거나 감소한 경우
                canceled_orders = {p: q for p, q in prev_dict.items() if p not in new_dict or new_dict[p] < prev_dict[p]}
                canceled_order_value = sum(p * q for p, q in canceled_orders.items())

                return new_order_value, canceled_order_value

            # ✅ 신규 주문 및 취소 주문 금액 계산
            bid_new_value, bid_canceled_value = calc_order_changes(prev_bids, (bid_prices, bid_qtys))
            ask_new_value, ask_canceled_value = calc_order_changes(prev_asks, (ask_prices, ask_qtys))

            # ✅ depth_data에 최신 데이터 추가 (pop 사용하지 않음, list(deque) 활용)
            depth_data.append({"bids": (bid_prices, bid_qtys), "asks": (ask_prices, ask_qtys)})

            # ✅ 누적된 데이터 활용 (list(deque) 변환)
            all_data = list(depth_data)

            # ✅ 전체 누적 데이터에서 총 주문 변화량 계산
            total_bid_new = sum(calc_order_changes(all_data[i-1]["bids"], all_data[i]["bids"])[0] for i in range(1, len(all_data)))
            total_bid_canceled = sum(calc_order_changes(all_data[i-1]["bids"], all_data[i]["bids"])[1] for i in range(1, len(all_data)))
            total_ask_new = sum(calc_order_changes(all_data[i-1]["asks"], all_data[i]["asks"])[0] for i in range(1, len(all_data)))
            total_ask_canceled = sum(calc_order_changes(all_data[i-1]["asks"], all_data[i]["asks"])[1] for i in range(1, len(all_data)))

            # ✅ 실시간 및 누적 데이터 출력
            print("\n📌 [100ms 업데이트] Futures Depth 변경 내역")
            print(f"  🟢 실시간 신규 매수 주문: {bid_new_value:.2f} USDT")
            print(f"  🔴 실시간 취소 매수 주문: {bid_canceled_value:.2f} USDT")
            print(f"  🟢 실시간 신규 매도 주문: {ask_new_value:.2f} USDT")
            print(f"  🔴 실시간 취소 매도 주문: {ask_canceled_value:.2f} USDT")

            print(f"\n📊 [누적 데이터] (최근 {max_len}개 기준)")
            print(f"  🟢 누적 신규 매수 주문 총액: {total_bid_new:,.2f} USDT")
            print(f"  🔴 누적 취소 매수 주문 총액: {total_bid_canceled:,.2f} USDT")
            print(f"  🟢 누적 신규 매도 주문 총액: {total_ask_new:,.2f} USDT")
            print(f"  🔴 누적 취소 매도 주문 총액: {total_ask_canceled:,.2f} USDT")

            await asyncio.sleep(0.1)  # ✅ 100ms 간격 유지

asyncio.run(process_order_book())
