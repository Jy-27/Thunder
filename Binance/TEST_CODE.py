import Client.Queries.Public.Futures as public_client
import Client.Queries.Private.Futures as private_client
import Client.Reciver.Futures as reciver_client
import Processor.ReciverData.Futures as handler
import Utils.DataModels as storage
import SystemConfig
import threading
import asyncio
import nest_asyncio

if __name__ == "__main__":
    symbols = SystemConfig.Streaming.symbols
    intervals = SystemConfig.Streaming.intervals
    
    ins_public_client = public_client.Client()
    ins_reciver_client = reciver_client.Client(symbols=symbols, intervals=intervals)
    
    real_storage = storage.SymbolStorage()  # 실시간 데이터 수집
    history_storage = storage.SymbolStorage()   # 과거 kline_data 수집
    
    ins_threading = handler.MarketDataHandler(real_storage=real_storage,
                                              history_storage=history_storage,
                                              reciver_client=ins_reciver_client,
                                              public_client=ins_public_client)
    asyncio.run(ins_threading.run())
    