import asyncio
import json
import nest_asyncio
import websockets
import pandas as pd
from collections import deque
from rich.console import Console
from rich.table import Table
from rich.live import Live

# Jupyter Notebook 비동기 실행을 위한 설정
nest_asyncio.apply()

# Binance 웹소켓 URL
BINANCE_WS_URL = "wss://stream.binance.com:9443/ws/btcusdt@depth"

# 최대 저장할 데이터 개수
MAX_DEPTH_RECORDS = 600
large_order_threshold = 5  # 대량 주문 감지 임계값 (예: 5 BTC)

# 데이터 저장 (매도 호가, 매수 호가)
order_book = {"asks": deque(maxlen=MAX_DEPTH_RECORDS), "bids": deque(maxlen=MAX_DEPTH_RECORDS)}

# 누적 델타 볼륨
cumulative_delta_volume = 0

# Rich 콘솔 설정
console = Console()

def get_sell_buy_walls():
    """매도벽(Sell Wall)과 매수벽(Buy Wall) 계산"""
    asks_df = pd.DataFrame(order_book["asks"], columns=["price", "quantity"], dtype=float)
    bids_df = pd.DataFrame(order_book["bids"], columns=["price", "quantity"], dtype=float)

    # 가장 많은 매도 주문량이 있는 가격(매도벽)
    sell_wall = asks_df.loc[asks_df["quantity"].idxmax(), "price"]
    # 가장 많은 매수 주문량이 있는 가격(매수벽)
    buy_wall = bids_df.loc[bids_df["quantity"].idxmax(), "price"]

    return sell_wall, buy_wall

def generate_table():
    """실시간 데이터를 기반으로 테이블 생성"""
    global cumulative_delta_volume

    if not order_book["asks"] or not order_book["bids"]:
        return Table()

    asks_df = pd.DataFrame(order_book["asks"], columns=["price", "quantity"], dtype=float)
    bids_df = pd.DataFrame(order_book["bids"], columns=["price", "quantity"], dtype=float)

    # 주문량 가중 평균 가격 (VWAP) 계산
    vwap_ask = (asks_df["price"] * asks_df["quantity"]).sum() / asks_df["quantity"].sum()
    vwap_bid = (bids_df["price"] * bids_df["quantity"]).sum() / bids_df["quantity"].sum()

    # 최우선 매도/매수 호가 스프레드 계산
    best_ask = asks_df.iloc[0]["price"]
    best_bid = bids_df.iloc[0]["price"]
    spread = best_ask - best_bid
    spread_ratio = (spread / best_ask) * 100  # 스프레드 비율 (%)

    # 매도벽 & 매수벽 계산
    sell_wall, buy_wall = get_sell_buy_walls()
    spread_wall = sell_wall - buy_wall  # 매도벽-매수벽 스프레드

    # 매도/매수 호가 총량 계산
    total_ask_volume = asks_df["quantity"].sum()
    total_bid_volume = bids_df["quantity"].sum()

    # 불균형 비율 (Imbalance) 계산
    imbalance = (total_bid_volume - total_ask_volume) / (total_bid_volume + total_ask_volume)

    # 대량 매수/매도 주문 감지
    large_buy_orders = bids_df[bids_df["quantity"] > large_order_threshold]
    large_sell_orders = asks_df[asks_df["quantity"] > large_order_threshold]
    large_buy_detected = not large_buy_orders.empty
    large_sell_detected = not large_sell_orders.empty

    # 누적 델타 볼륨 (매수 총량 - 매도 총량)
    delta_volume = total_bid_volume - total_ask_volume
    cumulative_delta_volume += delta_volume

    # 테이블 생성
    table = Table(title="📊 Order Book Analysis", show_header=True, header_style="bold cyan")
    table.add_column("Metric", style="dim", width=30)
    table.add_column("Value", justify="right", width=20)

    table.add_row("VWAP Ask", f"{vwap_ask:,.2f}")
    table.add_row("VWAP Bid", f"{vwap_bid:,.2f}")
    table.add_row("Spread (Best Ask - Best Bid)", f"{spread:,.2f}")
    table.add_row("Spread Ratio (%)", f"{spread_ratio:.4f}")
    table.add_row("Sell Wall Price", f"{sell_wall:,.2f}")
    table.add_row("Buy Wall Price", f"{buy_wall:,.2f}")
    table.add_row("Spread (Sell Wall - Buy Wall)", f"{spread_wall:,.2f}")
    table.add_row("Imbalance", f"{imbalance:.4f}")
    table.add_row("Cumulative Delta Volume", f"{cumulative_delta_volume:,.2f}")

    # 이벤트 감지 추가
    if large_buy_detected:
        table.add_row("🚀 Large Buy Orders", f"{len(large_buy_orders)} orders", style="bold green")
    if large_sell_detected:
        table.add_row("⚠️ Large Sell Orders", f"{len(large_sell_orders)} orders", style="bold red")

    return table

async def process_message(msg, live):
    """수신된 WebSocket 메시지를 처리하고 UI 갱신"""
    data = json.loads(msg)

    asks = data.get("a", [])  # 매도 호가
    bids = data.get("b", [])  # 매수 호가

    if asks:
        order_book["asks"].extend(asks)
    if bids:
        order_book["bids"].extend(bids)

    # 화면 갱신
    live.update(generate_table())

async def binance_websocket():
    """Binance 웹소켓 연결 및 실시간 데이터 수신"""
    with Live(generate_table(), console=console, refresh_per_second=1) as live:
        async with websockets.connect(BINANCE_WS_URL) as ws:
            while True:
                msg = await ws.recv()
                await process_message(msg, live)

# 비동기 실행
asyncio.run(binance_websocket())
