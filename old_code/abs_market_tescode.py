import logging
import asyncio
from abc import ABC, abstractmethod
from http import HTTPStatus
import aiohttp
from typing import Final, List, Dict, Any, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class AbstractClass(ABC):
    BASE_URL: str = ""
    OHLCV_INTERVALS = ["3m", "5m", "15m", "30m", "4h", "8h", "12h", "1d"]
    OHLCV_COLUMNS: Final[List[str]] = [
        "Open Time",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
        "Close Time",
        "Quote Asset Volume",
        "Number of Trades",
        "Taker Buy Base Asset Volume",
        "Taker Buy Quote Asset Volume",
        "Ignore",
    ]

    @abstractmethod
    async def get_tickers_price(self):
        pass

    @abstractmethod
    async def get_book_tickers(self):
        pass

    @abstractmethod
    async def get_24hr_tickers(self):
        pass

    @abstractmethod
    async def get_klines(self, symbol: str, interval: str, limit: int):
        pass

    @abstractmethod
    async def get_order_book(self, symbol: str, limit: int):
        pass

    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int):
        pass

    @abstractmethod
    async def get_agg_trades(self, symbol: str, limit: int):
        pass

    @abstractmethod
    async def get_exchange_info(self):
        pass

    @abstractmethod
    async def get_avg_price(self, symbol: str):
        pass

    @abstractmethod
    async def get_symbol_ticker_price(self, symbol: str):
        pass

    async def _fetch_data(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """공통 API 호출 메서드"""
        url = self.BASE_URL + endpoint
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=10) as response:
                    if response.status == HTTPStatus.OK:
                        return await response.json()
                    else:
                        logging.error(
                            f"HTTP 오류: {response.status} - {response.reason}"
                        )
                        return None
        except Exception as e:
            self._handle_exception(e)
            return None

    def _handle_exception(self, e: Exception) -> None:
        """예외 처리 로직을 함수로 분리"""
        if isinstance(e, aiohttp.ClientError):
            logging.error(f"클라이언트 오류 발생: {e}")
        elif isinstance(e, asyncio.TimeoutError):
            logging.error("요청 시간 초과.")
        else:
            logging.error(f"알 수 없는 오류 발생: {e}")


class SpotMarketData(AbstractClass):
    BASE_URL: str = "https://api.binance.com/api/v3/"

    async def get_tickers_price(self):
        return await self._fetch_data(endpoint="ticker/price")

    async def get_book_tickers(self):
        return await self._fetch_data(endpoint="ticker/bookTicker")

    async def get_24hr_tickers(self):
        return await self._fetch_data(endpoint="ticker/24hr")

    async def get_klines(self, symbol: str, interval: str, limit: int = 100):
        if interval not in self.OHLCV_INTERVALS:
            raise ValueError(
                f"유효하지 않은 간격: {interval}. 사용 가능한 간격: {self.OHLCV_INTERVALS}"
            )
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        return await self._fetch_data("klines", params=params)

    async def get_order_book(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("depth", params=params)

    async def get_recent_trades(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("trades", params=params)

    async def get_agg_trades(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("aggTrades", params=params)

    async def get_exchange_info(self):
        return await self._fetch_data("exchangeInfo")

    async def get_avg_price(self, symbol: str):
        params = {"symbol": symbol.upper()}
        return await self._fetch_data("avgPrice", params=params)

    async def get_symbol_ticker_price(self, symbol: str):
        params = {"symbol": symbol.upper()}
        return await self._fetch_data("ticker/price", params=params)


class FuturesMarketData(AbstractClass):
    BASE_URL: str = "https://fapi.binance.com/fapi/v1/"

    async def get_tickers_price(self):
        return await self._fetch_data(endpoint="ticker/price")

    async def get_book_tickers(self):
        return await self._fetch_data(endpoint="ticker/bookTicker")

    async def get_24hr_tickers(self):
        return await self._fetch_data(endpoint="ticker/24hr")

    async def get_klines(self, symbol: str, interval: str, limit: int = 100):
        if interval not in self.OHLCV_INTERVALS:
            raise ValueError(
                f"유효하지 않은 간격: {interval}. 사용 가능한 간격: {self.OHLCV_INTERVALS}"
            )
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        return await self._fetch_data("klines", params=params)

    async def get_order_book(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("depth", params=params)

    async def get_recent_trades(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("trades", params=params)

    async def get_agg_trades(self, symbol: str, limit: int = 100):
        params = {"symbol": symbol.upper(), "limit": limit}
        return await self._fetch_data("aggTrades", params=params)

    async def get_exchange_info(self):
        return await self._fetch_data("exchangeInfo")

    async def get_avg_price(self, symbol: str):
        params = {"symbol": symbol.upper()}
        return await self._fetch_data("avgPrice", params=params)

    async def get_symbol_ticker_price(self, symbol: str):
        params = {"symbol": symbol.upper()}
        return await self._fetch_data("ticker/price", params=params)


# 비동기 실행
if __name__ == "__main__":
    # 예시 실행
    async def main():
        spot_data = SpotMarketData()
        futures_data = FuturesMarketData()

        # SpotMarketData 예시 호출
        spot_price = await spot_data.get_tickers_price()
        print("Spot Ticker Price:", spot_price)

        # FuturesMarketData 예시 호출
        futures_price = await futures_data.get_tickers_price()
        print("Futures Ticker Price:", futures_price)

        # 추가된 get_avg_price 호출 예시
        avg_price = await spot_data.get_avg_price("BTCUSDT")
        print("Average Price for BTCUSDT:", avg_price)

        # 추가된 get_symbol_ticker_price 호출 예시
        symbol_price = await spot_data.get_symbol_ticker_price("BTCUSDT")
        print("Symbol Ticker Price for BTCUSDT:", symbol_price)

    asyncio.run(main())
