import aiohttp
import asyncio
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.DataStorage.NodeStorage as storage
import Workspace.Utils.BaseUtils as base_utils

class KlineCycle:
    def __init__(self, symbols: List, intervals: List, storage: storage, limit: int = 480):
        self.symbols = symbols
        self.intervals = intervals
        self.limit = limit
        self.storage = storage
        self.BASE_URL = "https://fapi.binance.com/fapi/v1/"
        self.session = aiohttp.ClientSession()
    
    async def _retrieve_api_data(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Any:
        url = self.BASE_URL + endpoint
        async with self.session.get(url, params=params, timeout=10) as response:
            response.raise_for_status()
            return await response.json()

    async def _sleep_next_minute(self, minutes: int = 1, buffer_time_sec: float = 0) -> datetime:
        """
        ⏱️ 지정한 시간(분)의 정각까지 비동기식으로 대기한다.

        Args:
            minutes (int, optional): 대기 시간
            buffer_time_sec (float, optional): 추가 대기 시간

        Returns:
            datetime: _description_
        """
        seconds_per_minute = 60
        sleep_seconds = seconds_per_minute * minutes
        current_time = datetime.now()
        ms_second = current_time.microsecond / 1_000_000
        elapsed_seconds = current_time.second + ms_second
        diff_second = sleep_seconds - elapsed_seconds
        await asyncio.sleep(max(1, diff_second + buffer_time_sec))
        return datetime.now()
    
    async def _init_setting(self):
        """
        🐣 전체 데이터를 초기 업데이트 한다.
        """
        print("🚀 Kline 전체 데이터 수신 중...")
        tasks = [
            self._update_storage(symbol, interval, self.limit)
            for symbol in self.symbols for interval in self.intervals
        ]
        await asyncio.gather(*tasks)
        print("👍🏻 수신 완료!")

    async def _fetch_kline_limit(self, symbol: str, interval: str, limit: int) -> List[List[Union[int, str]]]:
        """
        🚀 kline_data를 수신한다.

        Args:
            symbol (str): symbol
            interval (str): interval
            limit (int): 수신할 데이터 개수

        Returns:
            List[List[Union[int, str]]]: kline data
        """
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        return await self._retrieve_api_data("klines", params=params)

    async def _update_storage(self, symbol: str, interval: str, limit: int):
        """
        💾 수신된 데이터를 storage에 저장한다.

        Args:
            symbol (str): main field
            interval (str): sub field
            limit (int): 수신할 데이터 개수
        """
        self.storage.set_data(
            symbol,
            f"interval_{interval}",
            await self._fetch_kline_limit(symbol, interval, limit)
        )
    
    async def start(self):
        await self._init_setting()
        while True:
            valid_intervals = [interval for interval in self.intervals if base_utils.is_time_match(interval)]
            if valid_intervals:
                start = datetime.now()
                tasks = [
                    asyncio.create_task(self._update_storage(symbol, interval, self.limit))
                    for symbol in self.symbols for interval in valid_intervals
                ]
                await asyncio.gather(*tasks)
                end = datetime.now()
                print(f"소요시간: {(end - start).total_seconds():,.2f} sec")
            await self._sleep_next_minute(1, 0.5)
    
    async def close(self):
        await self.session.close()

if __name__ == "__main__":
    async def main():
        symbols = ['BTCUSDT', 'XRPUSDT', 'TRXUSDT', 'ADAUSDT', 'ETHUSDT']
        intervals = ['3m', '5m', '30m', '2h', '4h', '1d']
        limit = 480
        sub_storage = storage.SubStorage([f"interval_{i}" for i in intervals])
        kline_storage = storage.MainStorage(symbols, sub_storage)

        obj = KlineCycle(symbols, intervals, kline_storage, limit)
        
        try:
            await obj.start()
        finally:
            await obj.close()

    asyncio.run(main())
