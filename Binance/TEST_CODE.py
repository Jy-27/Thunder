import Services.PublicData.FuturesMarketFetcher as public_futures
import Services.Receiver.FuturesWebsocketReceiver as futures_ws_receiver
import Services.PrivateAPI.Messaging.TelegramClient as telegram_client
import Processor.DataReceiver.FuturesDataManager as handler
import Processor.DataStorage.DataStorage as storage
import SystemConfig
import asyncio
import os

if __name__ == "__main__":
    os.system('pkill -f *.py')
    os.system('clear')
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_public_client = public_futures.FuturesMarketFetcher()
    ins_futures_ws_receiver = futures_ws_receiver.FuturesWebsocketReceiver(symbols=symbols, intervals=intervals)
    ins_telegram_client = telegram_client.TelegramClient(SystemConfig.Path.telegram)
    
    real_storage = storage.SymbolStorage(storage.IntervalStorage)  # 실시간 데이터 수집
    history_storage = storage.SymbolStorage(storage.IntervalStorage)   # 과거 kline_data 수집

    message = (
        f"💻 program start!\n"
        f"  ℹ️ ConfigSetting \n"
        f"    🚀 Symbol     : 🪙 {', 🪙 '.join(SystemConfig.Streaming.symbols)}\n"
        f"    🚀 Interval   : ⏳ {', ⏳ '.join(SystemConfig.Streaming.intervals)}\n"
        )
    ins_telegram_client.send_message_with_log(message)
    ins_threading = handler.FuturesDataManager(real_storage=real_storage,
                                               history_storage=history_storage,
                                               public_futures=ins_public_client,
                                               ws_futures=ins_futures_ws_receiver)
    asyncio.run(ins_threading.run())