import TradeComputation
import TickerDataFetcher
import TradeClient
import os
import utils
import numpy as np
import TradeSignalAnalyzer
import asyncio
import nest_asyncio
import utils
from collections import defaultdict

from typing import Dict, Final, List, Any, Union, Tuple


class LiveTradingManager:
    def __init__(
        self,
        seed_money: float,  # 초기 자금
        increase_type: str = "stepwise",  # "stepwise"계단식 // "proportional"비율 증가식
        max_held_symbols: int = 4,  # 동시 거래가능 횟수 제한
        safe_asset_ratio: float = 0.02,  # 전체 금액 안전 자산 비율
        use_scale_stop: bool = True,  # 스케일 손절 적용여부 (최고가 / 최저가에 따른 손절가 변동)
        stop_loss_rate: float = 0.065,  # 손절가 비율
        is_dynamic_adjustment: bool = True,  # 시간 흐름에 따른 손절비율 축소
        dynamic_adjustment_rate: float = 0.0007,  # 시간 흐름에 따른 손절 축소 비율
        dynamic_adjustment_interval: str = "3m",  # 축소비율 적용 시간 간격 (3분 / interval값 사용할 것.)
        requested_leverage: int = 10,  # 지정 레버리지 (symbol별 최대 레버리지값을 초과할 경우 최대 레버리지 적용됨.)
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
        self.increase_type = increase_type
        self.max_held_symbols = max_held_symbols
        self.safe_asset_ratio = safe_asset_ratio
        self.use_scale_stop = use_scale_stop
        self.stop_loss_rate = stop_loss_rate
        self.is_dynamic_adjustment = is_dynamic_adjustment
        self.dynamic_adjustment_rate = dynamic_adjustment_rate
        self.dynamic_adjustment_interval = dynamic_adjustment_interval
        self.requested_leverage = requested_leverage
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
        )  # >> 거래정보 관리 모듈
        self.ins_trade_calculator = TradeComputation.TradeCalculator(
            max_held_symbols=self.max_held_symbols,
            requested_leverage=self.requested_leverage,
            instance=self.ins_portfolio,
            safe_asset_ratio=safe_asset_ratio,
        )  # >> 거래관련 계산 관리 모듈
        self.ins_constraint = TradeComputation.OrderConstraint(
            max_held_symbols=self.max_held_symbols,
            increase_type=self.increase_type,
            chance=self.allowed_loss_streak,
            instance=self.ins_portfolio,
            loss_recovery_interval=self.loss_recovery_interval,
        )  # >> 거래관련 제한사항 관리 모듈
        self.ins_tickers = (
            TickerDataFetcher.FuturesTickers()
        )  # >> Future Market 심볼 관리 모듈
        self.ins_client = TradeClient.FuturesOrder()    # >> Futures Client 주문 모듈

        ### 기본 설정 ###
        self.kline_period: Final[int] = 2  # kline_data 수신시 기간을 지정
        self.intervals: List[str] = self.ins_analyzer.intervals # interval 정보를 가져옴.
        
        ### 데이터 관리용 ###
        self.interval_dataset = (
            utils.DataContainer()
        )  # >> interval 데이터 임시저장 데이터셋
        self.final_message_received: DefaultDict[str, DefaultDict[str, List[List[Any]]]] = defaultdict(lambda: defaultdict())   # websocket data 마지막값 임시저장용
        self.select_symbols: List = []  # 검토 결과 선택된 심볼들
    
    # Ticker 수집에 필요한 정보를 수신
    async def __collect_filtered_ticker_data(self) -> Tuple:
        """
        1. 기능 : 기준값에 충족하는 ticker정보를 수신.
        2. 매개변수 : 해당없음.
        """
        above_value_tickers = await self.ins_tickers.get_tickers_above_value(
            target_value=self.symbols_transaction_volume, comparison=self.symbols_comparison_mode
        )
        above_percent_tickers = await self.ins_tickers.get_tickers_above_change(
            target_percent=self.symbols_price_change_threshold, comparison=self.symbols_comparison_mode, absolute=self.symbols_comparison_mode
        )
        quote_usdt_tickers = await self.ins_tickers.get_asset_tickers(
            quote=self.symbols_quote_currency
        )
        return above_value_tickers, above_percent_tickers, quote_usdt_tickers
    
    # Ticker 필터하여 리스트로 반환
    async def fetch_essential_tickers(self) -> List:
        """
        1. 기능 : 기준값에 충족하는 tickers를 반환.
        2. 매개변수 : 해당없음.
        """
        mandatory_tickers = ["BTCUSDT", "XRPUSDT", "ETHUSDT", "TRXUSDT"]
        filtered_ticker_data = await self.__collect_filtered_ticker_data()
        # 공통 필터링된 티커 요소를 리스트로 반환받음
        common_filtered_tickers = utils._find_common_elements(*filtered_ticker_data)

        # 필수 티커와 공통 필터링된 티커를 합쳐 중복 제거
        final_ticker_list = list(
            set(
                mandatory_tickers
                + common_filtered_tickers
                + list(self.ins_portfolio.open_positions.keys())
            )
        )

        return final_ticker_list
    
    
    async def tickers_loop(self): ...

    def kline_data_loop(self): ...

    def websocket_loop(self): ...

    def get_order_signal(self): ...

    # 손절 여부를 검토한다. (websocket_loop)
    def __stop_loss_monitor(self, websocket_message:Dict) -> bool:
        """
        1. 기능 : 포지션 보유건에 대하여 손절여부를 검토한다.
        2. 매개변수
            1) websocket_message : 웹소켓 수신데이터.
        3. 추가사항 : 오버헤드가 발생할 것으로 예상됨.
        """
        # 웹소켓 메시지에서 심볼 정보를 추출한다.
        symbol = str(websocket_message['s'])
        
        # 보유 여부를 확인한다.
        if self.ins_portfolio.open_positions.get(symbol, None):
            return False
        # 웹소켓 메시지에서 interval 값을 추출한다.
        interval = str(websocket_message['i'])
        # 과도한 연산을 방지하기 위하여 최소 interval값을 반영하는것이다. (current_price는 동일하므로)
        if interval == self.intervals[0]:
            # 현재 가격을 추출한다.
            current_price = float(websocket_message['c'])
            # 현재 시간을 추출한다.
            current_timestamp = int(time.time() * 1000)
            # 데이터를 업데이트하고 포지션 종료여부 신호를 반환한다.
            return self.ins_portfolio.update_log_data(symbol=symbol, price=current_price, timestamp=current_timestamp)

    # 포지션 진입 또는 종료시 보유상태를 점검한다. (submit_order_open_signal // sumbit_order_close_signal)
    async def __verify_position(self, symbol: str, order_type: str) -> Tuple[bool, Dict]:
        """
        1. 기능 : 포지션 진입 또는 종료시 보유상태를 점검한다.
        2. 매개변수
            1) symbol : 대상 심볼
            2) order_type : 점검하고자 하는 주문 종류
        """
        # 포트폴리오 포지션 확인
        portfolio_position = self.ins_portfolio.open_positions.get(symbol, None)

        # API를 통한 전체 보유 현황 조회
        get_account_balance = await self.ins_client.account_balance()
        api_balance = get_account_balance.get(symbol, None)

        if order_type == "close":
            # 포지션이 없을 경우 종료
            if portfolio_position is None:
                return (False, {})

            # API 데이터와 매칭되지 않으면 오류
            if api_balance is None:
                raise ValueError(f'portfolio data 비매칭 발생: {symbol}')

            return (True, api_balance)

        elif order_type == "open":
            # 포지션이 존재하면 종료
            if portfolio_position is not None:
                return (False, {})

            # API 데이터와 매칭되면 오류
            if api_balance is not None:
                raise ValueError(f'portfolio data 비매칭 발생: {symbol}')

            return (True, {})

        else:
            raise ValueError(f'잘못된 order_type: {order_type}')

    # position 진입 신호를 발생한다.
    async def submit_order_open_signal(self, symbol: str, scenario_data:tuple) -> Dict[str, Union[Any]]:
        # 포지션 보유 상태를 점검한다.
        is_verify, _ = await self.__verify_position(symbol=symbol, order_type='open')
        # None이 아닐 경우,
        if not is_verify:
            # 종료한다.
            return
        
        # 현재 진행중인 포지션 수량이 지정 최대 거래 수량 초과시
        if len(self.ins_portfolio.open_positions) >= self.max_held_symbols:
            # 종료한다.
            return
        
        order_signal = scenario_data[0]
        position = scenario_data[1]
        scenario_type = scenario_data[2]
        
        side_order = 'BUY' if position==1 else "SELL"
        # 분석결과 order_signal이 false면
        if not order_signal:
            # 종료한다.
            return
        
        
        reference_data = self.ins_trade_calculator.get_trade_reference_amount()
        is_order_available, quantity, leverage = await self.ins_trade_calculator.get_order_params(trading_symbol=symbol,
                                                                                                  order_amount=reference_data['maxTradeAmount'])
        # 자금이 부족하여 주문이 불가한 경우
        if not is_order_available:
            # 종료한다.
            return
        
        # 마진 타입 설정
        self.ins_client.set_margin_type(symbol=symbol, margin_type='ISOLATED')
        # 레버리지 값 설정
        self.ins_client.set_leverage(symbol=symbol, leverage=leverage)
        # 주문 신호 전송
        order_log = await self.ins_client.submit_order(
            symbol=symbol,
            side=position,
            order_type='MARKET',
            quantity=quantity
        )
        
        # API 1초 대기
        utils._wait_time_sleep(time_unit='second', duration=1)
        # balance 데이터 수신
        account_balance = await self.ins_client.get_account_balance()
        # 대상 데이터 조회
        select_balance_data = account_balance[symbol]
        
        # 거래내역을 log형태로 저장한다.
        log_data = TradeComputation.TradingLog(
            symbol=symbol,
            start_timestamp=int(order_log['updateTime']),
            entry_price=float(select_balance_data['entryPrice']),
            position=position,
            quantity=quantity,
            leverage=leverage,
            trade_scenario=scenario_type,
            test_mode=self.test_mode,
            stop_rate=self.stop_loss_rate,
            init_stop_rate=self.init_stop_rate,
            is_dynamic_adjustment=self.is_dynamic_adjustment,
            dynamic_adjustment_rate=self.dynamic_adjustment_rate,
            dynamic_adjustment_interval=self.dynamic_adjustment_interval,
            use_scale_stop=self.use_scale_stop,
        )
        # 거래시작시 트레이드 정보를 저장한다.
        self.ins_portfolio.add_log_data(log_data=log_data)
        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=1)
        return order_log

    # position 종료 신호를 발생한다.
    async def submit_order_close_signal(self, symbol:str) -> Dict[str, Union[Any]]:
        # 포지션 보유 상태를 점검한다.
        is_verify, api_data = await self.__verify_position(symbol=symbol, order_type='close')
        # 유효성 검사 결과 false면
        if not is_verify:
            # 아무것도 하지 않는다.
            return
        
        # 보유수량을 조회한다.
        position_amount = api_data['positionAmt']
        
        # 거래종료시 진입 포지션과 반대 포지션 구매신호를 보내야 한다.
        order_side = "SELL" if position_amount > 0 else "BUY"

        # 주문 정보를 발송한다.
        order_log = await self.ins_client.submit_order(
            symbol=symbol,  # 목표 symbol
            side=order_side,    # 포지션 정보 : 진입 포지션과 반대로 지정
            order_type="MARKET",    # 거래방식 : limit or market
            quantity=abs(position_amount),  # 매각 수량 : 절대값 반영해야함.
            reduce_only=True,   # 매각처리 여부 : 거래종료시 소수점 단위까지 전량 매각 처리됨.
        )
        
        # 거래종료시 트레이드 정보를 삭제한다.(이후 저장은 아래 함수에서 알아서 처리함.)
        self.ins_portfolio.remove_order_data(symbol=symbol)
        
        # api서버 과요청 방지
        await utils._wait_time_sleep(time_unit="second", duration=1)
        return order_log


    def run(self):
        ...
        


if __name__ == "__main__":
    ins_live_trading = LiveTradingManager(seed_money=5000)
    print(asyncio.run(ins_live_trading.fetch_essential_tickers()))