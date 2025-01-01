from TickerDataFetcher import SpotTickers, FuturesTickers
from DataHandler import SpotHandler, FuturesHandler
from typing import (
    Dict,
    List,
    Optional,
    Union,
    Tuple,
    Final,
    cast,
    Any,
    DefaultDict,
    cast,
)
from pprint import pprint
from collections import defaultdict
from MarketDataFetcher import SpotMarket, FuturesMarket
from Analysis import AnalysisManager

# from DataProcess import TradeStopper, OrderConstraint
from DataProcess import OrderConstraint, DataInfo

import BinanceTradeClient as my_client
import asyncio
import utils
import datetime
import json


class TradeManager:
    def __init__(
        self,
        ticker_instance,
        handler_instance,
        client_instance,
        market_instance,
    ):

        self.tickers_data = None

        self.lock = asyncio.Lock()

        self.market_type: str = self.__class__.__name__.split("Data")[0]

        # TESTER
        self.interval_map: Dict = {}
        # TESTER
        self.KLINE_INTERVALS: Final[List] = [
            # "1m",
            # "3m",
            "5m",
            "15m",
            # "30m",
            # "1h",
            # "2h",
            # "4h",
            # "6h",
            # "8h",
            # "12h",
            # "1d",
            # "3d",
            # "1w",
            # "1M",
        ]
        self.kline_data: defaultdict[str, defaultdict[str, List[Union[str, int]]]] = (
            defaultdict(lambda: defaultdict(list))
        )

        # anlysis 함수 현재 데이터 유형 확인
        self.websocket_type: dict = {}

        # self.kline_data_update_flag = False
        # 수집할 kline_data의 기간을 지정한다.
        # 해당 값을 활용하여 수신된 데이터의 길이를 비교하여 유효성을 검토한다.
        self.interval_days: Optional[int] = None

        # instance init 전달
        self.ticker_instance = ticker_instance
        self.handler_instance = handler_instance  # asyncio._queue << 속성 여기에 있음.
        self.client_instance = client_instance
        self.market_instance = market_instance
        self.analysis_instance = AnalysisManager(intervals=self.KLINE_INTERVALS)
        # self.process_instance = TradeStopper(profit_ratio=0.015, risk_ratio=0.85)
        self.constraint_instance = OrderConstraint()

        self.signal_data: Dict[str, Dict[str, Union[int, float]]] = {}

        # ticker 정보 저장 및 공유
        # 검토 선정된 tickers 리스트
        self.active_tickers: List = []

        # 거래중과 관련된 정보
        self.account_balance_raw: Dict = {}
        self.account_balance_summary: Dict = {}
        self.account_active_symbols: List = []

        # websocket 수신데이터의 가장 마지막값을 저장한다. (kline과 결합을 위함.)
        self.final_message_received: DefaultDict[
            str, DefaultDict[str, List[List[Any]]]
        ] = defaultdict(lambda: defaultdict())

        self.account_balance_summary = {}
        self.account_active_symbols = []

    # 오버라이딩
    async def close_position(self, symbol: str, market_price: float): ...
    async def submit_open_order_signal(
        self, symbol: str, position: int, leverage: int
    ): ...
    async def submit_close_order_signal(self, symbol: str): ...

    # Ticker 수집에 필요한 정보를 수신
    async def _collect_filtered_ticker_data(self) -> Tuple:
        """
        1. 기능 : 기준값에 충족하는 ticker정보를 수신.
        2. 매개변수 : 해당없음.
        """
        comparison = "above"  # above : 이상, below : 이하
        absolute = True  # True : 비율 절대값, False : 비율 실제값
        value = 350_000_000  # 거래대금 : 단위 USD
        target_percent = 0.03  # 변동 비율폭 : 음수 가능
        quote_type = "usdt"  # 쌍거래 거래화폐

        above_value_tickers = await self.ticker_instance.get_tickers_above_value(
            target_value=value, comparison=comparison
        )
        above_percent_tickers = await self.ticker_instance.get_tickers_above_change(
            target_percent=target_percent, comparison=comparison, absolute=absolute
        )
        quote_usdt_tickers = await self.ticker_instance.get_asset_tickers(
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

        mandatory_tickers = ["BTCUSDT", "XRPUSDT", "ETHUSDT", "TRXUSDT"]
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
            await self.handler_instance.generator_control_signal()
            try:
                # 필수 티커를 업데이트
                self.active_tickers = await self.fetch_essential_tickers()

                print(
                    f"tickers - {len(self.active_tickers)}종 update! {datetime.datetime.now()}"
                )
                # 간격 대기 함수 호출 (예: 4시간 간격)

                # ticker update완료시 신규 kline데이터 갱신함.
                async with self.lock:
                    self.kline_data.clear()
                # ticker 초기화시 전체 kline을 업데이트 한다.abs
                await self.update_all_klines()
                # self.kline_data_update_flag = True

            except Exception as e:
                # 예외 발생 시 로깅 및 오류 메시지 출력
                print(f"Error in ticker_update_loop: {e}")
            # 적절한 대기 시간 추가 (예: 짧은 대기)
            # interval 지정값 기준 시계 시간을 의미.
            await utils._wait_until_next_interval(time_unit="minute", interval=10)

    # 계좌정보 업데이트
    async def fetch_active_positions(self):
        """
        1. 기능 : 활성 포지션을 요약하여 포지션 요약 정보와 활성 심볼 목록을 생성.
        2. 매개변수 : 해당없음.
        """
        # 계좌 잔고 데이터 가져오기
        self.account_balance_raw = await self.client_instance.fetch_account_balance()

        # 시장 유형에 따라 주요 필드명 설정
        primary_field_name = {"FuturesTrade": "positions", "SpotTrade": "balances"}.get(
            self.market_type
        )
        amount_field_name = {"FuturesTrade": "positionAmt", "SpotTrade": "free"}.get(
            self.market_type
        )
        symbol_field_name = {"FuturesTrade": "symbol", "SpotTrade": "asset"}.get(
            self.market_type
        )

        # # 주요 데이터 필드가 존재하지 않을 경우 함수 종료
        raw_data = self.account_balance_raw.get(primary_field_name, [])

        # DEBUG
        # print(self.market_type)
        # print(raw_data)
        # if not raw_data:
        #     return

        # 포지션 요약 정보와 활성 심볼 목록 초기화
        self.account_balance_summary = {}
        self.account_active_symbols = []

        # 활성 포지션 필터링 및 요약 생성
        for position in raw_data:
            converted_data = utils._collections_to_literal([position])[0]
            # print(converted_data)

            # 포지션 수량이 0이 아닌 경우 활성 포지션으로 간주
            if abs(converted_data.get(amount_field_name, 0)) > 0:
                symbol = converted_data.get(symbol_field_name)
                self.account_active_symbols.append(symbol)
                self.account_balance_summary[symbol] = converted_data
        return self.account_balance_summary

    # stream websocket 연결
    async def connect_stream_loop(self, ws_type: str):
        """
        1. 기능 : websocket stream 데이터 수신
        2. 매개변수
            1) ws_type : ENDPOINT 속성 참조
        """
        self.websocket_type["stream"] = ws_type
        await utils._wait_until_exact_time(time_unit="minute")
        await utils._wait_time_sleep(time_unit="minute", duration=1)
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
            1) ws_intervals : KLINE_INTERVALS 속성 참조
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

                # debug
                # print(len(self.active_tickers))

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

    # websocket 수신 데이터를 속성값에 저장한다.
    async def update_received_data_loop(self) -> Dict[str, Dict[str, Union[str, int]]]:
        while True:
            # print(f"queue size - {self.handler_instance.asyncio_queue.qsize()}")
            while not self.handler_instance.asyncio_queue.empty():
                received_massage = await self.handler_instance.asyncio_queue.get()
                if isinstance(received_massage, dict) and received_massage:
                    k_data = received_massage.get("k")  # 중간 변수로 저장
                    if isinstance(k_data, dict) and k_data:
                        symbol = received_massage.get("s", None)
                        price = k_data.get("c", None)
                        interval = k_data.get("i", None)

                        if (
                            symbol is not None
                            or price is not None
                            or interval is not None
                        ):
                            price = float(price)
                            # 해당코인 소지여부를 검토하고 손절가극 계산하여 조건 성립시 현재가 매각처리한다.

                            # if symbol in self.process_instance.trading_data.keys():
                            #     is_close_signal = (
                            #         self.process_instance.get_trading_stop_signal(
                            #             symbol=symbol, current_price=price
                            #         )
                            #     )
                            #     if is_close_signal:
                            #         await self.submit_close_order_signal(symbol=symbol)
                            #         self.process_instance.remove_trading_data(
                            #             symbol=symbol
                            #         )
                            self.final_message_received[symbol][
                                interval
                            ] = received_massage
            await utils._wait_time_sleep(time_unit="second", duration=1)

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
        VALID_INTERVAL_UNITS = ["m", "h", "d", "w", "M"]
        MINUTES_PER_DAY = 1_440
        MAX_KLINE_LIMIT = 1_000

        # interval 유효성 검사
        interval_unit = interval[-1]
        interval_value = int(interval[:-1])

        if interval not in self.KLINE_INTERVALS:
            raise ValueError(f"유효하지 않은 interval입니다: {interval}")

        # 분 단위로 interval 변환
        interval_minutes = interval_value * {"m": 1, "h": 60, "d": 1440}[interval_unit]

        # 최대 수집 가능 일 수 및 제한 계산
        intervals_per_day = MINUTES_PER_DAY / interval_minutes
        max_days = int(MAX_KLINE_LIMIT / intervals_per_day)
        max_limit = int(intervals_per_day * max_days)

        # 결과 반환
        return (max_days, max_limit)

    # kline 매개변수에 들어가는 limit을 day기준으로 개수를 계산한다.
    def _get_kline_limit_by_days(self, interval: str, days: int) -> int:
        """
        1. 기능 : kline 매개변수에 들어갈 day 기간 만큼 interval의 limit값을 구한다.
        2. 매개변수
            1) interval : KLINE_INTERVALS 속성 참조
            2) day : 기간을 정한다.
        """
        day, limit = self._get_valid_kline_limit(interval=interval)
        if day == 0:
            return 1000
        max_klines_per_day = (limit / day) * days

        if max_klines_per_day > 1_000:
            print(
                f"The calculated limit exceeds the maximum allowed value: {max_klines_per_day}. Limiting to 1,000."
            )
            return 1_000

        return int(max_klines_per_day)

    # kline전체를 days기준 범위로 업데이트한다.
    async def update_all_klines(self, days: int = 1):
        """
        1. 기능 : 현재 선택된 ticker에 대한 모든 interval kline을 수신한다.
        2. 매개변수
            1) max_recordes : max 1_000, 조회할 데이터의 길이를 정한다.
        """
        # 활성화된 티커가 준비될 때까지 대기
        while not self.active_tickers:
            await asyncio.sleep(
                2
            )  # utils._wait_time_sleep을 asyncio.sleep으로 대체하여 비동기 방식으로 대기

        # 모든 활성화된 티커에 대해 데이터를 수집 및 업데이트
        for ticker in self.active_tickers:
            for interval in self.KLINE_INTERVALS:
                if interval.endswith("d"):
                    limit_ = 30
                else:
                    limit_ = self._get_kline_limit_by_days(interval=interval, days=days)
                # Kline 데이터를 수집하고 self.kline_data에 업데이트
                self.kline_data[ticker][interval] = (
                    await self.market_instance.fetch_klines_limit(
                        symbol=ticker,
                        interval=interval,
                        limit=limit_,
                    )
                )
        # print(f"Kline 전체 update완료 - {datetime.datetime.now()}")

    # kline 데이터 interval map별 수집
    async def collect_kline_by_interval_loop(self, days: int = 2):

        # interval day기간을 속성에 저장 후 현재 로딩 데이터의 길이가 유효한지 검토하는 목적
        self.interval_days = days

        interval_map = self._generate_time_intervals()
        time_units = ["hours", "minutes"]
        KLINE_LMIT: Final[int] = 300

        while True:
            await utils._wait_until_exact_time(time_unit="minute")
            currunt_time_now = cast(datetime.datetime, utils._get_time_component())
            current_time_hour = cast(int, currunt_time_now.hour)
            current_time_minute = cast(int, currunt_time_now.minute)

            # self.kline_data_update_flag = False
            # print(self.kline_data_update_flag)
            # print(datetime.datetime.now())

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
                                    limit_ = self._get_kline_limit_by_days(
                                        interval=interval, days=days
                                    )
                                    self.kline_data[ticker][interval] = (
                                        await self.market_instance.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=limit_,
                                        )
                                    )
                        if time_unit == time_units[1] and current_time_minute == times:
                            for ticker in self.active_tickers:
                                for interval in intervals:
                                    limit_ = self._get_kline_limit_by_days(
                                        interval=interval, days=days
                                    )
                                    self.kline_data[ticker][interval] = (
                                        await self.market_instance.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=limit_,
                                        )
                                    )
            # self.kline_data_update_flag = True
            # print(self.kline_data_update_flag)
            # print(datetime.datetime.now())
        # return self.kline_data

    # WebSocket에서 수신한 kline 데이터를 OHLCV 형식으로 변환
    async def _transform_kline(
        self, raw_kline_data: dict
    ) -> List[Union[str, int, float]]:
        """
        WebSocket에서 수신한 kline 데이터를 OHLCV 형식으로 변환합니다.

        Args:
            raw_kline_data (dict): WebSocket에서 수신된 원시 kline 데이터

        Returns:
            List[Union[str, int, float]]: 변환된 kline 데이터 리스트 (OHLCV 형식)
        """
        kline_details = raw_kline_data.get("k", {})

        transformed_kline = [
            kline_details.get("t"),  # open_time
            float(kline_details.get("o", 0)),  # open_price
            float(kline_details.get("h", 0)),  # high_price
            float(kline_details.get("l", 0)),  # low_price
            float(kline_details.get("c", 0)),  # close_price
            float(kline_details.get("v", 0)),  # volume
            kline_details.get("T"),  # close_time
            float(kline_details.get("q", 0)),  # quote_asset_volume
            kline_details.get("n"),  # trade_count
            float(kline_details.get("V", 0)),  # taker_buy_base_volume
            float(kline_details.get("Q", 0)),  # taker_buy_quote_volume
            0,  # Placeholder (Optional)
        ]
        return transformed_kline

    # weboskcet data와 kline데이터를 결합한다.
    async def _merge_kline_data(self, kline_message: Dict[str, Union[str, int, dict]]):
        """
        1. 기능 : websocket data와 kline data를 하나로 결합한다.
        2. 매개변수
            1) kline_message : websocket kline실시간 수신 데이터
        """
        # isinstance를 하나로 묶으면 mypy에서 error발생함.
        if isinstance(kline_message, dict):
            k_data = kline_message.get("k", {})
            if isinstance(k_data, dict):
                interval = k_data.get("i", {})
                symbol = k_data.get("s")
        if not isinstance(kline_message, dict):
            raise ValueError(f"잘못된 값 입력됨")

        # 웹소켓으로 수신된 데이터를 변환
        transformed_kline = await self._transform_kline(kline_message)

        # 심볼 및 주기에 해당하는 데이터가 존재하는지 확인
        if isinstance(symbol, str) and isinstance(interval, str):
            if symbol in self.kline_data and interval in self.kline_data[symbol]:
                last_kline = self.kline_data[symbol][interval][-1]

                # 오픈 및 클로즈 타임스탬프 일치 여부 확인
                is_open_timestamp_match = int(transformed_kline[0]) == int(
                    last_kline[0]
                )
                is_close_timestamp_match = int(transformed_kline[6]) == int(
                    last_kline[6]
                )

                # 조건에 따라 마지막 Kline 업데이트 또는 새로운 Kline 추가
                if is_open_timestamp_match and is_close_timestamp_match:
                    self.kline_data[symbol][interval][-1] = transformed_kline
                else:
                    self.kline_data[symbol][interval].append(transformed_kline)
            else:
                # 새로운 심볼 및 주기 데이터 초기화
                self.kline_data[symbol][interval].append(transformed_kline)

    # websocket데이터와 kline데이터를 00초마다 병합함.
    async def merge_websocket_kline_data_loop(self):
        """
        1. 기능 : 실시간 Kline 데이터를 반복적으로 처리하는 함수
        2. 매개변수 : 해당없음.
        """
        await utils._wait_time_sleep(time_unit="minute", duration=2)

        while True:
            await utils._wait_until_exact_time(time_unit="second")
            await asyncio.sleep(4)
            for ticker in self.active_tickers:
                ticker_data = self.final_message_received.get(ticker)

                # ticker_data가 유효한 dict인지 확인
                if isinstance(ticker_data, dict):
                    for interval in self.KLINE_INTERVALS:
                        interval_data = ticker_data.get(interval)

                        # interval_data가 존재할 때 병합 수행
                        if interval_data:
                            message = self.final_message_received[ticker][interval]
                            # print(f"{ticker}-{interval}병합")
                            await self._merge_kline_data(message)

    # TEST ZONE = 검토대상 체크한다.

    # def validate_kline(self):
    #     #수집된 데이터의 symbols값을 확보한다.
    #     symbols_key = self.kline_data.keys()

    #     # 수집된 데이터의 symbols와 타겟 symbols를 비교한다.
    #     is_symbol = set(symbols_key) == set(self.active_tickers)

    #     if not is_symbol:
    #         print('symbol 없음.')
    #         return False

    #     # 마지막 값만 본다.
    #     get_intervals = [interval for interval in self.kline_data.get(self.active_tickers[-1])]

    #     is_interval = set(get_intervals) == set(self.KLINE_INTERVALS)
    #     if not is_interval:
    #         print('interval 없음.')
    #         return False

    #     target_idx = -1
    #     target_data = self.kline_data[self.active_tickers[target_idx]][self.KLINE_INTERVALS[target_idx]]
    #     data_length = len(target_data)

    #     # print(self.interval_days)
    #     if self.interval_days is None:
    #         print('interval dasy 없음.')
    #         return False

    #     abs_data_len = self._get_kline_limit_by_days(interval=self.KLINE_INTERVALS[-1], days=self.interval_days)
    #     is_data_emtpy = data_length >= abs_data_len

    #     if not is_data_emtpy:
    #         print('data길이 짧음 없음.')
    #         return False

    #     return True

    def __validate(self) -> bool:
        for symbol, symbol_data in self.kline_data.items():
            for interval, interval_data in symbol_data.items():
                if not interval_data:
                    return False
        return True

    async def analysis_loop(self):
        target_interval = "5m"
        await asyncio.sleep(20)
        while True:
            # print(self.active_tickers)
            async with self.lock:
                # kline update중 데이터가 부실할경우 continue
                # if not self.kline_data_update_flag:
                #     # print(self.active_tickers)
                #     # print("데이터 부족. continue")
                #     await asyncio.sleep(5)
                #     continue
                if not self.__validate():
                    # 원인은 모르겠지만 데이터가 업데이트 되기전에 array처리된 상황이 발생했다. 가장 마지막으로 수신예정인 항목을 수신여부 체크한다.
                    await asyncio.sleep(5)
                    continue

                # data길이 안맞을때 그냥 넘김. 이것은 패딩처리로 추후 수정 필요함.
                kline_data_array = utils._convert_to_array(
                    kline_data=self.kline_data, is_slice=True
                )
                # print(kline_data_array)
                # if not kline_data_array[2]:
                #     continue

                symbol_map, interval_map, container_data = utils._convert_to_container(
                    kline_data_array
                )

                if isinstance(symbol_map, int):
                    print("symbol_map이 int로 지정됨.")
                    asyncio.sleep(5)
                    continue

                for symbol, idx_s in symbol_map.items():
                    for interval in interval_map.keys():
                        get_data = container_data.get_data(f"interval_{interval}")[
                            idx_s
                        ]
                        self.analysis_instance.case_1_data_length(
                            kline_data_lv3=get_data
                        )
                        self.analysis_instance.case_2_candle_length(
                            kline_data_lv3=get_data
                        )
                        self.analysis_instance.case_3_continuous_trend_position(
                            kline_data_lv3=get_data
                        )
                        self.analysis_instance.case_7_ocillator_value(
                            kline_data_lv3=get_data
                        )
                        self.analysis_instance.case_8_sorted_indices(
                            kline_data_lv3=get_data, high_col=2, low_col=3
                        )

                    scenario_1 = self.analysis_instance.scenario_2()
                    self.analysis_instance.reset_cases()

                    if scenario_1[0]:
                        await self.submit_open_order_signal(
                            symbol=symbol,
                            position=scenario_1[1],
                            leverage=10,
                        )
                        # self.save_to_json(file_path=path, new_data=result)
            await utils._wait_time_sleep(time_unit="second", duration=30)

    # original code
    # async def analysis_loop(self):
    #     target_interval = "5m"
    # while True:
    #     async with self.lock:
    #         print(self.kline_data_update_flag)
    #         asyncio.sleep(0)

    #     self.analysis_instance.update_data(
    #         kline_data=self.kline_data,
    #         intervals=self.KLINE_INTERVALS,
    #         tickers=self.active_tickers,
    #     )
    #     for ticker in self.analysis_instance.tickers:
    #         is_kline_data = self.analysis_instance._validate_kline_data(ticker)
    #         if not is_kline_data:
    #             continue
    #         case_1 = self.analysis_instance.case1_conditions(ticker)
    #         # DEBUG
    #         if case_1 and case_1[2] and case_1[4] and case_1[3] < 24:
    #             print(f"{ticker} - {case_1}")

    #             order_position = case_1[0]
    #             order_leverage = case_1[3]
    #             if order_leverage is None or order_leverage < 3:
    #                 # order_leverage = 5
    #                 continue

    #             await self.submit_open_order_signal(
    #                 symbol=ticker,
    #                 position=order_position,
    #                 leverage=order_leverage,
    #             )
    #             # self.save_to_json(file_path=path, new_data=result)
    # await utils._wait_time_sleep(time_unit="second", duration=20)


