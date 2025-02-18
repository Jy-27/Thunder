

#My Module
import SystemConfig
import Services.Receiver.FuturesWebsocketReceiver as ws_recevier
import Services.PublicData.FuturesMarketFetcher as market_fetcher
import Processor.DataStorage.DataStorage as storage
import Processor.DataReceiver.FuturesDataManager as data_manager
import Processor.DataStorage.OrderSheet as sheet
import Processor.DataStorage.StorageManager as storage_mananger
import asyncio
import Utils.BaseUtils as base_utils
import concurrent.futures
import time

if __name__ == "__main__":

    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    limit = SystemConfig.Streaming.kline_limit
    ins_ws_receiver = ws_recevier.FuturesWebsocketReceiver(symbols, intervals)
    ins_market_fetcher = market_fetcher.FuturesMarketFetcher()    
    real_time_storage = storage.SymbolStorage(storage.IntervalStorage)
    history_storage = storage.SymbolStorage(storage.IntervalStorage)

    ins_sync_storage = storage_mananger.SyncStorage(SystemConfig.Streaming.symbols, SystemConfig.Streaming.intervals)
    ins_split_storage = storage_mananger.SymbolDataSubset(*(SystemConfig.Streaming.symbols), storage=history_storage)
    # 이걸 병렬로 돌려?
    ins_data_manager = data_manager.KlineDataManager(ins_ws_receiver,
                                                    real_time_storage,
                                                    history_storage,
                                                    ins_market_fetcher,
                                                    3,
                                                    limit)

    def dummy(data):
        print(data)

    def multiprocessing_run():
        time.sleep(10)
        print(False)
        while True:
            # 싱크 실행
            print(True)
            ins_sync_storage.data_sync(history_storage, real_time_storage)
            with concurrent.futures.ProcessPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(dummy, history_storage.get_data_symbol(symbol)) for symbol in symbols]

                for future in concurrent.futures.as_completed(futures):
                    future.result()
            base_utils.sleep_next_minute(1)

    def start():
        asyncio.run(ins_data_manager.start_async_tasks())
        ins_data_manager.start_threading()
        print("????")
        multiprocessing_run()

if __name__ == "__main__":
    ins_data_manager.start()