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
    symbols = ["BTCUSDT"]#, "TRXUSDT", "ETHUSDT", "XRPUSDT"]#, "SOLUSDT", "BNBUSDT"]
    intervals = ["5m", "30m", "1h", "1d"]#, "4h", "1d"]
    kline_limit: int = 480  # MAX 1,000



home = os.path.expanduser("~")
main_path = os.path.join(home, "github")

class Path:
    bianace = os.path.join(main_path, "API-KEY", "binance.json")
    telegram = os.path.join(main_path, "API-KEY", "telegram.json")
    project = os.path.join(main_path, "Thunder", "Binance")


