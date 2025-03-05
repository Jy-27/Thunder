import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient

class DependencyContainer:
    def __init__(self):
        self.__path = SystemConfig.Path.telegram
        self.__api = base_utils.load_json(self.__path)
        self.client = TelegramClient(**self.__api)

container = DependencyContainer()