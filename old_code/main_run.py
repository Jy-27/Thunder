from TickerDataFetcher import SpotTickers, FuturesTickers
from BinanceTradeClient import SpotOrderManager, FuturesOrderManager
from TradingDataManager import SpotDataControl, FuturesDataControl

class Main_run(SpotTickers(), FuturesTickers()):
    ...
    