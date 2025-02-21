from typing import List

import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Utils.TradingUtils as trading_utils

#힌트용
from Workspace.DataStorage.DataStorage import MainStroage as storage

class SymbolDataSubset:
    """
    ❌ storage 코드 수정되면서 동작 불가함.
    특정 심볼 데이터의 서브셋을 생성하는 클래스"""

    def __init__(self, *symbols:tuple(str), storage:storage):
        """선택한 심볼만 포함하는 객체 생성"""
        self.__class__.__slots__ = symbols  # ✅ __slots__을 동적으로 지정
        for symbol in symbols:
            setattr(self, symbol, getattr(storage, symbol))  # ✅ 해당 심볼 데이터 저장

    def get_data_symbol(self, symbol:str):
        return getattr(self, symbol)

    def get_data_detail(self, symbol: str, interval: str):
        """특정 심볼의 특정 interval 데이터를 가져옴"""
        symbol_obj = getattr(self, symbol)
        interval_key = f"interval_{interval}"
        return getattr(symbol_obj, interval_key)

    def clear(self):
        """저장된 데이터를 초기화"""
        for slot in self.__slots__:
            setattr(self, slot, None)  # ✅ 데이터를 None으로 초기화

class SyncStorage:
    @classmethod
    def sync_data(cls, storage_history:storage, storage_real_time:storage):
        """
        🔄 실시간 저장소를 이용하여 히스토리 저장소 전체를 업데이트(동기화) 한다.

        Args:
            storage_history (storage): 거래기록 저장소
            storage_real_time (storage): 실시간 저장소
        """
        
        fields = cls._get_fields(storage_history)
        for main_field in fields["target"]:
            for sub_field in fields["new"]
                history_data = storage_history.get_data(main_field, sub_field)
                real_time_data = storage_real_time.get_data(main_field, sub_field)
                update_data = cls._merge_data(history_data, real_time_data)
                storage_history.set_data(main_field, sub_field, update_data)

    @classmethod
    def _get_fields(cls, storage:storage):
        """
        👻 메인과 서브 저장소의 필드명을 조회한다.

        Args:
            storage (storage): class strage

        Returns:
            Dict: 필드정보
        """
        return {"target":storage.get_main_field(),
                "new":storage.get_sub_field()}
    
    @classmethod
    def _merge_data(cls, target_data:List[Any], new_data:List[Any]) -> List[Any]:
        """
        👻 실시간 저장소를 이용하여 히스토리 저장소를 동기화 한다.

        Args:
            target_data (List[Any]): old data
            new_data (List[Any]): new data

        Returns:
            List[Any]: update data
        """
        old_last_data = target_data[-1]
        if new_data[0] == old_last_data[0] and new_data[6] == old_last_data[6]:
            target_data[-1] = new_data
        else:
            history_data.append(new_data)
        return target_data




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