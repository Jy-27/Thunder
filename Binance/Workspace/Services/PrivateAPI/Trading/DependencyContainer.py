import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient

class DependencyContainer:
    def __init__(self):
        self.__symbols = SystemConfig.Streaming.symbols
        self.__intervals = SystemConfig.Streaming.intervals
        self.__path = SystemConfig.Path.bianace
        self.__api = base_utils.load_json(self.__path)
        self.client = FuturesTradingClient(**self.__api)

container = DependencyContainer()