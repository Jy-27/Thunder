import SystemConfig
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient
from Workspace.Services.PrivateAPI.Messaging.TelegramClient import TelegramClient
from Workspace.DataStorage.NodeStorage import SubStorage, MainStorage
from Workspace.Services.PrivateAPI.Receiver.FuturesExecutionWebsocket import FuturesExecutionWebsocket
from Workspace.DataStorage.ExecutionMessageRecorder import ExecutionMessageRecorder
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher
from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket
from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet
import Workspace.Utils.BaseUtils as base_utils

path_binance = SystemConfig.Path.bianace
api_binance = base_utils.load_json(path_binance)
path_telegram = SystemConfig.Path.telegram
api_telegram = base_utils.load_json(path_telegram)

conver_to_interval = [f"interval_{i}" for i in SystemConfig.Streaming.intervals]
sub_storage = SubStorage(conver_to_interval)

class DependencyContainer:
    def __init__(self):
        self.futures_trading_client = FuturesTradingClient(**api_binance)
        self.futures_execution_websocket = FuturesExecutionWebsocket(**api_binance)
        
        self.telegram_client = TelegramClient(**api_telegram)
        
        self.storage_real_time = MainStorage(SystemConfig.Streaming.symbols, sub_storage)
        self.storage_history = MainStorage(SystemConfig.Streaming.symbols, sub_storage)
        
        self.execution_message_recorder = ExecutionMessageRecorder()
        self.futures_market_fetcher = FuturesMarketFetcher()
        self.futures_market_websocket = FuturesMarketWebsocket(SystemConfig.Streaming.symbols)

        # self.pending_order = PendingOrder(self.futures_trading_client)
        # self.wallet = Wallet(self.futures_trading_client)
container = DependencyContainer()