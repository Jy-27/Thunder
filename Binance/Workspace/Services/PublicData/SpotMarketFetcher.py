from .MarketFetcher import MarketFetcher
from typing import Dict, Any, Optional, Union
import asyncio


class SpotMarketFetcher(MarketFetcher):
    """
    Spot market에서 API-KEY가 필요 없이 조회할 수 있는 함수들의 집합이다.
    """
    BASE_URL = "https://api.binance.com/api/v3/"

    def __init__(self):
        super().__init__(base_url=self.BASE_URL)

    # spot 거래소의 메타데이터 수신
    def fetch_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Spot 거래소의 메타정보를 수신한다.

        Returns:
            Dict: 대용량 데이터 수신됨.
        """
        if symbol:
            query_params = {"symbol": symbol}
            exchange_data = self._retrieve_api_data("exchangeInfo", params=query_params)
            return exchange_data if exchange_data is not None else {}

        exchange_data = self._retrieve_api_data("exchangeInfo")
        return exchange_data if exchange_data is not None else {}

    # Ticker별 평균가격 수신
    def fetch_avg_price(self, symbol: str) -> Dict[str, Union[int, str]]:
        """
        지정 symbol의 최근 5분간 평균 가격을 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'

        Returns:
            Dict:
            {
                'closeTime': 1739239275426,
                'mins': 5, 'price': '2.45732311'
            }
        """
        params = {"symbol": symbol}
        return self._retrieve_api_data("avgPrice", params=params)

    def fetch_historical_trades(self, symbol:str, limit:Optional[int]=None, from_id:Optional[int]=None):
        """
        과거 체결 내역을 상세 조회 및 반환한다.

        Args:
            symbol (str): _description_
            limit (Optional[int], optional): _description_. Defaults to None.
            from_id (Optional[int], optional): _description_. Defaults to None.

        Notes:
            Futures는 API-KEY가 필요하다. 그러므로 동일 기능함수는 Client 콤퍼넌트에 있다.

        Returns:
            _type_: _description_
        """
        
        params = {
            "symbol": symbol
        }
        if limit:
            params["limit"] = limit
        if from_id:
            params["fromId"] = from_id
        
        return self._retrieve_api_data("historicalTrades", params)

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

    avg_price = ins_market.fetch_avg_price(symbol)
    print(f"\n10. fetch_avg_price:")
    pprint(avg_price)

    server_time = ins_market.fetch_server_time()
    print(f"\n11. fetch_server_time:")
    print(server_time)

    pint_signal = ins_market.ping_binance()
    print(f"\n12. pint_balance:")
    print(pint_signal)

    limit = 1
    historical_trades = ins_market.fetch_historical_trades(symbol, limit)
    print(f"\n13. fetch_historical_trades:")
    print(historical_trades)