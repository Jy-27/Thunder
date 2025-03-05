import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket
from Workspace.Services.PrivateAPI.Receiver.SpotExecutionWebsocket import SoptExcutionWebsocket


class DependencyContainer:
    def __init__(self):
        self.__symbols = SystemConfig.Streaming.symbols
        self.__intervals = SystemConfig.Streaming.intervals
        self.__path = SystemConfig.Path.bianace
        self.__api = base_utils.load_json(self.__path)
        self.futures_client = FuturesExecutionWebsocket(**self.__api)
        self.spot_client = SoptExcutionWebsocket(**self.__api)

container = DependencyContainer()