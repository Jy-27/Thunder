import Workspace.Utils.BaseUtils as base_utils
import os

from typing import Final


class Streaming:
    all_intervals: Final = [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    ]
    symbols = ["BTCUSDT", "TRXUSDT", "ETHUSDT", "XRPUSDT", "SOLUSDT", "BNBUSDT"]
    intervals = ["5m", "30m", "1h", "1d"]#, "4h", "1d"]
    # intervals = all_intervals
    kline_limit: int = 480  # MAX 1,000
    orderbook_limit: int = 50
    orderbook_timesleep: int = 1
    
    max_lengh_ticker = 300
    max_lengh_trade = 300
    max_lengh_miniTicker = 300 
    max_lengh_depth = 300
    max_lengh_aggTrade = 300
    max_lengh_orderbook = 300



home = os.path.expanduser("~")
main_path = os.path.join(home, "github")

class Path:
    bianace = os.path.join(main_path, "API-KEY", "binance.json")
    telegram = os.path.join(main_path, "API-KEY", "telegram.json")
    project = os.path.join(main_path, "Thunder", "Binance")


class Position:
    leverage:int = 5
    margin_type:str = "ISOLATED"
    
class Info:
    # 데이터 단방향 전송용
    transmission_queues = [
        "queue_feed_ticker_ws",
        "queue_feed_trade_ws",
        "queue_feed_miniTicker_ws",
        "queue_feed_depth_ws",
        "queue_feed_aggTrade_ws",
        "queue_feed_kline_ws",
        "queue_feed_execution_ws",
        "queue_fetch_kline",
        "queue_fetch_orderbook",
        "queue_fetch_account_balance",
        "queue_fetch_order_status"]

    # 자료 요청용
    args_queues = [
        "queue_request_exponential",
        "queue_response_exponential",
        "queue_request_wallet",
        "queue_response_wallet"
    ]

    # 중앙 이벤트 컨트롤로가 발신 일경우,
    trigger_event = [
        "event_trigger_stop_loop",
        "event_trigger_kline",
        "event_trigger_orderbook",
        "event_trigger_private"
        ]

    # 중앙 이벤트 컨트롤로가 수신일경우,
    fired_event_signal = [
        "event_fired_execution_ws"  #이벤트 발생을 알리고 fetcher를 실행하기 위한 기본 신호로 결정한다.
    ]

    # stop loop 종료 확인신호
    fired_event_stop = [
        "event_fired_ticker_loop",
        "event_fired_trade_loop",
        "event_fired_miniTicker_loop",
        "event_fired_depth_loop",
        "event_fired_aggTrade_loop",
        "event_fired_kline_loop",
        "event_fired_execution_loop",
        "event_fired_f_kline_loop",
        "event_fired_orderbook_loop",
        "event_fired_private_loop"
        ]