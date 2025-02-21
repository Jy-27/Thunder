from .MarketFetcher import MarketFetcher
from typing import Dict, Any, List, Union


class FuturesMarketFetcher(MarketFetcher):
    """
    Futures market에서 API-KEY가 필요 없이 조회할 수 있는 함수들의 집합이다.
    
    Alias: futures_mk_fecher
    """
    BASE_URL = "https://fapi.binance.com/fapi/v1/"

    def __init__(self):
        super().__init__(base_url=self.BASE_URL)

    # Futures 거래소의 메타데이터 수신
    def fetch_exchange_info(self) -> Dict[str, Any]:
        """
        Futures 거래소의 메타정보를 수신한다.

        Returns:
            Dict: 대용량 데이터 수신됨.
        """
        exchange_data = self._retrieve_api_data("exchangeInfo")  # type: ignore
        return exchange_data if exchange_data is not None else {}

    def fetch_mark_price(self, symbol: str) -> Dict:
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
        return self._retrieve_api_data("premiumIndex", params)

    def fetch_funding_rate(
        self, symbol: str, limit: int
    ) -> List[Dict[str, Union[int, str]]]:
        """펀딩 비율 기록 조회"""
        params = {"symbol": symbol, "limit": limit}
        return self._retrieve_api_data("fundingRate", params)

    def fetch_all_force_orders(self, symbol: str, limit: int):
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
        return self._retrieve_api_data("allForceOrders", params)

    def fetch_open_interest(self, symbol: str) -> Dict[str, Union[int, str]]:
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
        return self._retrieve_api_data("openInterest", params)


if __name__ == "__main__":
    from pprint import pprint
    import utils

    ins_market = Manager()
    symbol = "XRPUSDT"
    interval = "3m"

    price = ins_market.fetch_ticker_price(symbol)
    print(f"1. fetch_ticker_price:")
    pprint(price)

    book = ins_market.fetch_book_tickers(symbol)
    print(f"\n2. fetch_book_tickers:")
    pprint(book)

    hr24_ticker = ins_market.fetch_24hr_ticker(symbol)
    print(f"\n3. fetch_24hr_ticker:")
    pprint(hr24_ticker)

    k_limit = 1
    kline_limit = ins_market.fetch_klines_limit(symbol, interval, k_limit)
    print(f"\n4. fetch_kline_limit:")
    pprint(kline_limit)

    start_date = "2025-01-01 09:00:00"
    start_ms_timestamp = utils._convert_to_timestamp_ms(start_date)
    end_date = "2025-01-02 08:59:59"
    end_ms_timestamp = utils._convert_to_timestamp_ms(end_date)
    print(f"\n5. fetch_kline_date: 축소 출력")
    kline_date = ins_market.fetch_klines_date(
        symbol, interval, start_ms_timestamp, end_ms_timestamp
    )
    print(True if kline_date else False)

    r_trades_limit = 1
    recent_trades = ins_market.fetch_recent_trades(symbol, r_trades_limit)
    print(f"\n6. fetch_recent_trades:")
    pprint(recent_trades)

    book_limit = 5  # 5, 10, 20, 50, 100, 500, 1000
    order_book = ins_market.fetch_order_book(symbol, book_limit)
    print(f"\n7. fetch_order_book:")
    pprint(order_book)

    trades_limit = 1
    agg_trades = ins_market.fetch_agg_trades(symbol, trades_limit)
    print(f"\n8. fetch_agg_trades:")
    pprint(agg_trades)

    exchange_info = ins_market.fetch_exchange_info()
    print(f"\n9. fetch_exchange_info: 축소 출력")
    print(True if exchange_info else False)

    server_time = ins_market.fetch_server_time()
    print(f"\n10. fetch_server_time:")
    print(server_time)

    mark_price = ins_market.fetch_mark_price(symbol)  # , 500)
    print(f"\n11. fetch_mark_price:")
    pprint(mark_price)

    rate_limit = 1
    funding_rate = ins_market.fetch_funding_rate(symbol, rate_limit)
    print(f"\n12. fetch_funding_rate:")
    pprint(funding_rate)

    interest = ins_market.fetch_open_interest(symbol)
    print(f"\n13. fetch_open_interest:")
    pprint(interest)

    pint_signal = ins_market.ping_binance()
    print(f"\n14. pint_balance:")
    print(pint_signal)
