
import aiohttp
import asyncio
from typing import Final, Dict, Any, Optional, List, Union


class MarketFetcher:
    """
    Binance에서 API KEY없이 조회가능한 데이터를
    수신 및 반환한다.
    
    Alias: mk_fetcher
    """
    BASE_URL: str

    def __init__(self, base_url: str):
        self.BASE_URL: str = base_url

    async def _retrieve_api_data(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        공동 API 호출 메서드 (비공개)
        """
        url = self.BASE_URL + endpoint
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=10) as response:
                response.raise_for_status()
                return await response.json()

    async def fetch_ticker_price(
        self, symbol: Optional[str]
    ) -> Union[List[Dict[str, Union[int, str]]], Dict[str, Union[int, str]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 최신 가격을 조회 및 반환한다.
        """
        params = {"symbol": symbol} if symbol else None
        return await self._retrieve_api_data("ticker/price", params=params)

    async def fetch_book_tickers(
        self, symbol: Optional[str] = None
    ) -> Union[List[Dict[str, Union[int, str]]], Dict[str, Union[int, str]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 최고 매수/매도 가격 및 수량 정보를 조회 및 반환한다.
        """
        params = {"symbol": symbol} if symbol else None
        return await self._retrieve_api_data("ticker/bookTicker", params=params)

    async def fetch_24hr_ticker(
        self, symbol: Optional[str] = None
    ) -> Optional[List[Dict[str, Union[str, int, float]]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 24시간 가격 변동 통계정보를 조회 및 반환한다.
        """
        params = {"symbol": symbol} if symbol else None
        return await self._retrieve_api_data("ticker/24hr", params=params)

    async def fetch_klines_limit(
        self, symbol: str, interval: str, limit: int
    ) -> List[List[Union[int, str]]]:
        """
        조회할 데이터 개수를 지정하여 캔들 스틱 데이터(OHLCV)를 조회 및 반환한다.
        """
        params = {"symbol": symbol, "interval": interval, "limit": limit}
        return await self._retrieve_api_data("klines", params=params)

    async def fetch_klines_date(
        self,
        symbol: str,
        interval: str,
        start_ms_timestamp: int,
        end_ms_timestamp: int,
        limit: int = 1000
    ) -> List[List[Union[int, str]]]:
        """
        조회할 데이터의 기간을 지정하여 캔들 스틱 데이터(OHLCV)를 조회 및 반환한다.
        """
        params = {
            "symbol": symbol,
            "startTime": start_ms_timestamp,
            "endTime": end_ms_timestamp,
            "interval": interval,
            "limit":limit
        }
        return await self._retrieve_api_data("klines", params=params)

    async def fetch_order_book(
        self, symbol: str, limit: int
    ) -> Optional[Dict[str, Union[List[List[str]], int]]]:
        """
        지정 심볼의 호가 데이터(주문서)를 조회 및 반환한다.
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._retrieve_api_data("depth", params=params)

    async def fetch_recent_trades(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """
        지정 symbol의 최근 거래 목록을 조회 및 반환한다.
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._retrieve_api_data("trades", params=params)

    async def fetch_agg_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        지정 symbol의 최근 거래내역 집계(상세정보 취합) 정보를 조회 및 반환한다.
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._retrieve_api_data("aggTrades", params=params)

    async def fetch_server_time(self) -> Dict[str, int]:
        """
        서버 시간 정보를 조회 및 반환한다.
        """
        return await self._retrieve_api_data("time")

    async def ping_binance(self):
        """
        서버 상태를 확인한다.
        """
        return await self._retrieve_api_data("ping")