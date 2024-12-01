import logging
import asyncio
import aiohttp
import utils
import datetime
from http import HTTPStatus
from typing import Final, Dict, Any, Optional, List, Union, TypeVar, cast

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
T = TypeVar("T")


class MarketDataManager:
    BASE_URL: str
    OHLCV_INTERVALS: Final[list] = [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        # "1w",
        # "1M",
    ]
    OHLCV_COLUMNS: Final[list[str]] = [
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

    def __init__(self, base_url: str):
        BASE_URL: str = base_url

    # 공통 API 호출 메서드
    async def __retrieve_api_data(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        1. 기능 : 공통 API 호출 메서드
        2. 매개변수
            1) endpoint : Base url제외 나머지 주소
            2) params : 각 함수별 별도 지정
        """
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
            self.__handle_exception(e)
            return None

    # 예외 처리 로직
    def __handle_exception(self, e: Exception) -> None:
        """
        1. 기능 : Error발생시 대응위한 예외 로직코드
        2. 매개변수 : 해당없음.
        """
        if isinstance(e, aiohttp.ClientError):
            logging.error(f"클라이언트 오류 발생: {e}")
        elif isinstance(e, asyncio.TimeoutError):
            logging.error("요청 시간 초과.")
        else:
            logging.error(f"알 수 없는 오류 발생: {e}")

    # fetch_kiles함수 parameter 유효성 확인
    def __validate_kline_params(
        self,
        interval: str,
        limit: Optional[int] = None,
        start_date: Optional[Union[str, datetime.datetime]] = None,
        end_date: Optional[Union[str, datetime.datetime]] = None,
    ):
        """
        1. 기능 : fetch_klines_limit 또는 fetch_klines_date함수의 parameter 유효성 검사
        2. 매개변수
            1) interval : self.OHLCV_INTERVALS 리스트 참조
            2) limit : Data 수신 개수
            3) start_date : 시작 날짜 예) '2024-01-01'
            4) end_date : 종료 날짜 예) '2024-01-05'
        """

        MAX_ALLOWED_LIMIT = 1_000

        if interval not in self.OHLCV_INTERVALS:
            raise ValueError(f"interval값 입력 오류 >> {interval}")

        if start_date and end_date:
            interval_amount = int(interval[:-1])  # 숫자 부분
            interval_unit_type = interval[-1]  # 단위 부분

            # 간격 단위를 밀리초로 변환
            unit_milliseconds = cast(
                int,
                {
                    "m": 60 * 1000,
                    "h": 60 * 60 * 1000,
                    "d": 24 * 60 * 60 * 1000,
                    "w": 7 * 24 * 60 * 60 * 1000,
                    "M": 30 * 24 * 60 * 60 * 1000,
                }.get(interval_unit_type),
            )

            start_timestamp = utils._convert_to_timestamp_ms(date=start_date)
            end_timestamp = utils._convert_to_timestamp_ms(date=end_date)
            time_range_milliseconds = end_timestamp - start_timestamp

            # 지정된 시간 간격 내에서 몇 개의 간격이 필요한지 계산
            limit = int(time_range_milliseconds / (unit_milliseconds * interval_amount))

        if isinstance(limit, int) and MAX_ALLOWED_LIMIT < limit:
            raise ValueError(
                f"limit 값은 {MAX_ALLOWED_LIMIT:,}을 초과할 수 없음. >> 현재 {limit:,}"
            )

        return True

    # Ticker별 현재가격 수신
    async def fetch_ticker_price(
        self, symbol: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """
        1. 기능 : 지정 Ticker 또는 전체 Ticker의 현재가격 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.) 또는 미입력(default값 : None)
        """
        params = {"symbol": symbol.upper()} if symbol else None
        result = await self.__retrieve_api_data("ticker/price", params=params)
        return utils._none_or(result)

    # Ticker별 실시간 매수/매도 주문정보 수신
    async def fetch_book_ticker(
        self, symbol: Optional[str] = None
    ) -> Optional[List[Dict[str, str]]]:
        """
        1. 기능 : 지정 Ticker 또는 전체 Ticker의 실시간 매수/매도 주문정보 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.) 또는 미입력(default값 : None)
        """
        params = {"symbol": symbol.upper()} if symbol else None
        result = await self.__retrieve_api_data("ticker/bookTicker", params=params)
        return utils._none_or(result)

    # Ticker별 24시간 거래내역 수신
    async def fetch_24hr_ticker(
        self, symbol: Optional[str] = None
    ) -> Optional[List[Dict[str, Union[str, int, float]]]]:
        """
        1. 기능 : 지정 Ticker 또는 전체 Ticker의 24시간 거래내역을 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.) 또는 미입력(default값 : None)
        """
        params = {"symbol": symbol.upper()} if symbol else None
        result = await self.__retrieve_api_data("ticker/24hr", params=params)
        return utils._none_or(result)

    # Ticker별 limit 지정 OHLCV데이터 수신
    async def fetch_klines_limit(
        self, symbol: str, interval: str, limit: int = 1000
    ) -> Optional[List[List[Union[str, int]]]]:
        """
        1. 기능 : 지정 Ticker의 OHLCV값을 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) interval : BinanceAPIBase Class의 OHLCV_INTERVALS 속성값 참조
            3) limit : 수신하고자 하는 데이터의 양
        """
        # parameter 유효성 확인
        self.__validate_kline_params(limit=limit, interval=interval)

        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}
        result = await self.__retrieve_api_data("klines", params=params)
        return utils._none_or(result)

    # Ticker별 date 지정 OHLCV데이터 수신 (limit으로도 활용 가능)
    async def fetch_klines_date(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[Union[str, datetime.datetime]] = None,
        end_date: Optional[Union[str, datetime.datetime]] = None,
        limit: int = 1_000,
    ) -> Optional[List[List[Union[str, int]]]]:
        """
        1. 기능 : 지정 Ticker의 OHLCV값을 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) interval : BinanceAPIBase Class의 OHLCV_INTERVALS 속성값 참조
            3) limit : 수신하고자 하는 데이터의 양
        """
        limit = 1000  # 최대 수신 길이 1000
        ms_second = 1000

        # 날짜 매개변수 검증
        if not start_date and not end_date:
            raise ValueError("매개변수 start_date 또는 end_date 하나는 이상 필수 입력")

        # parameter 유효성 확인
        self.__validate_kline_params(
            interval=interval, start_date=start_date, end_date=end_date
        )

        # 초기 params 설정
        params = {"symbol": symbol.upper(), "interval": interval, "limit": limit}

        # 시작 및 종료 날짜가 제공된 경우 타임스탬프 변환 및 params 업데이트
        if start_date:
            params["startTime"] = utils._convert_to_timestamp_ms(start_date)
        if end_date:
            params["endTime"] = utils._convert_to_timestamp_ms(end_date)

        # 데이터 요청 및 반환
        result = await self.__retrieve_api_data("klines", params=params)
        return utils._none_or(result)

    # Ticker별 호가창 내용 수신
    async def fetch_order_book(
        self, symbol: str, limit: int = 100
    ) -> Optional[Dict[str, Union[List[List[str]], int]]]:
        """
        1. 기능 : 지정 Ticker의 호가정보 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) limit : 수신하고자 하는 데이터의 양
        """
        params = {"symbol": symbol.upper(), "limit": limit}
        result = await self.__retrieve_api_data("depth", params=params)
        return utils._none_or(result)

    # Tickers별 최근 거래내역 상세
    async def fetch_recent_trades(
        self, symbol: str, limit: int = 100
    ) -> Optional[List[Dict[str, Union[str, int, bool]]]]:
        """
        1. 기능 : 지정 Ticker의 최근 거래내역 상세정보 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) limit : 수신하고자 하는 데이터의 양
        """
        params = {"symbol": symbol.upper(), "limit": limit}
        result = await self.__retrieve_api_data("trades", params=params)
        return utils._none_or(result)

    # Ticker별 최근 거래내역 집계 상세 / fetch_recent_trades와 유사함.
    async def fetch_agg_trades(
        self, symbol: str, limit: int = 100
    ) -> Optional[List[Dict[str, Union[str, int, bool]]]]:
        """
        1. 기능 : 지정 Ticker의 최근 거래내역 집계 상세정보를 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) limit : 수신하고자 하는 데이터의 양
        """
        params = {"symbol": symbol.upper(), "limit": limit}
        result = await self.__retrieve_api_data("aggTrades", params=params)
        return utils._none_or(result)

    # Ticker별 평균가격 수신
    async def fetch_avg_price(
        self, symbol: str
    ) -> Optional[Dict[str, Union[str, int]]]:
        """
        1. 기능 : 지정 Ticker별 평균가격 수신 및 반환한다.
        2. 매개변수 : 해당없음.
        """
        params = {"symbol": symbol.upper()}
        result = await self.__retrieve_api_data("avgPrice", params=params)
        return utils._none_or(result)

    # Ticker 개별 현재가 수신
    async def fetch_symbol_price(self, symbol: str) -> Optional[Dict[str, str]]:
        """
        1. 기능 : 지정 Ticker별 현재가를 수신 및 반환한다.
        2. 매개변수 : 해당없음.
        """
        params = {"symbol": symbol.upper()}
        result = await self.__retrieve_api_data("ticker/price", params=params)
        return utils._none_or(result)


class SpotMarket(MarketDataManager):
    BASE_URL = "https://api.binance.com/api/v3/"

    def __init__(self):
        super().__init__(base_url=self.BASE_URL)

    # spot 거래소의 메타데이터 수신
    async def fetch_exchange_info(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        1. 기능 : spot type별 거래소 메타데이터 정보를 수신 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (asset 타입 입력안됨.)
        """
        if symbol:
            symbol = symbol.upper()
            query_params = {"symbol": symbol}
            # 맹글링(Name Mangling)을 우회하기 위하여 "self._ + 부모클라스 + 비공개 함수"를 사용하였음.
            exchange_data = await self._MarketDataManager__retrieve_api_data(  # type: ignore
                "exchangeInfo", params=query_params
            )  # type: ignore
            return exchange_data if exchange_data is not None else {}

        # 전체 거래소 정보를 가져오는 경우
        # 맹글링(Name Mangling)을 우회하기 위하여 "self._ + 부모클라스 + 비공개 함수"를 사용하였음.
        exchange_data = await self._MarketDataManager__retrieve_api_data("exchangeInfo")  # type: ignore
        return exchange_data if exchange_data is not None else {}


