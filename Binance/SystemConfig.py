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
    kline_limit: int = 480  # MAX 1,000
    orderbook_limit: int = 50
    orderbook_timesleep: int = 1
    
    max_lengh_ticker = 300
    max_lengh_trade = 300
    max_lengh_minTicker = 300 
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
    
    queues_list = [
        "queue_ticker",
        "queue_trade",
        "queue_minTicker",
        "queue_depth",
        "queue_aggTrade",
        "queue_kline_ws",
        "queue_execution_ws",
        "queue_kline_fetcher",
        "queue_orderbook_fetcher",
        "queue_fetch_all_storage",
        "queue_send_exponential",
        "queue_fetch_exponential",
        "queue_send_analysis",
        "queue_fetch_analysis",
        "queue_fetch_analysis",
        "queue_send_analysis",
        "queue_send_trading_status",
        "queue_fetch_trading_status",
    ]
    events_list = [
        "event_stop_loop",
        "event_timer_start",
        "event_start_exponential",
        "event_done_exeponential",
        "event_request_receiver_data",
        "event_start_analysis",
        "event_done_analysis",
        "event_request_computed_results",
        "event_start_orders",
        "event_done_orders",
        "event_request_status",
        "event_start_monitor",
        "event_done_monitor",
        "event_request_message",
        "event_start_message",
        "event_done_message",
    ]