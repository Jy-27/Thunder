import concurrent.futures
import API.Queries.Public.Futures as public_api
import Utils.DataModels as storage
import threading
import datetime

ins_public_api = public_api.API()

api_storage = storage.SymbolStorage()

symbols = ["BTCUSDT","TRXUSDT","ETHUSDT","XRPUSDT","SOLUSDT","BNBUSDT"]
# intervals = ["1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "8h", "12h", "1d", "3d", "1w", "1M",]
intervals = ["3m", "5m","1h"]#, "2h", "4h","8h", "1d"]#

def fetch_and_update(symbol, interval, api, storage):
    """심볼과 인터벌 데이터를 API에서 가져와 저장하는 함수"""
    kline_data = api.fetch_klines_limit(symbol=symbol, interval=interval, limit=480)
    storage.update_data(symbol, interval, kline_data)

def threaded_data_fetch(symbols, intervals, api, storage):#, max_workers=100):
    """스레드를 사용하여 심볼과 인터벌별 데이터를 병렬로 가져옴"""
    max_workers = 5
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for symbol in symbols:
            for interval in intervals:
                futures.append(executor.submit(fetch_and_update, symbol, interval, api, storage))
        
        # 모든 작업 완료 대기
        concurrent.futures.wait(futures)

# 실행 예제
if __name__ == "__main__":
    start = datetime.datetime.now()
    threaded_data_fetch(symbols, intervals, ins_public_api, api_storage)
    print(api_storage)
    end = datetime.datetime.now()
    print(f"diff_time: {end-start}")