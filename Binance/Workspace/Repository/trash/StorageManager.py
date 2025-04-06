from typing import List, Any

import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
import Workspace.Utils.TradingUtils as trading_utils

#힌트용
from Workspace.DataStorage.DataStorage import MainStroage as storage

class SyncStorage:
    @classmethod
    def sync_data(cls, storage_history:storage, storage_real_time:storage):
        """
        🔄 실시간 저장소를 이용하여 히스토리 저장소 전체를 업데이트(동기화) 한다.

        Args:
            storage_history (storage): 거래기록 저장소
            storage_real_time (storage): 실시간 저장소
        """
        main_fields, sub_fields = cls.get_all_fields(storage_history)

        for main_field in main_fields:
            for sub_field in sub_fields:
                history_data = storage_history.get_data(main_field, sub_field)
                real_time_data = storage_real_time.get_data(main_field, sub_field)
                update_data = cls.data_merge(history_data, real_time_data)
                storage_history.set_data(main_field, sub_field, update_data)

    @classmethod
    def data_merge(cls, target_data:storage, new_data:storage):
        target_timestamp = target_data[-1][0]
        new_timestamp = new_data[0]
        if target_timestamp == new_timestamp:
            target_data[-1] = new_data
        else:
            target_data.append(new_data)
        return target_data
        
    
    @classmethod
    def get_all_fields(cls, main_storage:storage) -> List[str]:
        main_field =main_storage.get_fields()
        field = main_field[0]
        sub_field = getattr(main_storage, field).get_fields()
        return main_field, sub_field

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