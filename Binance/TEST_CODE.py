import SystemConfig
import Services.Receiver.FuturesWebsocketReceiver as futures_ws_receiver
import Processor.DataStorage.DataStorage as storage
import Services.PublicData.FuturesMarketFetcher as futures_market
import Processor.DataReceiver.TestFuturesDataManager as test_manager
import datetime

if __name__ == "__main__":
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_futures_market = futures_market.FuturesMarketFetcher()
    ins_ws_receiver = futures_ws_receiver.FuturesWebsocketReceiver(symbols, intervals)
    real_time_storage = storage.SymbolStorage(storage.IntervalStorage)
    history_storage = storage.SymbolStorage(storage.IntervalStorage)

    data_manager = test_manager.KlineDataManager(ins_ws_receiver, real_time_storage, history_storage, ins_futures_market, workers=5)
    data_manager.run()


# if __name__ == "__main__":
#     os.system('pkill -f *.py')
#     os.system('clear')
#     symbols = SystemConfig.Streaming.symbols
#     intervals = SystemConfig.Streaming.intervals
    
#     ins_public_client = public_futures.FuturesMarketFetcher()
#     ins_futures_ws_receiver = futures_ws_receiver.FuturesWebsocketReceiver(symbols=symbols, intervals=intervals)
#     ins_telegram_client = telegram_client.TelegramClient(SystemConfig.Path.telegram)
    
#     real_storage = storage.SymbolStorage(storage.IntervalStorage)  # 실시간 데이터 수집
#     history_storage = storage.SymbolStorage(storage.IntervalStorage)   # 과거 kline_data 수집

#     message = (
#         f"💻 program start!\n"
#         f"  ℹ️ ConfigSetting \n"
#         f"    🚀 Symbol     : 🪙 {', 🪙 '.join(SystemConfig.Streaming.symbols)}\n"
#         f"    🚀 Interval   : ⏳ {', ⏳ '.join(SystemConfig.Streaming.intervals)}\n"
#         )
#     ins_telegram_client.send_message_with_log(message)
#     ins_threading = handler.FuturesDataManager(real_storage=real_storage,
#                                                history_storage=history_storage,
#                                                public_futures=ins_public_client,
#                                                ws_futures=ins_futures_ws_receiver)
#     asyncio.run(ins_threading.run())