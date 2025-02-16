import API.Queries.Public.Futures as public_api
import API.Reciver.Futures as reciver_api
import Processor.ReciverData.Futures as handler
import Utils.DataModels as storage
import SystemConfig
import threading
import asyncio
import nest_asyncio


if __name__ == "__main__":
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_public_api = public_api.API()
    ins_reciver_api = reciver_api.API(symbols=symbols,
                                      intervals=intervals)
    
    real_storage = storage.SymbolStorage()  # 실시간 데이터 수집
    history_storage = storage.SymbolStorage()   # 과거 kline_data 수집
    
    ins_threading = handler.MarketDataHandler(real_storage=real_storage,
                                              history_storage=history_storage,
                                              ins_reciver=ins_reciver_api,
                                              ins_public=ins_public_api)
    asyncio.run(ins_threading.run())
    