class FuturesMarket(MarketDataManager):
    BASE_URL = "https://fapi.binance.com/fapi/v1/"

    def __init__(self):
        super().__init__(base_url=self.BASE_URL)

    # Futures 거래소의 메타데이터 수신
    async def fetch_exchange_info(self) -> Dict[str, Any]:
        """
        1. 기능 : futures type별 거래소 메타데이터 정보를 수신 및 반환한다.
        2. 매개변수 : 해당없음.
            >> symbol값 별도 입력을 이용한 선택 조회 안됨.
        """
        # 맹글링(Name Mangling)을 우회하기 위하여 "self._ + 부모클라스 + 비공개 함수"를 사용하였음.
        exchange_data = await self._MarketDataManager__retrieve_api_data("exchangeInfo")  # type: ignore
        return exchange_data if exchange_data is not None else {}


# 비동기 실행
if __name__ == "__main__":
    from pprint import pprint

    # 예시 실행
    # async def main():
    spot_obj = SpotMarket()
    futures_obj = FuturesMarket()

    # SpotMarket 예시 호출
    spot_price = asyncio.run(spot_obj.fetch_ticker_price())
    print(f"TEST 1. Spot Ticker Price : {spot_price}")

    # FuturesMarket 예시 호출
    futures_price = asyncio.run(futures_obj.fetch_ticker_price())
    print(f"TEST 2. Futures Ticker Price : {futures_price}")

    # 추가된 fetch_avg_price 호출 예시
    avg_price = asyncio.run(spot_obj.fetch_avg_price("BTCUSDT"))
    print(f"TEST 3. Average Price for BTCUSDT : {avg_price}")

    # 추가된 fetch_symbol_ticker_price 호출 예시
    symbol_price = asyncio.run(spot_obj.fetch_symbol_price("BTCUSDT"))
    print(f"TEST 4. Symbol Ticker Price for BTCUSDT : {symbol_price}")

    symbol_exchange = asyncio.run(spot_obj.fetch_exchange_info())
    print(f"TEST 5. Symbol Ticker Exchange : {symbol_exchange}")

    # asyncio.run(main())
