import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))

from Workspace.DataStorage.DataCollector.NodeStorage import SubStorage, MainStorage
import SystemConfig

class WebsocketMessage:
    def __init__(self):
        self.main_fields = SystemConfig.Streaming.symbols
        self.intervals = SystemConfig.Streaming.intervals
        self.sub_fields = [f"interval_{i}"for i in self.intervals]
        self.__sub_storyage = SubStorage(self.sub_fields)
        self.storage = MainStorage(self.main_fields, self.__sub_storyage)

stroage_history = WebsocketMessage()
storage_real_time = WebsocketMessage()