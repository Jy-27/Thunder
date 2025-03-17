

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))

import Workspace.Utils.BaseUtils as base_utils
import SystemConfig
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket

symbols = SystemConfig.Streaming.symbols
intervals = SystemConfig.Streaming.intervals

path_api = SystemConfig.Path.bianace
api = base_utils.load_json(path_api)

instance_private_client = FuturesExecutionWebsocket(**api)
