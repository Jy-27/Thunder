import requests
import datetime
from typing import Final, Dict, Any, Optional, List, Union, TypeVar, cast
from abc import ABC, abstractmethod


class BaseAPI(ABC):
    """
    Binance에서 API KEY없이 조회가능한 데이터를
    수신 및 반환한다.
    """
    BASE_URL: str

    def __init__(self, base_url: str):
        BASE_URL: str = base_url

    def _retrieve_api_data(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        공동 API 호출 메서드 (비공개)

        Args:
            endpoint (str): Base URL 제외 나머지 주소
            params (Optional[Dict[str, Any]], optional): 각 함수별 별도 지정 (선택사항)

        Returns:
            Any: API 응답 JSON
        """
        url = self.BASE_URL + endpoint
        response = requests.get(url, params=params, timeout=10)

        # HTTP 오류 발생 시 예외 발생
        response.raise_for_status()

        return response.json()

    # Ticker별 현재가격 조회
    def fetch_ticker_price(
        self, symbol: Optional[str]
    ) -> Union[List[Dict[str, Union[int, str]]], Dict[str, Union[int, str]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 최신 가격을 조회 및 반환한다.

        Args:
            symbol (Optional[str], optional):
                - 'BTCUSDT'
                - None

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """
        params = {"symbol": symbol} if symbol else None
        return self._retrieve_api_data("ticker/price", params=params)

    # Ticker별 실시간 매수/매도 주문정보 조회
    def fetch_book_tickers(
        self, symbol: Optional[str] = None
    ) -> Union[List[Dict[str, Union[int, str]]], Dict[str, Union[int, str]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 최고 매수/매도 가격 및 수량 정보를 조회 및 반환한다.

        Args:
            symbols (Optional[Union[List[str],str]], optional):
                - 'BTCUSDT'
                - None

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """

        params = {"symbol": symbol} if symbol else None
        return self._retrieve_api_data("ticker/bookTicker", params=params)

    # Ticker별 24시간 거래내역 조회
    def fetch_24hr_ticker(
        self, symbol: Optional[str] = None
    ) -> Optional[List[Dict[str, Union[str, int, float]]]]:
        """
        지정 symbol 또는 전체(symbol:None) symbol에 대한 24시간 가격 변동 통계정보를 조회 및 반환한다.

        Args:
            symbol (Optional[str], optional):
                - 'BTCUSDT'
                - None

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """
        params = {"symbol": symbol} if symbol else None
        return self._retrieve_api_data("ticker/24hr", params=params)

    # Ticker별 limit 지정 OHLCV데이터 조회
    def fetch_klines_limit(
        self, symbol: str, interval: str, limit: int
    ) -> List[List[Union[int, str]]]:
        """
        조회할 데이터 개수를 지정하여 캔들 스틱 데이터(OHLCV)를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            interval (str): '3m' (이 외 Binance 지원 interval 참조)
            limit (int): 조회 데이터 개수 (max 1,000)

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """

        params = {"symbol": symbol, "interval": interval, "limit": limit}
        return self._retrieve_api_data("klines", params=params)

    # Ticker별 date 지정 OHLCV데이터 조회 (limit으로도 활용 가능)
    def fetch_klines_date(
        self,
        symbol: str,
        interval: str,
        start_ms_timestamp: int,
        end_ms_timestamp: int,
    ) -> List[List[Union[int, str]]]:
        """
        조회할 데이터의 기간을 지정하여 캔들 스틱 데이터(OHLCV)를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            interval (str): '3m'
            start_ms_timestamp (int): 밀리초 타임스템프
            end_ms_timestamp (int): 밀리초 타임스템프

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """
        params = {
            "symbol": symbol,
            "startTime": start_ms_timestamp,
            "endTime": end_ms_timestamp,
            "interval": interval,
        }

        # 데이터 요청 및 반환
        return self._retrieve_api_data("klines", params=params)

    # Ticker별 호가창 내용 조회
    def fetch_order_book(
        self, symbol: str, limit: int
    ) -> Optional[Dict[str, Union[List[List[str]], int]]]:
        """
        지정 심볼의 호가 데이터(주문서)를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            limit (int, optional): 조회하고자 하는 데이터의 양 (max 100)

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """

        params = {"symbol": symbol, "limit": limit}
        return self._retrieve_api_data("depth", params=params)

    # Tickers별 최근 거래내역 상세
    def fetch_recent_trades(self, symbol: str, limit: int) -> List[Dict[str, Any]]:
        """
        지정 symbol의 최근 거래 목록을 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            limit (int, optional): 조회하고자 하는 데이터의 양 (max 100)

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """
        params = {"symbol": symbol, "limit": limit}
        return self._retrieve_api_data("trades", params=params)

    # Ticker별 최근 거래내역 집계 상세 / fetch_recent_trades와 유사함.
    def fetch_agg_trades(self, symbol: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        지정 synbols의 최근 거래내역 집계(상세정보 취합) 정보를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            limit (int, optional): 조회 데이터 개수 (max 100)

        Returns:
            https://docs.binance.us 에서 endpoint 검색 참조
        """
        params = {"symbol": symbol, "limit": limit}
        return self._retrieve_api_data("aggTrades", params=params)

    def fetch_server_time(self) -> Dict[str, int]:
        """
        서버 시간 정보를 조회 및 반환한다.

        Returns:
            Dict[str, int]: {'serverTime': 1739235404909}
        """
        return self._retrieve_api_data("time")

    def ping_binance(self):
        """
        서버 상태를 확인한다.

        Returns:
            dict: {} 로 반환시 정상, 그 외 신호는 비정상을 의미함.
        """
        return self._retrieve_api_data("ping")

    @abstractmethod
    def fetch_exchange_info(self):
        """
        추상 메소드, 거래소 정보 조회
        """
        pass