class SpotTrade(TradeManager):
    def __init__(self):
        super().__init__(
            SpotTickers(),
            SpotHandler(),
            my_client.SpotOrder(),
            SpotMarket(),
        )


class FuturesTrade(TradeManager):
    def __init__(self):
        super().__init__(
            FuturesTickers(),
            FuturesHandler(),
            my_client.FuturesOrder(),
            FuturesMarket(),
        )

    # TEST ZONE
    # Position OPEN 신호를 보낸다. 신호가 정상적이라면 positon open 된다.
    async def submit_open_order_signal(self, symbol: str, position: int, leverage: int):
        """
        1. 기능 : Position open 주문 신호를 생성한다. 그에 따른 필요한 값들을 연산도 함께 처리한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) position : SELL or LONG
            3) leverage : 레버리지 값

        """

        # 계좌정보에서 해당 symbol 보유내역 확인
        balance_data = self.account_balance_summary.get(symbol, None)

        # 사용가능한 usdt를 계산한다.
        available_funds = await self.client_instance.get_available_balance()
        total_funds = await self.client_instance.get_total_wallet_balance()

        calc_fund = self.constraint_instance.calc_fund(funds=total_funds)

        count = calc_fund.get("count")
        trade_value = min(calc_fund.get("tradeValue"), available_funds)

        is_active_symbols = symbol in self.account_active_symbols
        is_count_over = count <= len(self.account_active_symbols)

        # 계좌 보유시 추가 매수 금지
        if balance_data or trade_value == 0 or is_active_symbols or is_count_over:
            return

        min_trade_quantity = await self.client_instance.get_min_trade_quantity(symbol)
        max_trade_quantity = await self.client_instance.get_max_trade_quantity(
            symbol=symbol, leverage=leverage, balance=trade_value
        )
        if min_trade_quantity > max_trade_quantity:
            return

        # max_leverage = await self.client_instance.get_max_leverage(symbol)
        max_leverage = 20
        target_leverage = min(max_leverage, leverage)

        # 레버리지 설정
        await self.client_instance.set_leverage(symbol=symbol, leverage=target_leverage)
        # 마진 타입 설정
        await self.client_instance.set_margin_type(
            symbol=symbol, margin_type="ISOLATED"
        )

        order_side = "BUY" if position == 1 else "SELL"
        await self.client_instance.submit_order(
            symbol=symbol,
            side=order_side,
            order_type="MARKET",
            quantity=max_trade_quantity,
        )

        # 매도가격 연산 함수 초기값 실행
        # self.process_instance.initialize_trading_data(symbol = symbol,
        #                                               position = order_side,
        #                                               )
        # 계좌정보 업데이트
        await self.fetch_active_positions()
        print(self.account_balance_summary)
        # entry_price = self.account_balance_summary.get(symbol).get("entryPrice")
        # self.process_instance.initialize_trading_data(
        #     symbol=symbol, position=order_side, entry_price=entry_price
        # )

        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=2)

    # TEST ZONE
    # 포지션 종료 신호를 발송한다.
    async def submit_close_order_signal(self, symbol: str):
        """
        1. 기능 : 해당 symbol의 포지션을 종료한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol정보
        """
        # DEBUG PRINT
        print("종료신호 발생")
        position_data = self.account_balance_summary.get(symbol, None)
        if not position_data:
            return
        if isinstance(position_data, dict) or position_data:
            position_amount = position_data.get("positionAmt", None)
            if not position_amount:
                return
            # 포지션 종료이므로 주문 방향을 반대로 처리 (SELL ↔ BUY)
            order_side = "SELL" if position_amount > 0 else "BUY"

            await self.client_instance.submit_order(
                symbol=symbol,
                side=order_side,
                order_type="MARKET",
                quantity=abs(position_amount),
                reduce_only=True,
            )
            await self.fetch_active_positions()
        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=2)


if __name__ == "__main__":

    import os

    os.system("clear")

    obj = FuturesTrade()

    async def main_run():
        await obj.fetch_active_positions()

        for key, data in obj.account_balance_summary.items():
            symbol = key
            position = "LONG" if data.get("positionAmt") > 0 else "SHORT"
            entry_price = data.get("entryPrice")
            obj.process_instance.initialize_trading_data(
                symbol=symbol, position=position, entry_price=entry_price
            )
        # print(obj.process_instance.trading_data)
        intervals = ["kline_" + interval for interval in obj.KLINE_INTERVALS]

        tasks = [
            asyncio.create_task(obj.ticker_update_loop()),
            asyncio.create_task(obj.connect_kline_loop(ws_intervals=intervals)),
            asyncio.create_task(obj.collect_kline_by_interval_loop()),
            asyncio.create_task(obj.merge_websocket_kline_data_loop()),
            asyncio.create_task(obj.analysis_loop()),
            asyncio.create_task(obj.update_received_data_loop()),
        ]

        await asyncio.gather(*tasks)

    asyncio.run(main_run())
