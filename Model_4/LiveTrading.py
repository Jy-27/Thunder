import TradeComputation
import TickerDataFetcher
import TradeClient
import DataHandler
import os
import utils
import numpy as np
import TradeSignalAnalyzer
import asyncio
import nest_asyncio
import datetime
import MarketDataFetcher
import time
from copy import copy, deepcopy
from collections import defaultdict

from typing import Dict, Final, List, Any, Union, Tuple, cast, Optional
from pprint import pprint


class LiveTradingManager:
    def __init__(
        self,
        seed_money: float,  # 초기 자금
        market: str,  # 거래중인 시장 정보
        kline_period: int,
        increase_type: str = "stepwise",  # "stepwise"계단식 // "proportional"비율 증가식
        max_held_symbols: int = 4,  # 동시 거래가능 횟수 제한
        safe_asset_ratio: float = 0.02,  # 전체 금액 안전 자산 비율
        use_scale_stop: bool = True,  # 스케일 손절 적용여부 (최고가 / 최저가에 따른 손절가 변동)
        stop_loss_rate: float = 0.035,  # 손절가 비율
        is_dynamic_adjustment: bool = True,  # 시간 흐름에 따른 손절비율 축소
        dynamic_adjustment_rate: float = 0.0007,  # 시간 흐름에 따른 손절 축소 비율
        dynamic_adjustment_interval: str = "3m",  # 축소비율 적용 시간 간격 (3분 / interval값 사용할 것.)
        requested_leverage: int = 10,  # 지정 레버리지 (symbol별 최대 레버리지값을 초과할 경우 최대 레버리지 적용됨.)
        max_leverage: int = 30,  # 최대 레버리지값
        init_stop_rate: float = 0.035,  # 시작 손절 비율 (use_scale_stop:False일경우 stop_loss_rate반영)
        is_order_break: bool = True,  # 반복 손실시 주문 불가 신호 발생
        allowed_loss_streak: int = 2,  # 반복 손실 유예 횟수
        loss_recovery_interval: str = "4h",  # 반복 손실 시간 범위 지정 (설명 : 4시간 동안 2회 손실 초과시 주문신호 생겨도 주문 거절처리 됨.)
        is_profit_preservation: bool = True,  # 수익발생 부분 별도 분리 (원금 초과 수익분 Futures >> Spot 계좌로 이동)
        symbols_comparison_mode: str = "above",  # 조건 비교 모드: 이상(above), 이하(below)
        symbols_use_absolute_value: bool = True,  # True: 비율 절대값 사용, False: 실제값 사용
        symbols_transaction_volume: int = 550_000_000,  # 거래대금 (USD 단위)
        symbols_price_change_threshold: float = 0.035,  # 변동 비율 폭 (음수 가능)
        symbols_quote_currency: str = "usdt",  # 쌍거래 기준 화폐
    ):
        self.seed_money = seed_money
        self.market = market
        self.kline_period = kline_period
        self.increase_type = increase_type
        self.max_held_symbols = max_held_symbols
        self.safe_asset_ratio = safe_asset_ratio
        self.use_scale_stop = use_scale_stop
        self.stop_loss_rate = stop_loss_rate
        self.is_dynamic_adjustment = is_dynamic_adjustment
        self.dynamic_adjustment_rate = dynamic_adjustment_rate
        self.dynamic_adjustment_interval = dynamic_adjustment_interval
        self.requested_leverage = requested_leverage
        self.max_leverage = max_leverage
        self.init_stop_rate = init_stop_rate
        self.is_order_break = is_order_break
        self.allowed_loss_streak = allowed_loss_streak
        self.loss_recovery_interval = loss_recovery_interval
        self.is_profit_preservation = is_profit_preservation
        self.symbols_comparison_mode = symbols_comparison_mode
        self.symbols_use_absolute_value = symbols_use_absolute_value
        self.symbols_transaction_volume = symbols_transaction_volume
        self.symbols_price_change_threshold = symbols_price_change_threshold
        self.symbols_quote_currency = symbols_quote_currency

        ### instance 설정 ###
        self.ins_analyzer = TradeSignalAnalyzer.AnalysisManager(
            back_test=False
        )  # >> 데이터 분석 모듈
        self.ins_portfolio = TradeComputation.PortfolioManager(
            is_profit_preservation=self.is_profit_preservation,
            initial_balance=self.seed_money,
            market=self.market,
        )  # >> 거래정보 관리 모듈
        self.ins_trade_calculator: Optional[TradeComputation] = (
            None  # >> 거래관련 계산 관리 모듈 // start_update_account함수에서 재선언함.
        )
        # self.ins_trade_calculator = TradeComputation.TradeCalculator(
        #     max_held_symbols=self.max_held_symbols,
        #     requested_leverage=self.requested_leverage,
        #     instance=self.ins_portfolio,
        #     safe_asset_ratio=self.safe_asset_ratio,
        # )  # >> 거래관련 계산 관리 모듈
        self.ins_constraint = TradeComputation.OrderConstraint(
            market=self.market,
            max_held_symbols=self.max_held_symbols,
            increase_type=self.increase_type,
            chance=self.allowed_loss_streak,
            instance=self.ins_portfolio,
            loss_recovery_interval=self.loss_recovery_interval,
        )  # >> 거래관련 제한사항 관리 모듈
        self.ins_tickers = (
            TickerDataFetcher.FuturesTickers()
        )  # >> Future Market 심볼 관리 모듈
        self.ins_client = TradeClient.FuturesOrder()  # >> Futures Client 주문 모듈
        self.ins_handler = DataHandler.FuturesHandler(
            intervals=self.ins_analyzer.intervals
        )  # >> Futures 데이터 수신 모듈
        self.ins_market = (
            MarketDataFetcher.FuturesMarket()
        )  # >> market 데이터 수신 모듈

        ### 기본 설정 ###
        self.kline_period: Final[int] = 2  # kline_data 수신시 기간을 지정
        self.convert_intervals: List[str] = [
            "kline_" + interval for interval in self.ins_analyzer.intervals
        ]  # interval 정보를 가져옴.

        ### 데이터 관리용 ###
        self.interval_dataset = (
            utils.DataContainer()
        )  # >> interval 데이터 임시저장 데이터셋
        self.final_message_received: DefaultDict[
            str, DefaultDict[str, List[List[Any]]]
        ] = defaultdict(
            lambda: defaultdict()
        )  # websocket data 마지막값 임시저장용
        self.select_symbols: List = []  # 검토 결과 선택된 심볼들
        self.kline_data: DefaultDict[str, DefaultDict[str, List[List[Any]]]] = (
            defaultdict(lambda: defaultdict())
        )  # kline_data 저장용

        ### 유틸리티 ###
        self.lock = asyncio.Lock()
        self.is_data_ready = False  # kline_data 수신 완료여부

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---==-* 심볼 수신관련    *-==---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    # Ticker 수집에 필요한 정보를 수신
    async def __collect_filtered_ticker_data(self) -> Tuple:
        """
        1. 기능 : 기준값에 충족하는 ticker정보를 수신.
        2. 매개변수 : 해당없음.
        """
        above_value_tickers = await self.ins_tickers.get_tickers_above_value(
            target_value=self.symbols_transaction_volume,
            comparison=self.symbols_comparison_mode,
        )
        above_percent_tickers = await self.ins_tickers.get_tickers_above_change(
            target_percent=self.symbols_price_change_threshold,
            comparison=self.symbols_comparison_mode,
            absolute=self.symbols_comparison_mode,
        )
        quote_usdt_tickers = await self.ins_tickers.get_asset_tickers(
            quote=self.symbols_quote_currency
        )
        return above_value_tickers, above_percent_tickers, quote_usdt_tickers

    # Ticker 필터하여 리스트로 반환
    async def __fetch_essential_tickers(self) -> List:
        """
        1. 기능 : 기준값에 충족하는 tickers를 반환.
        2. 매개변수 : 해당없음.
        """
        mandatory_tickers = ["BTCUSDT", "XRPUSDT", "ETHUSDT", "TRXUSDT"]

        if self.ins_portfolio.open_positions:
            for symbol_code, _ in self.ins_portfolio.open_positions.items():
                symbol = symbol_code.split("_")[1]
                mandatory_tickers.append(symbol)

        filtered_ticker_data = await self.__collect_filtered_ticker_data()
        # 공통 필터링된 티커 요소를 리스트로 반환받음
        common_filtered_tickers = utils._find_common_elements(*filtered_ticker_data)

        # 필수 티커와 공통 필터링된 티커를 합쳐 중복 제거
        final_ticker_list = list(set(mandatory_tickers + common_filtered_tickers))

        return final_ticker_list

    # symbol값 업데이트
    async def ticker_update_loop(self):
        """
        1. 기능 : Tickers를 주기적으로 update한다.
        2. 매개변수 : 해당없음.
        """
        while True:
            # kline_data 준비 미완료 표시
            self.is_data_ready = False
            # 수신 데이터 초기화
            self.final_message_received.clear()
            # kline data 초기화
            self.kline_data.clear()

            await self.ins_handler.generator_control_signal()
            try:
                # 필수 티커를 업데이트
                self.select_symbols = await self.__fetch_essential_tickers()

                print(
                    f"symbols - {len(self.select_symbols)}종 update! {datetime.datetime.now()}\n"
                )
                # print(self.select_symbols)
                # 간격 대기 함수 호출 (예: 4시간 간격)

                # ticker update완료시 신규 kline데이터 갱신함.
                async with self.lock:
                    self.kline_data.clear()
                # # ticker 초기화시 전체 kline을 업데이트 한다.abs
                await self.update_all_klines(days=self.kline_period)
                # self.kline_data_update_flag = True

            except Exception as e:
                # 예외 발생 시 로깅 및 오류 메시지 출력
                print(f"Error in ticker_update_loop: {e}")
            # 적절한 대기 시간 추가 (예: 짧은 대기)
            # interval 지정값 기준 시계 시간을 의미.
            await utils._wait_until_next_interval(time_unit="minute", interval=10)

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---=-*kline data수신관련 *-=---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    # klline 매개변수에 들어갈 유효 limit
    def __get_valid_kline_limit(self, interval: str) -> Dict:
        # 상수 설정
        VALID_INTERVAL_UNITS = ["m", "h", "d", "w", "M"]
        MINUTES_PER_DAY = 1_440
        MAX_KLINE_LIMIT = 1_000

        # interval 유효성 검사
        interval_unit = interval[-1]
        interval_value = int(interval[:-1])

        if interval not in self.ins_analyzer.intervals:
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
    def __get_kline_limit_by_days(self, interval: str, days: int) -> int:
        """
        1. 기능 : kline 매개변수에 들어갈 day 기간 만큼 interval의 limit값을 구한다.
        2. 매개변수
            1) interval : KLINE_INTERVALS 속성 참조
            2) day : 기간을 정한다.
        """
        day, limit = self.__get_valid_kline_limit(interval=interval)
        if day == 0:
            return 1000
        max_klines_per_day = (limit / day) * days

        if max_klines_per_day > 1_000:
            print(
                f"The calculated limit exceeds the maximum allowed value: {max_klines_per_day}. Limiting to 1,000."
            )
            return 1_000

        return int(max_klines_per_day)

    # kline전체를 days기준 범위로 업데이트한다. tickers 업데이트시 일괄 업데이트
    async def update_all_klines(self, days: int = 1):
        """
        1. 기능 : 현재 선택된 ticker에 대한 모든 interval kline을 수신한다.
        2. 매개변수
            1) max_recordes : max 1_000, 조회할 데이터의 길이를 정한다.
        """
        # 활성화된 티커가 준비될 때까지 대기
        while not self.select_symbols:
            await asyncio.sleep(
                2
            )  # awaitutils._wait_time_sleep을 asyncio.sleep으로 대체하여 비동기 방식으로 대기

        # 모든 활성화된 티커에 대해 데이터를 수집 및 업데이트
        for ticker in self.select_symbols:
            for interval in self.ins_analyzer.intervals:
                if interval.endswith("d"):
                    limit_ = 30
                else:
                    limit_ = self.__get_kline_limit_by_days(
                        interval=interval, days=self.kline_period
                    )
                # Kline 데이터를 수집하고 self.kline_data에 업데이트
                self.kline_data[ticker][interval] = (
                    await self.ins_market.fetch_klines_limit(
                        symbol=ticker,
                        interval=interval,
                        limit=limit_,
                    )
                )
        # 데이터가 준비 되었음을 표시
        self.is_data_ready = True

    # hour 또는 minute별 수신해야할 interval을 리스트화 정렬
    def __generate_time_intervals(self):
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

        for interval in self.ins_analyzer.intervals:
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

    # kline_data 수집 최종버전.
    async def collect_kline_by_interval_loop(self, days: int = 2):
        # interval day기간을 속성에 저장 후 현재 로딩 데이터의 길이가 유효한지 검토하는 목적
        interval_map = self.__generate_time_intervals()
        time_units = ["hours", "minutes"]

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
                            for ticker in self.select_symbols:
                                for interval in intervals:
                                    limit_ = self.__get_kline_limit_by_days(
                                        interval=interval, days=days
                                    )

                                    # ### DEBUG
                                    # print(f'{ticker} - {interval}')

                                    self.kline_data[ticker][interval] = (
                                        await self.ins_market.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=limit_,
                                        )
                                    )
                        if time_unit == time_units[1] and current_time_minute == times:
                            for ticker in self.select_symbols:
                                for interval in intervals:
                                    limit_ = self.__get_kline_limit_by_days(
                                        interval=interval, days=days
                                    )
                                    # ### DEBUG
                                    # print(f'{ticker} - {interval}')
                                    self.kline_data[ticker][interval] = (
                                        await self.ins_market.fetch_klines_limit(
                                            symbol=ticker,
                                            interval=interval,
                                            limit=limit_,
                                        )
                                    )

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---=-*websocket 수신관련 *-=---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    # websocket 데이터 수신
    async def websocket_loop(self):
        """
        1. 기능 : websocket을 실행하고 kline형태로 데이터를 수신한다.
        2. 매개변수
            1) ws_intervals : KLINE_INTERVALS 속성 참조
        """
        # 정시(0초)에 WebSocket 연결을 시작하기 위한 대기 로직
        await utils._wait_until_exact_time(time_unit="minute")
        print(f"WebSocket Loop 진입 - {utils._get_time_component()}")

        while True:
            # 중단 이벤트 또는 초기 Ticker 데이터 비어있음에 대한 대응
            if self.ins_handler.stop_event.is_set():
                print(f"Loop 중단 - 중단 이벤트 감지됨 {utils._get_time_component()}")
                break  # stop_event가 설정된 경우 루프 종료

            if not self.select_symbols:
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
                # print(len(self.select_symbols))

                await self.ins_handler.connect_kline_limit(
                    symbols=self.select_symbols, intervals=self.convert_intervals
                )

                print(f"tickers update complete - {utils._get_time_component()}")
                # 시스템 안정성을 위한 5초 대기
                await utils._wait_time_sleep(time_unit="second", duration=5)
            except Exception as e:
                print(f"WebSocket 연결 오류 발생: {e} - {utils._get_time_component()}")
                # 오류 발생 시 안전하게 대기 후 재시도
                await utils._wait_time_sleep(time_unit="second", duration=5)

    # kline 데이터 수신 및 stoploss 검토.
    async def final_message_stop_loss_check(self):
        """'
        1. 기능 : websocket 수신데이터의 마지막 값을 저장하고 스톱로스를 감시 및 매도주문을 발생한다.
        2. 매개변수 : 해당없음.
        """
        while True:
            # DEBUG
            # queue 데이터가 존재한다면,
            if not self.ins_handler.asyncio_queue.empty():
                # 웹소켓 메시지를 queue에서 획득하고
                websocket_message = await self.ins_handler.asyncio_queue.get()
                # 심볼값과
                symbol = websocket_message["s"]
                # interval
                interval = websocket_message["k"]["i"]
                # close price값을 추출한다.
                # 웹소켓 메시지 원본 데이터를 별도 저장한다. (마지막값만 계속 업데이트)
                self.final_message_received[symbol][interval] = websocket_message

                # 현재 보유중인 포지션이 있을경우 손절여부를 검토한다.
                # DEBUG
                # print(websocket_message)
                # orignal_code
                if self.__stop_loss_monitor(websocket_message):
                    await self.submit_order_close_signal(symbol=symbol)
                    print("\n" + "=" * 30)
                    print("Portfolio Summary".center(30))
                    print("=" * 30)
                    print(
                        f"1. Init Balance  : {self.ins_portfolio.initial_balance:,.2f} USD"
                    )
                    print(
                        f"2. Total Balance : {self.ins_portfolio.total_wallet_balance:,.2f} USD"
                    )
                    print(
                        f"3. PNL           : {self.ins_portfolio.profit_loss:,.2f} USD"
                    )
                    print(
                        f"4. PNL Ratio     : {self.ins_portfolio.profit_loss_ratio * 100:,.1f} %"
                    )
                    print("=" * 30 + "\n")
            else:
                await asyncio.sleep(2)

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---=-* kline_data 편집관련 *-=---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    # WebSocket에서 수신한 kline 데이터를 OHLCV 형식으로 변환
    def __transform_kline(
        self, raw_websocket_message: dict
    ) -> List[Union[str, int, float]]:
        """
        WebSocket에서 수신한 kline 데이터를 OHLCV 형식으로 변환합니다.

        Args:
            raw_websocket_message (dict): WebSocket에서 수신된 원시 kline 데이터

        Returns:
            List[Union[str, int, float]]: 변환된 kline 데이터 리스트 (OHLCV 형식)
        """
        kline_details = raw_websocket_message.get("k", {})

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

    # kline_data의 마지막 값을 웹소켓 수신데이터 마지막값으로 업데이트한다. 분석함수에 상속예정.
    def update_last_element(self):
        """'
        1. 기능 : kline_data의 마지막 값을 웹소켓 데이터로 업데이트한다.
        2. 매개변수 : 해당없음.
        3. 추가사항 : kline_data와 websocket 데이터는 자료타입이 다르다.
                    하지만 np.array(object, float)으로 자료형태를 수정할 예정이므로 문제 없다.
        """
        if self.is_data_ready:
            for symbol, symbol_data in self.kline_data.items():
                for interval, interval_data in symbol_data.items():

                    message_symbol_data = self.final_message_received.get(symbol, None)
                    if message_symbol_data is None:
                        continue
                    message_interval_data = self.final_message_received[symbol].get(
                        interval, None
                    )
                    if message_interval_data is None:
                        continue

                    message_last_data = self.final_message_received[symbol][interval]

                    kline_last_data = interval_data[-1]
                    transform_kline = self.__transform_kline(message_last_data)

                    # open_timestamp / close timestamp가 같을경우
                    if (kline_last_data[0] == transform_kline[0]) and (
                        kline_last_data[6] == transform_kline[6]
                    ):
                        # 값을 수정한다.
                        self.kline_data[symbol][interval][-1] = transform_kline

                    # kline_data open_timestam가 웹소켓 open_timestamp보다 작을경우
                    if kline_last_data[0] < transform_kline[0]:
                        # 값을 추가한다.
                        self.kline_data[symbol][interval].append(transform_kline)

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---=-* 분석 파트 (주문 포함) *-=---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    async def trade_siganl_analyzer_loop(self):
        while True:
            if self.is_data_ready:
                # kline_data를 웹소켓 데이터로 업데이트한다.
                self.update_last_element()
                # 데이터셋을 비운다.
                self.interval_dataset.clear_all_data()

                # #DEBUG
                # start = time.time()

                # 심볼을 추출
                for symbol in self.select_symbols:
                    # interval을 추출
                    for interval in self.ins_analyzer.intervals:
                        # 데이터를 np.ndarray화 한다. 타입은 float
                        array_ = np.array(
                            object=self.kline_data[symbol][interval], dtype=float
                        )
                        # 각 interval 데이터를 컨테이너 데이터화 한다.
                        self.interval_dataset.set_data(
                            data_name=f"{self.market}_{symbol}_{interval}", data=array_
                        )
                # 컨테이너 데이터를 분석 클라스의 속성값에 넣는다.
                self.ins_analyzer.data_container = self.interval_dataset
                # 분석을 시작한다.
                # debug
                # print(symbol)
                scenario_data = self.ins_analyzer.scenario_run()

                # 분석 결과를 주문 함수에 넣는다. false일경우 자동 return
                await self.submit_order_open_signal(scenario_data=scenario_data)

                # # DEBUG
                # end = time.time()
                # print(f'{len(self.select_symbols)}종 연산 소요 시간 : {end-start:,.2f} sec')

                # 20초 대기한다.
                await asyncio.sleep(20)
            # 데이터가 온전치 못할경우 5초 대기한다.
            await asyncio.sleep(5)

    ##=--=####=---=###=--=####=---=###=--=##
    # -=##=---=-* 주문 명령 관련 *-=---=##=-#
    ##=--=####=---=###=--=####=---=###=--=##

    # 프로그램 시작시 계좌정보를 업데이트한다.
    async def start_update_account(self):
        # 총 평가금액을 불러온다.
        api_total_balance = await self.ins_client.get_total_wallet_balance()

        # 거래중인 항목을 불러온다.
        api_balance = await self.ins_client.get_account_balance()

        # 초기 설정 자금보다 실제 자금이 작을경우
        if self.seed_money > api_total_balance:
            # 실제 자금으로 시드머니를 조정한다.
            print(
                f"seed money 조정 : {self.seed_money :,.2f} -> {api_total_balance:,.2f}"
            )
            self.seed_money = api_total_balance
            # instance 재설정.
            self.ins_portfolio = TradeComputation.PortfolioManager(
                is_profit_preservation=self.is_profit_preservation,
                initial_balance=self.seed_money,
                market=self.market,
            )  # >> 거래정보 관리 모듈
            self.ins_trade_calculator = TradeComputation.TradeCalculator(
                max_held_symbols=self.max_held_symbols,
                requested_leverage=self.requested_leverage,
                instance=self.ins_portfolio,
                safe_asset_ratio=self.safe_asset_ratio,
            )  # >> 거래관련 계산 관리 모듈

        # 거래중인 항목이 없으면,
        if not api_balance:
            # 아무것도 하지 않는다.
            return

        # 거래중인 항목 내역을 트레이딩 로그에 기록한다.
        for symbol, log in api_balance.items():

            initial_margin = log["initialMargin"]
            isolated_wallet = log["isolatedWallet"]
            entry_fee = initial_margin - isolated_wallet
            exit_fee = 0

            log_data = TradeComputation.TradingLog(
                symbol=f"{self.market}_{symbol}",
                start_timestamp=int(log["updateTime"]),
                entry_price=float(log["entryPrice"]),
                position=1 if log["positionAmt"] > 0 else 2,
                quantity=abs(log["positionAmt"]),
                leverage=log["leverage"],
                trade_scenario=0,
                test_mode=False,
                stop_rate=self.stop_loss_rate,
                init_stop_rate=self.init_stop_rate,
                is_dynamic_adjustment=self.is_dynamic_adjustment,
                dynamic_adjustment_rate=self.dynamic_adjustment_rate,
                dynamic_adjustment_interval=self.dynamic_adjustment_interval,
                use_scale_stop=self.use_scale_stop,
                initial_value=initial_margin,
                entry_fee=entry_fee,
                exit_fee=exit_fee,
            )

            # debug
            pprint(log_data)
            # 거래시작시 트레이드 정보를 저장한다.
            self.ins_portfolio.add_log_data(log_data=log_data)

    # 손절 여부를 검토한다. (websocket_loop)
    def __stop_loss_monitor(self, websocket_message: Dict) -> bool:
        """
        1. 기능 : 포지션 보유건에 대하여 손절여부를 검토한다.
        2. 매개변수
            1) websocket_message : 웹소켓 수신데이터.
        3. 추가사항 : 오버헤드가 발생할 것으로 예상됨.
        """
        # 웹소켓 메시지에서 심볼 정보를 추출한다.
        symbol = str(websocket_message["s"])

        convert_to_symbol = f"{self.market}_{symbol}"
        # 보유 여부를 확인한다.
        if self.ins_portfolio.open_positions.get(convert_to_symbol, None) is None:
            return False
        # 웹소켓 메시지에서 interval 값을 추출한다.
        kline_data = websocket_message["k"]
        interval = kline_data["i"]
        event_timestamp = websocket_message["E"]

        # 과도한 연산을 방지하기 위하여 최소 interval값을 반영하는것이다. (current_price는 동일하므로)
        if interval == self.ins_analyzer.intervals[0]:
            # DEBUG
            # 현재 가격을 추출한다.
            current_price = float(kline_data["c"])

            # original code
            # 데이터를 업데이트하고 포지션 종료여부 신호를 반환한다.
            return self.ins_portfolio.update_log_data(
                symbol=symbol, price=current_price, timestamp=event_timestamp
            )

            # # debug
            # signal_ = self.ins_portfolio.update_log_data(
            #     symbol=convert_to_symbol, price=current_price, timestamp=event_timestamp
            # )
            # print(signal_)
            # pprint(self.ins_portfolio.data_container.get_data(convert_to_symbol))

    # 포지션 진입 또는 종료시 보유상태를 점검한다. (submit_order_open_signal // sumbit_order_close_signal)
    async def __verify_position(
        self, symbol: str, order_type: str
    ) -> Tuple[bool, Dict]:
        """
        1. 기능 : 포지션 진입 또는 종료시 보유상태를 점검한다.
        2. 매개변수
            1) symbol : 대상 심볼
            2) order_type : 점검하고자 하는 주문 종류
        """
        # 포트폴리오 포지션 확인
        convert_to_symbol = f"{self.market}_{symbol}"
        portfolio_position = self.ins_portfolio.open_positions.get(
            convert_to_symbol, None
        )

        # API를 통한 전체 보유 현황 조회
        get_account_balance = await self.ins_client.get_account_balance()
        api_balance = get_account_balance.get(symbol, None)

        if order_type == "close":
            # 포지션이 없을 경우 종료
            if portfolio_position is None:
                return (False, {})

            # API 데이터와 매칭되지 않으면 오류
            if api_balance is None:
                raise ValueError(f"portfolio data 비매칭 발생: {symbol}")

            return (True, api_balance)

        elif order_type == "open":
            # 포지션이 존재하면 종료
            if portfolio_position is not None:
                return (False, {})

            # API 데이터와 매칭되면 오류
            if api_balance is not None:
                raise ValueError(f"portfolio data 비매칭 발생: {symbol}")

            return (True, {})

        else:
            raise ValueError(f"잘못된 order_type: {order_type}")

    # position 진입 신호를 발생한다.
    async def submit_order_open_signal(
        self, scenario_data: tuple
    ) -> Dict[str, Union[Any]]:

        order_signal = scenario_data[0]
        symbol = scenario_data[1]
        position = scenario_data[2]
        scenario_type = scenario_data[3]
        scenario_leverage = int(scenario_data[4] * self.requested_leverage)
        select_leverage = min(scenario_leverage, self.max_leverage)

        # 분석결과 order_signal이 false면
        if not order_signal:
            # 종료한다.
            return

        # 현재 진행중인 포지션 수량이 지정 최대 거래 수량 초과시
        if len(self.ins_portfolio.open_positions) >= self.max_held_symbols:
            # 종료한다.
            return

        # 포지션 보유 상태를 점검한다.
        is_verify, _ = await self.__verify_position(symbol=symbol, order_type="open")
        # None이 아닐 경우,
        if not is_verify:
            # 종료한다.
            return

        side_order = "BUY" if position == 1 else "SELL"

        reference_data = self.ins_trade_calculator.get_trade_reference_amount()
        # debug
        # pprint(reference_data)
        if (
            reference_data["maxTradeAmount"] * 1.025
            < self.ins_portfolio.available_balance
        ):
            amount = reference_data["maxTradeAmount"]
        else:
            amount = 0
        # DEBUG
        # print(amount)
        is_order_available, quantity, leverage = (
            await self.ins_trade_calculator.get_order_params(
                trading_symbol=symbol,
                order_amount=amount,
                scenario_leverage=select_leverage,
            )
        )
        
        # debug
        print(f'staus - {is_order_available}')
        print(f'quantity - {quantity}')
        print(leverage)        
        print(self.ins_portfolio.available_balance)
        # 자금이 부족하여 주문이 불가한 경우
        if not is_order_available:
            print(f"주문불가: {symbol} - {leverage} / 잔액 부족")
            # 종료한다.
            return

        # debug
        # print(symbol)
        # 마진 타입 설정
        await self.ins_client.set_margin_type(symbol=symbol, margin_type="ISOLATED")
        # 레버리지 값 설정
        await self.ins_client.set_leverage(symbol=symbol, leverage=leverage)
        # 주문 신호 전송
        order_log = await self.ins_client.submit_order(
            symbol=symbol, side=side_order, order_type="MARKET", quantity=quantity
        )

        # debug
        pprint(order_log)
        
        # API 1초 대기
        await utils._wait_time_sleep(time_unit="second", duration=1)
        # balance 데이터 수신
        account_balance = await self.ins_client.get_account_balance()
        # 대상 데이터 조회
        select_balance_data = account_balance[symbol]

        initial_margin = select_balance_data["initialMargin"]
        isolated_wallet = select_balance_data["isolatedWallet"]
        entry_fee = initial_margin - isolated_wallet
        exit_fee = 0

        # 거래내역을 log형태로 저장한다.
        log_data = TradeComputation.TradingLog(
            symbol=f"{self.market}_{symbol}",
            start_timestamp=int(order_log["updateTime"]),
            entry_price=float(select_balance_data["entryPrice"]),
            position=position,
            quantity=quantity,
            leverage=leverage,
            trade_scenario=scenario_type,
            test_mode=False,
            stop_rate=self.stop_loss_rate,
            init_stop_rate=self.init_stop_rate,
            is_dynamic_adjustment=self.is_dynamic_adjustment,
            dynamic_adjustment_rate=self.dynamic_adjustment_rate,
            dynamic_adjustment_interval=self.dynamic_adjustment_interval,
            use_scale_stop=self.use_scale_stop,
            initial_value=initial_margin,
            entry_fee=entry_fee,
            exit_fee=exit_fee,
        )
        # 거래시작시 트레이드 정보를 저장한다.
        self.ins_portfolio.add_log_data(log_data=log_data)
        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=1)
        return order_log

    # position 종료 신호를 발생한다.
    async def submit_order_close_signal(self, symbol: str) -> Dict[str, Union[Any]]:
        # 포지션 보유 상태를 점검한다.
        is_verify, api_data = await self.__verify_position(
            symbol=symbol, order_type="close"
        )

        # 유효성 검사 결과 false면
        if not is_verify:
            # 아무것도 하지 않는다.
            return

        # 보유수량을 조회한다.
        position_amount = float(api_data["positionAmt"])

        # 거래종료시 진입 포지션과 반대 포지션 구매신호를 보내야 한다.
        order_side = "SELL" if position_amount > 0 else "BUY"

        # 매각 전 예수금
        before_sell_balance = await self.ins_client.get_available_balance()

        # 주문 정보를 발송한다.
        order_log = await self.ins_client.submit_order(
            symbol=symbol,  # 목표 symbol
            side=order_side,  # 포지션 정보 : 진입 포지션과 반대로 지정
            order_type="MARKET",  # 거래방식 : limit or market
            quantity=abs(position_amount),  # 매각 수량 : 절대값 반영해야함.
            reduce_only=True,  # 매각처리 여부 : 거래종료시 소수점 단위까지 전량 매각 처리됨.
        )

        # 매각 후 예수금
        after_sell_balance = await self.ins_client.get_available_balance()

        # 거래 정보를 조회한다.
        trade_history = await self.ins_client.fetch_trade_history(symbol)
        last_trade_history = trade_history[-1]

        # 최종 데이터를 획득한다.
        commission = float(last_trade_history["commission"])
        # 종료 가격을 조회한다.
        closed_price = float(last_trade_history["price"])
        # 종료 시간을 조회한다.
        closed_timestamp = int(last_trade_history["time"])
        # 매각 후 회수금
        sell_balance = after_sell_balance - before_sell_balance + commission

        # 종료시 정보를 업데이트한다.
        self.ins_portfolio.update_log_data(
            symbol=symbol, price=closed_price, timestamp=closed_timestamp
        )

        convert_to_symbol = f"{self.market}_{symbol}"

        # 상세내역 강제 업데이트한다.
        self.ins_portfolio.data_container.get_data(convert_to_symbol).exit_fee = (
            commission
        )
        self.ins_portfolio.data_container.get_data(convert_to_symbol).current_value = (
            sell_balance
        )

        # 거래종료시 트레이드 정보를 삭제한다.(이후 저장은 아래 함수에서 알아서 처리함.)
        self.ins_portfolio.remove_order_data(symbol=symbol)

        # 금액 보정
        if not self.ins_portfolio.open_positions:
            self.ins_portfolio.available_balance = after_sell_balance
            self.ins_portfolio.total_wallet_balance = after_sell_balance
            self.ins_portfolio.profit_loss = (
                self.ins_portfolio.total_wallet_balance
                - self.ins_portfolio.initial_balance
            )
            self.ins_portfolio.profit_loss_ratio = (
                self.ins_portfolio.profit_loss / self.ins_portfolio.total_wallet_balance
            )

        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=1)
        return order_log

    # 실행 파트
    async def run(self):
        # 기존 거래중 항목 메모리 업데이트(binanace << >> memory)
        await self.start_update_account()

        tasks = [
            asyncio.create_task(self.ticker_update_loop()),
            asyncio.create_task(self.websocket_loop()),
            asyncio.create_task(
                self.collect_kline_by_interval_loop(days=self.kline_period)
            ),
            asyncio.create_task(self.final_message_stop_loss_check()),
            asyncio.create_task(self.trade_siganl_analyzer_loop()),
        ]
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    ins_live_trading = LiveTradingManager(seed_money=13)
    asyncio.run(ins_live_trading.run())
