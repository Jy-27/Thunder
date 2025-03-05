from .MarketFetcher import MarketFetcher
from typing import Dict, Any, List, Union
import asyncio

class FuturesMarketFetcher(MarketFetcher):
    """
    Futures market에서 API-KEY가 필요 없이 조회할 수 있는 함수들의 집합이다.
    
    Alias: futures_mk_fetcher
    """
    BASE_URL = "https://fapi.binance.com/fapi/v1/"

    def __init__(self):
        super().__init__(base_url=self.BASE_URL)

    # Futures 거래소의 메타데이터 수신
    async def fetch_exchange_info(self) -> Dict[str, Any]:
        """
        Futures 거래소의 메타정보를 수신한다.

        Returns:
            Dict: 대용량 데이터 수신됨.
        """
        exchange_data = self._retrieve_api_data("exchangeInfo")  # type: ignore
        return await exchange_data if exchange_data is not None else {}

    async def fetch_mark_price(self, symbol: str) -> Dict:
        """
        mark price를 조회 및 반환한다. 최신 가격과는 다른 개념이다.
        마크 가격, 펀딩 비율, 인덱스 가격 등 포함되어 있다.

        Args:
            symbol (str): 'BTCUSDT'

        Returns:
            Dict: {
                'estimatedSettlePrice': '97594.14545956',
                'indexPrice': '97738.25111111',
                'interestRate': '0.00010000',
                'lastFundingRate': '0.00003676',
                'markPrice': '97695.38508889',
                'nextFundingTime': 1739260800000,
                'symbol': 'BTCUSDT',
                'time': 1739233574000
                }
        """
        params = {"symbol": symbol}
        return await self._retrieve_api_data("premiumIndex", params)

    async def fetch_funding_rate(
        self, symbol: str, limit: int
    ) -> List[Dict[str, Union[int, str]]]:
        """펀딩 비율 기록 조회"""
        params = {"symbol": symbol, "limit": limit}
        return await self._retrieve_api_data("fundingRate", params)

    async def fetch_all_force_orders(self, symbol: str, limit: int):
        """
        ❌ 서비스 제공 중단됨.

        최근 강제 청산내역을 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            limit (int): 1

        Returns:
            Dict: {
                "symbol": "BTCUSDT",
                "price": "43500.00",
                "origQty": "0.5",
                "executedQty": "0.5",
                "averagePrice": "43520.00",
                "time": 1643059179325
                }
        """
        params = {"symbol": symbol, "limit": limit}
        return await self._retrieve_api_data("allForceOrders", params)

    async def fetch_open_interest(self, symbol: str) -> Dict[str, Union[int, str]]:
        """
        미체결된 계약(포지션)수량 정보를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'

        Returns:
            Dict: {
                'symbol': 'BTCUSDT',
                'openInterest': '76003.744',
                'time': 1739236807682
                }
        """
        params = {"symbol": symbol}
        return await self._retrieve_api_data("openInterest", params)