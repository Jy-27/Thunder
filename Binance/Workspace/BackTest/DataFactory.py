from typing import List, Dict, Optional
import numpy as np
import asyncio

from typing import Dict, List
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import FuturesMarketFetcher
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig

ins_market_fetcher = FuturesMarketFetcher()

class FactoryManager:
    """
    백테스트에 사용할 시계열 데이터를 생성한다.
    """
    def __init__(self, start_date:str, end_date:str):
        self.symbol: List[str] = SystemConfig.Streaming.symbols
        self.base_interval: str = '1m'
        
        # 기존 intervals 리스트를 수정하지 않고 새로운 리스트로 할당
        self.intervals: List[str] = (
            [self.base_interval] + SystemConfig.Streaming.intervals
            if self.base_interval not in SystemConfig.Streaming.intervals
            else SystemConfig.Streaming.intervals
        )
        self.start_date = start_date + " 09:00:00"
        self.end_date = end_date + " 08:59:59"


    def generate_timestamp_ranges(self, interval: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[List[int]]:
        """
        interval별로 timestamp 테이블을 구성한다.

        Args:
            interval (str): interval 값
            start_date (Optional[str], optional): 시작 날짜
            end_date (Optional[str], optional): 종료 날짜

        Raises:
            ValueError: interval 값 오입력시

        Returns:
            List[List[int]]: timestamp 값
        """
        start_date = self.start_date if start_date is None else start_date + " 09:00:00"
        end_date = self.end_date if end_date is None else end_date + " 08:59:59"

        interval_step = base_utils.get_interval_ms_seconds(interval)
        if interval_step is None:
            raise ValueError(f"interval step값 없음 - {interval_step}")
        
        MAX_LIMIT = 900
        start_ts = base_utils.convert_to_timestamp_ms(date=start_date)
        end_ts = base_utils.convert_to_timestamp_ms(date=end_date)# + 999
        
        timestamp_ranges = []
        while start_ts < end_ts:
            next_end_ts = min(start_ts + interval_step * MAX_LIMIT - 1, end_ts)
            timestamp_ranges.append([start_ts, next_end_ts])
            start_ts = next_end_ts + 1
        
        return timestamp_ranges

    
    async def get_kline_data(self, symbol:Optional[str]=None, intervals:Optional[str]=None, start_date:Optional[str]=None, end_date:Optional[str]=None):
        """
        kline data를 수신한다.

        Args:
            symbol (Optional[str], optional): 수신할 데이터 심볼값
            interval (Optional[str], optional): 수신할 데이터 interval 값
            start_date (Optional[str], optional): 데이터 시작 날짜
            end_date (Optional[str], optional): 데이터 종료 날짜

        Returns:
            List: 수신데이터 값
        """
        symbol = symbol if symbol is not None else self.symbol
        intervals = intervals if intervals is not None else self.intervals
        # start_date = start_date if start_date is not None else self.start_date
        # end_date = end_date if end_date is not None else self.end_date

        result = {}
        for interval in intervals:
            kline_data = []
            timestamp_range = self.generate_timestamp_ranges(interval, start_date, end_date)
            for start_timestamp, end_timesatmp in timestamp_range:
                fetch_data = await ins_market_fetcher.fetch_klines_date(symbol, interval, start_timestamp, end_timesatmp)
                kline_data.extend(fetch_data)
                await asyncio.sleep(0.2)
                print(base_utils.convert_to_datetime(end_timesatmp))
            print(f"  📨 {symbol}_{interval} 수신 완료")
            result[interval] = kline_data
        print(f"  👍 작업 완료.!")
        return result

    def generate_kline_closing_sync(self, kline_data: Dict):
        intervals = list(kline_data.keys())
        
        result = {}
        
        data_lengh = len(kline_data[intervals[0]][0])
        dummy_data = [0 for _ in range(data_lengh)]

        for interval in intervals:
            kline_data[interval].insert(0, dummy_data)
            # kline_data[interval] = np.array(kline_data[interval], float)
        
        base_data = np.array(kline_data[intervals[0]], float)
        
        for interval in intervals:
            if interval == intervals[0]:
                result[interval] = base_data
                print(interval)
                continue
            
            timestamp_range = base_utils.get_interval_ms_seconds(interval) - 1
            interval_data = np.array(kline_data[interval], float)
            temp_data = []
            
            for data in base_data:
                open_timestamp = data[0]  # 시작 타임스템프
                open_price = data[1]  # 시작 가격
                high_price = data[2]  # 최고 가격
                low_price = data[3]  # 최저 가격
                close_price = data[4]  # 마지막 가격
                volume = data[5]  # 거래량(단위 : coin)
                close_timestamp = data[6]  # 종료 타임스템프
                volume_total_usdt = data[7]  # 거래량(단위 : usdt)
                trades_count = data[8]  # 총 거래횟수
                taker_asset_volume = data[9]  # 시장가 주문 거래량(단위 : coin)
                taker_quote_volume = data[10]  # 시장가 주문 거래량(단위 : usdt)
                
                # print(interval_data)
                
                condition = np.where(
                    (interval_data[:, 0] <= open_timestamp)
                    & (interval_data[:, 6] >= close_timestamp))

                # print(condition)
                target_data = interval_data[condition]
                
                # print(f"interval:{interval} - {len(target_data)}")
                
                target_open_timestamp = target_data[0, 0]  # 단일값이 확실할 경우
                target_close_timestamp = target_data[0, 6]  # 단일값이 확실할 경우

                new_data_condition = np.where(
                    (base_data[:, 0] >= target_open_timestamp)
                    & (base_data[:, 6] <= close_timestamp)
                )  # close_timestamp는 현재 data종료 시간 기준으로 해야한다.

                new_base_data = base_data[new_data_condition]

                timestamp_diff = new_base_data[-1, 6] - new_base_data[0, 0]
                if timestamp_range == timestamp_diff:
                    new_data = target_data[0]
                else:
                    new_data = [
                        target_open_timestamp,
                        new_base_data[0, 1],
                        np.max(new_base_data[:, 2]),
                        np.min(new_base_data[:, 3]),
                        new_base_data[-1, 4],
                        np.sum(new_base_data[:, 5]),
                        target_close_timestamp,
                        np.sum(new_base_data[:, 7]),
                        np.sum(new_base_data[:, 8]),
                        np.sum(new_base_data[:, 9]),
                        np.sum(new_base_data[:, 10]),
                        0,
                    ]
                temp_data.append(new_data)
            result[interval] = np.array(temp_data, float)
        
        return result

if __name__ == "__main__":
    
    start_date = '2025-01-01'# 09:00:00'
    end_date = '2025-01-03'# 08:59:59'
    intervals = SystemConfig.Streaming.all_intervals
    symbol = 'BTCUSDT'

    ins = FactoryManager(start_date, end_date)
    data = asyncio.run(ins.get_kline_data())

    closing_sync = ins.generate_kline_closing_sync(data)
    
    print(np.sum(closing_sync["1m"][11:15, 7]))
    # print(closing_sync["5m"][9, 7])
    print(closing_sync["5m"][:15, 7])