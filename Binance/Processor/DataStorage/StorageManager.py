from typing import List


class SymbolDataSubset:
    """특정 심볼 데이터의 서브셋을 생성하는 클래스"""

    def __init__(self, *symbols, storage):
        """선택한 심볼만 포함하는 객체 생성"""
        self.__class__.__slots__ = symbols  # ✅ __slots__을 동적으로 지정
        for symbol in symbols:
            setattr(self, symbol, getattr(storage, symbol))  # ✅ 해당 심볼 데이터 저장

    def get_data(self, symbol: str, interval: str):
        """특정 심볼의 특정 interval 데이터를 가져옴"""
        symbol_obj = getattr(self, symbol)
        interval_key = f"interval_{interval}"
        return getattr(symbol_obj, interval_key)

    def clear(self):
        """저장된 데이터를 초기화"""
        for slot in self.__slots__:
            setattr(self, slot, None)  # ✅ 데이터를 None으로 초기화

class SyncStorage:
    def __init__(self, symbols:List, intervals:List):
        self.symbols = symbols
        self.intervals = intervals
        
    def data_sync(self, history_storage, real_time_stroage):
        for symbol in self.symbols:
            for interval in self.intervals:
                history_data = history_storage.get_data(symbol=symbol, interval=interval)
                real_time_data = real_time_stroage.get_data(symbol=symbol, interval=interval)
                update_data = self._merge_kline_data(history_data, real_time_data)
                history_storage.update_data(symbol, *(interval, update_data))
                
    def _format_kline_data(self, real_time_data):
        return [real_time_data["t"],
                real_time_data["o"],
                real_time_data["h"],
                real_time_data["l"],
                real_time_data["c"],
                real_time_data["v"],
                real_time_data["T"],
                real_time_data["q"],
                real_time_data["n"],
                real_time_data["V"],
                real_time_data["Q"],
                real_time_data["B"]]
        
    def _merge_kline_data(self, history_data, real_time_data):
        convert_to_last_data = self._format_kline_data(real_time_data)
        history_last_data = history_data[-1]
        if convert_to_last_data[0] == history_last_data[0] and convert_to_last_data[6] == history_last_data[6]:
            history_data[-1] = convert_to_last_data
        else:
            history_data.append(convert_to_last_data)
        return history_data
                            

if __name__ == "__main__":
    import sys
    import os
    sys.path.append(os.path.abspath("../../"))

    import Services.PublicData.FuturesMarketFetcher as futures_market
    import Processor.DataStorage.DataStorage as storage
    import SystemConfig

    from pprint import pprint
    
    ins_market = futures_market.FuturesMarketFetcher()
    ins_storage = storage.SymbolStorage(storage.IntervalStorage)

    for symbol in SystemConfig.Streaming.symbols:
        for interval in SystemConfig.Streaming.intervals:
            data = ins_market.fetch_klines_limit(symbol, interval, 480)
            ins_storage.update_data(symbol, *(interval, data))

    # ✅ 사용 예시
    subset_storage = SymbolDataSubset("BTCUSDT", "ETHUSDT", storage=ins_storage)

    # 데이터 조회
    pprint(subset_storage.get_data("BTCUSDT", "1m"))  # ✅ BTCUSDT의 1m 데이터 가져오기

    # 데이터 초기화
    subset_storage.clear()