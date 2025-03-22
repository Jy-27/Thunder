import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import SystemConfig

symbols = tuple(SystemConfig.Streaming.symbols)


class ComputedResults:
    __slots__ = symbols
    def __init__(self):
        