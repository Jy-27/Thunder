from TickerDataFetcher import SpotTickers, FuturesTickers
from DataHandler import SpotHandler, FuturesHandler
from typing import Dict, List, Optional, Union, Tuple, Final, cast
from pprint import pprint
from collections import defaultdict
from MarketDataFetcher import SpotAPI, FuturesAPI

import BinanceTradeClient as my_client
import asyncio
import utils
import datetime


class DataControlManager:
    def __init__(
        self, ticker_instance, handler_instance, client_instance, market_instance
    ):
        self.tickers_data = None

        self.market_type: str = self.__class__.__name__.split("Data")[0]

        # TESTER
        self.interval_map: Dict = {}
        # TESTER
        self.KLINE_INTERVALS: Final[List] = [
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
            "1w",
            "1M",
        ]
        self.kline_data: defaultdict[str, defaultdict[str, dict]] = defaultdict(
            lambda: defaultdict(dict)
        )
        # anlysis 함수 현재 데이터 유형 확인
        self.websocket_type: dict = {}

        # instance init 전달
        self.ticker_instance = ticker_instance
        self.handler_instance = handler_instance
        self.client_instance = client_instance
        self.market_instance = market_instance

        # ticker 정보 저장 및 공유
        self.active_tickers: List = []

        self.account_balance_raw: Dict = {}
        self.account_balance_summary: Dict = {}
        self.account_active_symbols: List = []

    # Ticker 수집에 필요한 정보를 수신
    async def _collect_filtered_ticker_data(self) -> Tuple:
        """
        1. 기능 : 기준값에 충족하는 ticker정보를 수신.
        2. 매개변수 : 해당없음.
        """
        comparison = "above"  # above : 이상, below : 이하
        absolute = True  # True : 비율 절대값, False : 비율 실제값
        value = 150_000_000  # 거래대금 : 단위 USD
        target_percent = 5  # 변동 비율폭 : 단위 %이며, 음수 가능
        quote_type = "usdt"  # 쌍거래 거래화폐

        above_value_tickers = await self.ticker_instance.fetch_tickers_above_value(
            target_value=value, comparison=comparison
        )
        above_percent_tickers = await self.ticker_instance.fetch_tickers_above_change(
            target_percent=target_percent, comparison=comparison, absolute=absolute
        )
        quote_usdt_tickers = await self.ticker_instance.fetch_asset_tickers(
            quote=quote_type
        )

        # result = {'above_value_tickers':above_value_tickers,
        #           'above_percent_tickers':above_percent_tickers,
        #           'quote_usdt_tickers':quote_usdt_tickers}

        return above_value_tickers, above_percent_tickers, quote_usdt_tickers

    # Ticker 필터하여 리스트로 반환
    async def fetch_essential_tickers(self) -> List:
        """
        1. 기능 : 기준값에 충족하는 tickers를 반환.
        2. 매개변수 : 해당없음.
        """
        mandatory_tickers = ["BTCUSDT", "XRPUSDT", "ETHUSDT"]
        filtered_ticker_data = await self._collect_filtered_ticker_data()
        # 공통 필터링된 티커 요소를 리스트로 반환받음
        common_filtered_tickers = utils._find_common_elements(*filtered_ticker_data)

        # 필수 티커와 공통 필터링된 티커를 합쳐 중복 제거
        final_ticker_list = list(
            set(
                mandatory_tickers
                + common_filtered_tickers
                + self.account_active_symbols
            )
        )

        return final_ticker_list

    # Ticker update 무한루프
    async def ticker_update_loop(self):
        """
        1. 기능 : Tickers를 주기적으로 update한다.
        2. 매개변수 : 해당없음.
        """
        while True:
            await self.handler_instance.pause_and_resume_loop()
            try:
                # 필수 티커를 업데이트
                self.active_tickers = await self.fetch_essential_tickers()
                # 간격 대기 함수 호출 (예: 4시간 간격)

            except Exception as e:
                # 예외 발생 시 로깅 및 오류 메시지 출력
                print(f"Error in ticker_update_loop: {e}")
            # 적절한 대기 시간 추가 (예: 짧은 대기)
            await utils._wait_until_next_interval(time_unit="minute", interval=2)

    # 계좌정보 업데이트
    def fetch_active_positions(self):
        """
        1. 기능 : 활성 포지션을 요약하여 포지션 요약 정보와 활성 심볼 목록을 생성.
        2. 매개변수 : 해당없음.
        """
        # 계좌 잔고 데이터 가져오기
        self.account_balance_raw = self.client_instance.fetch_account_balance()

        # 시장 유형에 따라 주요 필드명 설정
        primary_field_name = {"Futures": "positions", "Spot": "balances"}.get(
            self.market_type
        )
        amount_field_name = {"Futures": "positionAmt", "Spot": "free"}.get(
            self.market_type
        )
        symbol_field_name = {"Futures": "symbol", "Spot": "asset"}.get(self.market_type)

        # 주요 데이터 필드가 존재하지 않을 경우 함수 종료
        raw_data = self.account_balance_raw.get(primary_field_name, [])
        if not raw_data:
            return

        # 포지션 요약 정보와 활성 심볼 목록 초기화
        self.account_balance_summary = {}
        self.account_active_symbols = []

        # 활성 포지션 필터링 및 요약 생성
        for position in raw_data:
            converted_data = utils._collections_to_literal([position])[0]
            print(converted_data)

            # 포지션 수량이 0이 아닌 경우 활성 포지션으로 간주
            if abs(converted_data.get(amount_field_name, 0)) > 0:
                symbol = converted_data.get(symbol_field_name)
                self.account_active_symbols.append(symbol)
                self.account_balance_summary[symbol] = converted_data

    # stream websocket 연결
    async def connect_stream_loop(self, ws_type: str):
        """
        1. 기능 : websocket stream 데이터 수신
        2. 매개변수
            1) ws_type : ENDPOINT 속성 참조
        """
        self.websocket_type["stream"] = ws_type
        await utils._wait_until_exact_time(time_unit="minute")
        print(f"WebSocket Loop 진입 - {utils._get_time_component()}")

        while True:
            # 중단 이벤트 또는 초기 Ticker 데이터 비어있음에 대한 대응
            if self.handler_instance.stop_event.is_set():
                print(f"Loop 중단 - 중단 이벤트 감지됨 {utils._get_time_component()}")
                break  # stop_event가 설정된 경우 루프 종료

            if not self.active_tickers:
                print(
                    f"WebSocket 접속 대기 - 활성 티커가 없음 {utils._get_time_component()}"
                )
                # 빈 데이터 발생 시 루프 재시도를 위해 5초 대기
                await utils._wait_time_sleep(time_unit="second", duration=5)
                continue

            try:
                time_now = utils._get_time_component()
                print(f"WebSocket 접속 시도 - {time_now}")
                # WebSocket 데이터 수신 무한 루프 시작
                await self.handler_instance.connect_stream(
                    symbols=self.active_tickers, stream_type=ws_type
                )

                print(f"tickers update complete - {utils._get_time_component()}")
                # 시스템 안정성을 위한 5초 대기
                await utils._wait_time_sleep(time_unit="second", duration=5)
            except Exception as e:
                print(f"WebSocket 연결 오류 발생: {e} - {utils._get_time_component()}")
                # 오류 발생 시 안전하게 대기 후 재시도
                await utils._wait_time_sleep(time_unit="second", duration=5)

    # kline websocket 연결
    async def connect_kline_loop(self, ws_intervals: Union[str, list]):
        """
        1. 기능 : websocket kline 데이터 수신
        2. 매개변수
            1) ws_intervals : ENDPOINT 속성 참조
        """
        self.websocket_type["kline"] = ws_intervals
        # 정시(0초)에 WebSocket 연결을 시작하기 위한 대기 로직
        await utils._wait_until_exact_time(time_unit="minute")
        print(f"WebSocket Loop 진입 - {utils._get_time_component()}")

        while True:
            # 중단 이벤트 또는 초기 Ticker 데이터 비어있음에 대한 대응
            if self.handler_instance.stop_event.is_set():
                print(f"Loop 중단 - 중단 이벤트 감지됨 {utils._get_time_component()}")
                break  # stop_event가 설정된 경우 루프 종료

            if not self.active_tickers:
                print(
                    f"WebSocket 접속 대기 - 활성 티커가 없음 {utils._get_time_component()}"
                )
                # 빈 데이터 발생 시 루프 재시도를 위해 5초 대기
                await utils._wait_time_sleep(time_unit="second", duration=5)
                continue

            try:
                time_now = utils._get_time_component()
                print(f"WebSocket 접속 시도 - {time_now}")
                # WebSocket 데이터 수신 무한 루프 시작
                await self.handler_instance.connect_kline_limit(
                    symbols=self.active_tickers, intervals=ws_intervals
                )

                print(f"tickers update complete - {utils._get_time_component()}")
                # 시스템 안정성을 위한 5초 대기
                await utils._wait_time_sleep(time_unit="second", duration=5)
            except Exception as e:
                print(f"WebSocket 연결 오류 발생: {e} - {utils._get_time_component()}")
                # 오류 발생 시 안전하게 대기 후 재시도
                await utils._wait_time_sleep(time_unit="second", duration=5)

    # hour 또는 minute별 수신해야할 interval을 리스트화 정렬
    def _generate_time_intervals(self):
        time_intervals: Dict[str, Dict] = {
            "minutes": {},  # 분 단위 타임라인
            "hours": {},  # 시간 단위 타임라인
        }

        # 각 분 초기화
        for minute in range(60):
            time_intervals["minutes"][minute] = []

        # 각 시간 초기화
        for hour in range(24):
            time_intervals["hours"][hour] = []

        # 분 단위 간격 설정
        minute_intervals = {"1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30}

        # 시간 단위 간격 설정
        hour_intervals = {"1h": 1, "2h": 2, "4h": 4, "6h": 6, "8h": 8, "12h": 12}

        for interval in self.KLINE_INTERVALS:
            if str(interval).endswith("m"):
                for min in range(0, 60, minute_intervals.get(interval, 0)):
                    time_intervals["minutes"][min].append(interval)
            elif str(interval).endswith("h"):
                for hr in range(0, 24, hour_intervals.get(interval, 0)):
                    time_intervals["hours"][hr].append(interval)
            else:
                time_intervals["hours"][0].append(interval)

        # 비어 있는 key 제거
        time_intervals["minutes"] = {
            minute: intervals
            for minute, intervals in time_intervals["minutes"].items()
            if intervals
        }
        time_intervals["hours"] = {
            hour: intervals
            for hour, intervals in time_intervals["hours"].items()
            if intervals
        }
        return time_intervals

    # klline 매개변수에 들어갈 유효 limit
    def _get_valid_kline_limit(self, interval: str) -> Dict:
        # 상수 설정
        VALID_INTERVAL_UNITS = ["m", "h"]
        MINUTES_PER_DAY = 1_440
        MAX_KLINE_LIMIT = 1_000

        # interval 유효성 검사
        interval_unit = interval[-1]
        interval_value = int(interval[:-1])

        if interval_unit not in VALID_INTERVAL_UNITS:
            raise ValueError("interval은 분(m) 또는 시간(h) 단위여야 합니다.")
        if interval not in self.KLINE_INTERVALS:
            raise ValueError(f"유효하지 않은 interval입니다: {interval}")

        # 분 단위로 interval 변환
        interval_minutes = interval_value * {"m": 1, "h": 60}[interval_unit]

        # 최대 수집 가능 일 수 및 제한 계산
        intervals_per_day = MINUTES_PER_DAY / interval_minutes
        max_days = int(MAX_KLINE_LIMIT / intervals_per_day)
        max_limit = int(intervals_per_day * max_days)

        # 결과 반환
        return {"day": max_days, "limit": max_limit}

    async def fetch_historical_kline_hour_min(
        self,
        symbol: str,
        interval: str,
        start_date: Optional[Union[str, datetime.datetime]] = None,
        end_date: Optional[Union[str, datetime.datetime]] = None,
    ):
        active_limit_info = self._get_valid_kline_limit(interval=interval)
        if not start_date and end_date:
            return await self.market_instance.fetch_klines_limit(
                symbol=symbol, interval=interval
            )
        elif start_date and not end_date:
            return await self.market_instance.fetch_kllines_date(
                symbol=symbol, interval=interval, start_date=start_date
            )

        elif start_date and end_date:
            historicla_kline_data = []
            end_timestamp = utils._convert_to_timestamp_ms(date=end_date)

            while True:
                data = await self.market_instance.fetch_klines_date(
                    symbol=symbol, interval=interval, start_date=start_date
                )
                start_date = utils._convert_to_datetime(
                    date=start_date
                ) + datetime.timedelta(days=active_limit_info.get("day", 0))
                historicla_kline_data.extend(data)
                if data[-1][6] > end_timestamp:
                    break
            return historicla_kline_data

    # kline 데이터 interval map별 수집
    async def collect_kline_by_interval_loop(self):

        interval_map = self._generate_time_intervals()
        time_units = ["hours", "minutes"]
        KLINE_LMIT: Final[int] = 1_000

        while True:
            await utils._wait_until_exact_time(time_unit="minute")
            currunt_time_now = cast(datetime.datetime, utils._get_time_component())
            current_time_hour = cast(int, currunt_time_now.hour)
            current_time_minute = cast(int, currunt_time_now.minute)

            if current_time_minute in interval_map.get("minutes"):
                for time_unit in time_units:
                    for times, intervals in interval_map.get(time_unit).items():
                        if (
                            time_unit == time_units[0]
                            and current_time_minute == 0
                            and times == current_time_hour
                        ):
                            for ticker in self.active_tickers:
                                for interval in intervals:
                                    self.kline_data[ticker][interval] = (
                                        await self.market_instance.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=KLINE_LMIT,
                                        )
                                    )
                        if time_unit == time_units[1] and current_time_minute == times:
                            for ticker in self.active_tickers:
                                for interval in intervals:
                                    self.kline_data[ticker][interval] = (
                                        await self.market_instance.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=KLINE_LMIT,
                                        )
                                    )
        return self.kline_data

    # test zone
    async def test_princ(self):
        while True:
            data = await self.handler_instance.asyncio_queue.get()
            print(data)

    # Anlysis 만들것

    # sync_kline_data <<생성할 것.


class SpotDataControl(DataControlManager):
    def __init__(self):
        super().__init__(
            SpotTickers(), SpotHandler(), my_client.SpotOrderManager(), SpotAPI()
        )


class FuturesDataControl(DataControlManager):
    def __init__(self):
        super().__init__(
            FuturesTickers(),
            FuturesHandler(),
            my_client.FuturesOrderManager(),
            FuturesAPI(),
        )


if __name__ == "__main__":
    obj = FuturesDataControl()
    data = asyncio.run(obj.collect_kline_by_interval_loop())
    print(data)
