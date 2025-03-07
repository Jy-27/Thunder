import TradeComputation
import TickerDataFetcher
import os
import utils
import asyncio
import nest_asyncio
import pickle
import TradeSignalAnalyzer
from pprint import pprint
import matplotlib.pyplot as plt
from matplotlib import style, ticker
from typing import Optional, List, Union
import numpy as np
from multiprocessing import Pool, Manager

## 신규 테스트
import DataStoreage
import Analysis_new

class BackTesterManager:
    def __init__(
        self,
        symbols: list[str],
        market: str,
        kline_period: int,
        max_held_symbols: int,
        seed_money: Union[int, float],
        start_date: str,
        end_date: str,
        increase_type: str = "stepwise",  # "stepwise"계단식 // "proportional"비율 증가식
        init_stop_rate: float = 0.015,
        dynamic_adjustment_interval: str = "3m",
        dynamic_adjustment_rate: float = 0.0007,
        is_use_scale_stop: bool = True,
        is_dynamic_adjustment: bool = True,
        stop_loss_rate: float = 0.025,
        safe_asset_ratio: float = 0.2,
        is_download: bool = True,
        requested_leverage: int = 10,
        is_profit_preservation: bool = True,
        # 주문신호 유효성 검토(브레이크 기능)
        is_order_break: bool = True,
        allowed_loss_streak: int = 2,
        loss_recovery_interval: str = "2h",
        comparison: str = "above",
        absolute: bool = True,
        value: int = 350_000_000,
        percent: float = 0.03,
        quote_type: str = "usdt",
    ):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.market = market
        self.max_held_symbols = max_held_symbols
        self.start_date = start_date
        self.end_date = end_date
        # 전체 금액에서 안전금액 비율
        self.stop_loss_rate = stop_loss_rate
        self.is_download = is_download
        self.is_dynamic_adjustment = is_dynamic_adjustment
        self.dynamic_adjustment_rate = dynamic_adjustment_rate
        self.dynamic_adjustment_interval = dynamic_adjustment_interval
        self.is_use_scale_stop = is_use_scale_stop
        self.requested_leverage = requested_leverage
        self.is_profit_preservation = is_profit_preservation
        # 반복적인 손실발생시 해당 시나리오는 브레이크 타임을 갖는다.
        self.is_order_break = is_order_break
        # 시나리오 브레이크임 진입전 손실 횟수
        self.allowed_loss_streak: Optional[int] = (
            allowed_loss_streak if self.is_order_break else None
        )
        # 브레이크타임을 시간 지정 : interval값을 밀리미터로 변환.
        self.loss_recovery_interval: Optional[str] = (
            loss_recovery_interval if self.is_order_break else None
        )
        # TradingLog에 기록한다. 앞으로 어떻게 사용할지 고민중...
        self.test_mode: bool = True
        # 데이터를 pickle로 저장 및 로딩해야하며, 컨테이너화 하지 않는다.
        self.closing_sync_data: Optional[Dict[str, Dict[str, List[Any]]]] = None
        # self.kline_data: Optional[Dict[str,Dict[str,List[Any]]]] = None
        # 백테스트에 사용될 kline_data의 길이 지정(단위 : day)
        self.kline_period = kline_period
        self.ins_signal_analyzer = TradeSignalAnalyzer.AnalysisManager(
            back_test=self.test_mode
        )
        self.intervals = self.ins_signal_analyzer.base_config.intervals
        self.lookback_days = self.ins_signal_analyzer.base_config.lookback_days
        self.ins_backtest_data = TradeComputation.BacktestDataFactory(
            symbols=self.symbols,
            intervals=self.intervals,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.seed_money = seed_money
        self.ins_portfolio = TradeComputation.PortfolioManager(
            is_profit_preservation=self.is_profit_preservation,
            initial_balance=self.seed_money,
            market=self.market,
        )
        self.ins_trade_calculator = TradeComputation.TradeCalculator(
            max_held_symbols=self.max_held_symbols,
            requested_leverage=self.requested_leverage,
            instance=self.ins_portfolio,
            safe_asset_ratio=safe_asset_ratio,
        )
        self.constraint = TradeComputation.OrderConstraint(
            market=self.market,
            max_held_symbols=self.max_held_symbols,
            increase_type=increase_type,
            chance=self.allowed_loss_streak,
            instance=self.ins_portfolio,
            safety_ratio=safe_asset_ratio,
            loss_recovery_interval=self.loss_recovery_interval,
        )
        # self.symbol_map = None
        # self.interval_map = None
        self.closing_indices_data = None
        # self.target_run_interval = "map_1m"
        self.init_stop_rate = init_stop_rate

        # interval별 데이털르 저장하는 데이터셋
        self.interval_dataset = utils.DataContainer()

        #####신규 테스트
        self.kline_datsets = {}#DataStoreage.KlineData()
        self.ins_new_analysis = Analysis_new.AnalysisManager(self.kline_datsets)

        # ticker 관련 instance
        self.ins_ticker = TickerDataFetcher.FuturesTickers()
        self.comparison = comparison  # above : 이상, below : 이하
        self.absolute = absolute  # True : 비율 절대값, False : 비율 실제값
        self.value = value  # 거래대금 : 단위 USD
        self.target_percent = percent  # 변동 비율폭 : 음수 가능
        self.quote_type = quote_type  # 쌍거래 거래화폐

    # 저장데이터의 주소값을 확보한다.
    def __get_data_path(self):
        """
        1. 기능 : 백테스트에 적용될 kline_data의 주소값을 반환한다.
        2. 매개변수 : 해당없음.
        """
        # 파일명 - 속성명에 지정함.
        file_name = self.ins_backtest_data.kline_closing_sync_data
        # 폴더명 - 속성명에 지정함.
        folder_name = self.ins_backtest_data.storeage
        # 상위폴도명 - 함수로 확보
        base_directory = os.path.dirname(os.getcwd())
        # 주소 합성 - 상위폴더 + 폴더명 + 파일명
        path = os.path.join(base_directory, folder_name, file_name)
        # 주소 반환.
        return path

    # closing_sync_data의 유효성을 점검한다.
    def __validate_base_data(self):
        """
        1. 기능 : closing_sync_data의 유효성을 점검한다. symbol정보만 점검하며, interval데이터는 검토하지 않는다.
                (할 수 있응나 귀찮아서. [np.array화 하여 [0]index timestamp를 기준으로 전체 찾고 시작과 긑의 값 차이를 비교하여 interval 밀리초를 계산])
        2. 매개변수 : 해당없음.
        """
        # 속성에 데이터가 없다면,
        if not self.closing_sync_data:
            # 에러 발생
            raise ValueError(f"closing_sync_data가 비어있음.")
        #
        for symbol, _ in self.closing_sync_data.items():
            if not symbol in self.symbols:
                raise ValueError(f"closing_sync_data의 symbol정보 불일치: {symbol}")

    # 백테스트에 사용될 데이터를 로딩 또는 수신한다.
    async def get_base_data(self, is_save: bool = False):
        """
        1. 기능 : 백테스트에 사용될 데이터를 로딩 또는 수신한다.
        2. 매개변수
            1) is_save : 데이터를 저장할지 여부를 결정한다.
        """
        # 기존 데이터 로딩시
        if not self.is_download:
            # 파일 주소를 생성하고
            path = self.__get_data_path()
            # 해당 주소에 파일 존재여부를 점검
            # 파일 미존재시
            if not os.path.isfile(path):
                # 에러 발생시키고 중단
                raise ValueError(f"파일이 존재하지 않음: {path}")
            # 파일 존재시
            else:
                # 해당 파일을 불러온다.
                with open(path, "rb") as file:
                    self.closing_sync_data = pickle.load(file)
                    # return
        # 신규 다운로드 선택시
        else:
            # kline data를 수신한다.
            data = await self.ins_backtest_data.generate_kline_interval_data(
                save=is_save
            )
            # 데이터를 np.array타입으로 변환한다.
            # data_array = utils._convert_kline_data_array(data)
            # closing_sync 데이터를 생성 및 속성에 저장한다.
            self.closing_sync_data = self.ins_backtest_data.generate_kline_closing_sync(
                kline_data=data, save=is_save
            )

        self.closing_indices_data = self.ins_backtest_data.get_indices_data(
            closing_sync_data=self.closing_sync_data,
            lookback_days=self.kline_period,
        )

    # 현재 진행중인 포지션이 있다면, 최종 정보를 업데트한다.(단가, 현재타임스템프)
    # 업데이트 후 StopLoss 조건 성립시 포지션 종료 신호(True)를 반환한다.
    def update_trade_info(self, symbol: str, data):
        """
        1. 기능 : 진행중인 포지션이 있다면, 최종 데이터를 업데이트한다. 업데이트 후 포지션 종료 여부를 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) data : closing_sync_data 해당 index조회 값.
        """

        # 현재 가격
        price = data[-1][4]
        # 현재 타임스템프
        close_timestamp = data[-1][6]
        # 해당 symbol이 현재 진행중인 포지션이 있는지 확인한다.
        if f"{self.market}_{symbol}" in self.ins_portfolio.open_positions:
            # 현재 포지션 유지중이라면 데이터를 업데이트한다.
            # 포지션 종료신호를 반환한다. (True / False)
            return self.ins_portfolio.update_log_data(
                symbol=symbol, price=price, timestamp=close_timestamp
            )
        # 현재 포지션이 없다면,
        else:
            # 아무것도 하지 않고 포지션 종료 거절신호(False)를 반환한다.
            return False

    # position open전 주문 유효 점검 및 주문가능수량을 반환한다.
    async def __validate_open_signal(
        self, symbol: str, price: float, scenario_leverage: int
    ):  # , leverage: int):
        """
        1. 기능 : position open전 주문 유효 점검 및 주문 가능 수량을 계산 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) price : 진입가격
        3. 추가사항
            - 주문 전 open_position 사전 점검하기는 한다만...혹시 모르니 추가했다.
        """
        convert_to_symbol = f"{self.market}_{symbol}"
        if self.__validate_cloes_position(symbol=symbol):
            return False, 0, 0
        else:

            ### DEBUG START
            if self.ins_portfolio.secured_profit > 0:
                total_balance = (
                    self.ins_portfolio.total_wallet_balance
                    - self.ins_portfolio.secured_profit
                )
            elif self.ins_portfolio.secured_profit <= 0:
                total_balance = self.ins_portfolio.total_wallet_balance
            ### DEBUG END

            ### ORIGINAL CODE
            # total_balance = self.ins_portfolio.total_wallet_balance
            conctraint = self.ins_trade_calculator.get_trade_reference_amount()
            order_amount = conctraint["maxTradeAmount"] / self.max_held_symbols

            # 주문 신호 발생기
            status, quantity, leverage = (
                await self.ins_trade_calculator.get_order_params(
                    trading_symbol=symbol,  # 타겟 심볼
                    order_amount=order_amount,  # 최대 거래 가능 금액 반영
                    scenario_leverage=scenario_leverage,
                )
            )

            leverage = int(leverage)

            # DEBUG
            margin_ = (quantity / leverage) * price
            is_cash_margin = self.ins_portfolio.available_balance > margin_
            is_trade_count = self.ins_portfolio.number_of_stocks < self.max_held_symbols

            # print(self.ins_portfolio.available_balance)
            # print(margin_)

            if not status or not is_cash_margin or not is_trade_count:
                return False, 0, 0
            else:
                return True, quantity, leverage

    # symbol값 기준 포지션 유지여부 확인
    def __validate_cloes_position(self, symbol: str):
        """
        1. 기능 : symbol값 기준 포지션 유지여부를 확인한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        """

        if symbol in self.ins_portfolio.open_positions:
            return True
        else:
            return False

    # interval값을 활용하여 24hr 데이터를 생성한다. Ticker 필터행위 효과를 만든다.
    def __generate_dummy_24hr_tickers(self, symbol: str, data: np.ndarray):
        tickers_summary = []

        interval_duration = utils._get_interval_minutes("1d")

        idx_quote_volume = 7
        idx_price_change_percent = 4
        idx_close_time = 6

        end_timestamp = data[-1][idx_close_time]
        start_timestamp = end_timestamp - interval_duration

        # 데이터 필터링
        filtered_data = data[data[:, 0] <= start_timestamp]

        # 거래금액 계산
        quote_volume = np.sum(filtered_data[:, idx_quote_volume])

        # 증감률 계산
        start_price = filtered_data[0, idx_price_change_percent]
        last_price = filtered_data[-1, idx_price_change_percent]
        change_percent = (
            utils._calculate_percentage_change(start_price, last_price) * 100
        )

        # 결과값 리스트에 추가
        ticker_summary = {
            "symbol": symbol,
            "priceChangePercent": change_percent,
            "quoteVolume": quote_volume,
        }
        tickers_summary.append(ticker_summary)

        return tickers_summary

    # 조건에 맞는 symbol을 필터링한다. 실제 거래에서는 조건에 맞는 심볼만 수집했지만, 백테스트는 조건에 맞지 않으면 제외시킨다.abs
    # def select_symbols_backtest(self):

    # ticker 필터하여 리스트로 반환. << 조건에 맞는것만.
    async def validate_ticker_conditions(self, symbol: str, data: np.ndarray):
        dummy_24hr_tickers = self.__generate_dummy_24hr_tickers(
            symbol=symbol, data=data
        )
        # print(type(dummy_24hr_tickers))
        # print(dummy_24hr_tickers)
        # raise ValueError('stop')
        # 비동기 작업: 값을 기준으로 필터링된 티커와 변동률 기준 티커 가져오기
        above_value_tickers = await self.ins_ticker.get_tickers_above_value(
            target_value=self.value,
            comparison=self.comparison,
            dummy_data=dummy_24hr_tickers,
        )
        above_change_tickers = await self.ins_ticker.get_tickers_above_change(
            target_percent=self.target_percent,
            comparison=self.comparison,
            absolute=self.absolute,
            dummy_data=dummy_24hr_tickers,
        )

        common_filtered_tickers = utils._find_common_elements(
            above_value_tickers, above_change_tickers
        )
        # 병합 및 중복 제거
        # return list(set(above_value_tickers + above_change_tickers))
        return symbol in common_filtered_tickers

    # open 주문을 생성한다.
    async def active_open_position(
        self,
        symbol: str,
        price: float,
        position: int,
        start_timestamp: int,
        scenario_type: int,
        scenario_leverage: Optional[int] = None,
    ):
        """
        1. 기능 : position open 주문을 생성한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) price : 진입가격
            3) position : 1:long, 2:short
            4) start_timestamp : 시작 타임스템프
            5) secnario_type : intma() / 시나리오 종류
            6) scenario_leverage : 레버리지
        """

        # 주문전 유효성 검사 1
        if not self.constraint.can_open_more_trades():
            return
        # 주문전 유효성 검사 2
        is_open_signal, quantity, leverage = await self.__validate_open_signal(
            symbol=symbol, price=price, scenario_leverage=scenario_leverage
        )

        # debug

        # 주문 유혀성 검토 결과 False면,
        if not is_open_signal:
            # 함수 종료
            return

        # 브레이크 타임 설정시
        if self.is_order_break:
            # 기존 거래내역을 검토해서 브레이크 타임 적용여부 검토

            self.constraint.update_trading_data()  #
            is_loss_scnario = self.constraint.validate_failed_scenario(
                symbol=symbol,
                scenario=scenario_type,
                current_timestamp=start_timestamp,
            )
            # 브레이크 타임 해당될경우
            if not is_loss_scnario:
                # 함수 종료
                return

        # 브레이크 타임 검토 후 미적용시 주문정보 생성.
        log_data = TradeComputation.TradingLog(
            symbol=f"{self.market}_{symbol}",
            start_timestamp=start_timestamp,
            entry_price=price,
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
            use_scale_stop=self.is_use_scale_stop,
        )
        # 주문 정보를 추가
        self.ins_portfolio.add_log_data(log_data=log_data)

    # 포지션 종료를 위한 함수.
    def active_close_position(self, symbol: str):
        # 포지션 종료 신호를 수신해도 symbol값 기준으로 position 유효성 검토한다.
        convert_to_symbol = f"{self.market}_{symbol}"
        if self.__validate_cloes_position(symbol=convert_to_symbol):
            # 유효성 확인시 해당 내용을 제거한다.
            self.ins_portfolio.remove_order_data(symbol=symbol)

    # 백테스트 시작시 현재 설정정보를 출력한다.
    def start_masage(self):
        """
        1. 기능 : 백테스트 시작시 현재 설정 정보를 출력한다.
        2. 매개변수 : 해당없음.
        """
        header = "=" * 100
        print(f"\n {header}\n")
        print(f"    ***-=-=-<< BACK TESTING >>-=-=-***\n")
        print(f"    1.  StartDate   : {self.start_date}")
        print(f"    2.  EndDate     : {self.end_date}")
        print(f"    3.  Symbols     : {self.symbols}")
        print(f"    4.  SeedMoney   : {self.seed_money:,.1f} USDT")
        print(f"    5.  leverage    : {self.requested_leverage}x")
        print(f"    6.  Intervals   : {self.intervals}")
        print(f"    7.  ScaleStop   : {self.is_use_scale_stop}")
        print(f"    8.  StopRate    : {self.stop_loss_rate*100:.2f} %")
        print(f"    9.  AdjTimer    : {self.is_dynamic_adjustment}")
        print(f"    10. OrderBreak  : {self.is_order_break}")
        print(f"    11. 24hrValue   : {self.value:,.0f} USDT")
        print(f"    12. 24hrPercent : {self.target_percent*100:.1f} %")
        print(f"    13. Comparison  : {self.comparison}")
        print(f"    14. Absolute    : {self.absolute}")
        print(f"\n {header}\n")
        print(
            "     DateTime       Trading  trade_count   PnL_Ratio       Gross_PnL       Profit_Preservation"
        )

    # 백테스트 실행.
    async def run(self):
        """
        1. 기능 : 각종 기능을 집합하여 시계 데이터 loop 생성하고 가상의 거래를 진행한다.
        2. 매개변수 : 해당없음.
        """
        await self.get_base_data(is_save=True)
        self.__validate_base_data()
        # await self.get_indices_data(self.closing_sync_data)
        self.start_masage()

        # 최소단위 interval값 기준 데이터 길이를 확보한다.
        data_length = len(self.closing_sync_data[self.symbols[0]][self.intervals[0]])

        # Loop 시작
        for index in range(data_length):
            # print(index)
            price = {}
            for symbol in self.symbols:
                self.kline_datsets[symbol] = DataStoreage.KlineData()
                timestamp_min = []
                for interval in self.intervals:
                    select_indices_ = self.closing_indices_data.get_data(
                        f"interval_{interval}"
                    )[index]
                    
                    ### 가장 최대 interval값을 기준으로 index최대값도달 시 검토 필요하다.
                    ### 최대값 도달 전에 검토시 데이터 외곡 발생한다.
                    if len(select_indices_) <=960:
                        flag = False
                        continue
                    
                    select_data = self.closing_sync_data[symbol][interval][select_indices_]                 
                    # if interval == "3m":
                    #     import pickle
                    #     print(select_data)
                    #     with open('data.pickle', 'wb') as file:
                    #         pickle.dump(select_data, file)
                    self.kline_datsets[symbol].set_data(list(select_data))
                    #     raise ValueError(f'중간점검')
                        # print(select_data)
                    if interval == self.intervals[0]:
                        update_and_stop_signal = self.update_trade_info(
                            symbol=symbol, data=select_data
                        )

                        if update_and_stop_signal:
                            self.active_close_position(symbol=symbol)
                        end_timestamp = int(select_data[-1, 6])
                        price[symbol] = select_data[-1, 4]
                        ### trane 출력 ###
                        date = utils._convert_to_datetime(end_timestamp)
                        utils._std_print(
                            f"{date}    {self.ins_portfolio.number_of_stocks}         {self.ins_portfolio.trade_count:,.0f}          {self.ins_portfolio.profit_loss_ratio*100:,.2f} %             {self.ins_portfolio.profit_loss:,.2f}             {self.ins_portfolio.secured_profit:,.2f}"
                        )

                        ### DEBUG
                        if self.ins_portfolio.profit_loss_ratio <= -0.95:
                            raise ValueError(f"원금 청산")
                        # if self.ins_portfolio.trade_count > 5:
                        #     raise ValueError(f'중간점검')
                    # kline_data[symbol][interval] = select_data
                    flag = True
                    
            if flag:
                self.ins_new_analysis.run()

                for position in ['buy', 'sell']:
                    signal = getattr(self.ins_new_analysis, f'success_{position}_signal')
                    if signal:
                        for symbol, data in signal.items():
                            await self.active_open_position(
                                symbol=symbol,
                                price=price[symbol],
                                position=data[1],
                                scenario_leverage=20,
                                start_timestamp=end_timestamp,
                                scenario_type=data[2],
                            )
                            # ...
                            # print(f'{signal} - {data}')

            self.ins_new_analysis.reset_signal()

            # await self.active_open_position(
            #     symbol=trade_signal[1],
            #     price=price,
            #     position=trade_signal[2],
            #     scenario_leverage=trade_signal[4],
            #     start_timestamp=current_timestamp,
            #     scenario_type=trade_signal[3],
            # )

        # self.ins_portfolio.export_trading_logs()
        # print("\n\nEND")

        # end_step = len(self.closing_indices_data.get_data(f'map_{self.intervals[-1]}'))

        # ### 데이터 타임루프 시작 ###
        # for idx, data in enumerate(
        #     self.closing_indices_data.get_data(self.target_run_interval)
        # ):
        #     if idx <= self.start_step:  # or idx >= end_step:
        #         # utils._std_print(idx)
        #         continue
        #     # interval 기준이므로 end_timestamp는 for문 이탈시 가장 큰 값을 가진다.
        #     # list에 값을 추가하여 for문 종료시 min값(1분) 확보한다.
        #     # timestamp_min값을 초기화 한다.
        #     timestamp_min = []

        #     # 원본 코드
        #     ### 분석에 사용될 데이터셋 초기화 ###
        #     self.interval_dataset.clear_all_data()
        #     # dummy_data = {}
        #     """
        #     동작원리 고민중...

        #     np.array변환을 한번에 하기 위하여 다차원 list데이터가 필요하다.
        #         변수1 >> 데이터 수신속도에 따라서 같은 interval이라 하더라도 데이터의 길이가 다를경우 np.array처리시 오류발생.

        #     순서는 interval loop
        #         >> symbol.interval_data
        #     """

        #     for interval in self.intervals:
        #         maps_ = self.closing_indices_data.get_data(f"map_{interval}")[idx]
        #         data = self.closing_indices_data.get_data(f"interval_{interval}")[maps_]
        #         # print(idx)
        #         # print(maps_)
        #         # print(data)
        #         # raise ValueError(f'{len(data)}')

        #         ### 데이터셋으로 저장한다 ###
        #         # TEST 진행시 첫번째가 왜 symols[0]이 아닌지 의문 발생시 위의 self.start_step이 있음을 인지할 것.
        #         symbol = self.symbols[maps_[0]]
        #         price = data[-1][4]
        #         end_timestamp = data[-1][6]

        #         timestamp_min.append(end_timestamp)

        #         ### 업데이트 및 이탈 검토 ###
        #         if interval == self.intervals[0]:
        #             # 현재 정보 업데이트와 동시에 stop signal 정보를 조회한다.
        #             update_and_stop_signal = self.update_trade_info(
        #                 symbol=symbol, data=data
        #             )
        #             if update_and_stop_signal:
        #                 self.active_close_position(symbol=symbol)
        #             ### trane 출력 ###
        #             date = utils._convert_to_datetime(end_timestamp)
        #             utils._std_print(
        #                 f"{date}    {self.ins_portfolio.number_of_stocks}         {self.ins_portfolio.trade_count:,.0f}          {self.ins_portfolio.profit_loss_ratio*100:,.2f} %         {self.ins_portfolio.profit_loss:,.2f}"
        #             )
        #             ### 포지션 보유시 연산 pass ###
        #             if self.ins_portfolio.validate_open_position(symbol):
        #                 continue

        #         self.interval_dataset.set_data(
        #             data_name=f"interval_{interval}", data=data
        #         )
        #         # 티켓 분류 조건 부합여부를 점검한다.
        #         # 조건에 맞지 않으면 루프를 지나친다.

        #         # 원본 코드
        #         ### interval data를 데이터셋으로 구성 ###
        #         # dummy_data[interval] = data
        #         # print(data)

        #     if not await self.validate_ticker_conditions(
        #         symbol=symbol, data=data
        #     ) or self.ins_portfolio.validate_open_position(symbol):
        #         continue

        #     # 원본 코드
        #     ### 분석 진행을 위해 데이터셋을 Analysis로 이동###
        #     self.ins_signal_analyzer.data_container = self.interval_dataset
        #     # self.ins_signal_analyzer.dummy_d = dummy_data

        #     trade_signal = self.ins_signal_analyzer.scenario_run()
        #     if not trade_signal[0]:
        #         continue

        #     current_timestamp = min(timestamp_min)

        #     await self.active_open_position(
        #         symbol=symbol,
        #         price=price,
        #         position=trade_signal[1],
        #         leverage=self.requested_leverage,
        #         start_timestamp=current_timestamp,
        #         scenario_type=trade_signal[2],
        #     )

        print("\n\nEND")


if __name__ == "__main__":
    symbols = [
        "btcusdt",
        "xrpusdt",
        "adausdt",
        "linkusdt",
        "sandusdt",
        "bnbusdt",
        "dogeusdt",
        "solusdt",
        "ethusdt",
    ]  # 확인하고자 하는 심볼 정보
    # intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    ### 수신받을 데이터의 기간 ###
    start_date = "2024-11-1 09:00:00"  # 시작 시간
    end_date = "2025-1-6 08:59:59"  # 종료 시간
    safety_balance_ratio = 0.4  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.65  # 스톱 로스 비율
    is_download = False  # 기존 데이터로 할경우 False, 신규 다운로드 True
    is_dynamic_adjustment = (
        True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    )
    dynamic_adjustment_rate = 0.0007  # 시간 흐름에 따른 시작가 변동율
    dynamic_adjustment_interval = "3m"  # 변동율 반영 스텝
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 350  # 시작금액
    leverage = 15  # 레버리지
    init_stop_rate = 0.035  # 시작 손절가
    is_order_break = True  # 반복 손실 발생시 주문 거절여부
    allowed_loss_streak = 2  # 반복 손실 발생 유예횟수
    loss_recovery_interval = "4h"  # 반복 손실 시간 범위
    max_held_symbols = 4  # 동시 거래 가능 수량
    is_profit_preservation = True  # 수익보존여부
    ### Ticker Setting Option ###
    comparison = "above"  # above : 이상, below : 이하
    absolute = True  # True : 비율 절대값, False : 비율 실제값
    value = 35_000_000  # 거래대금 : 단위 USD
    target_percent = 0.035  # 변동 비율폭 : 음수 가능
    quote_type = "usdt"  # 쌍거래 거래화폐

    ins_backtest = BackTesterManager(
        symbols=symbols,
        max_held_symbols=max_held_symbols,
        start_date=start_date,
        end_date=end_date,
        safe_asset_ratio=safety_balance_ratio,
        stop_loss_rate=stop_loss_rate,
        is_download=is_download,
        is_dynamic_adjustment=is_dynamic_adjustment,
        dynamic_adjustment_rate=dynamic_adjustment_rate,
        is_use_scale_stop=use_scale_stop,
        seed_money=seed_money,
        requested_leverage=leverage,
        init_stop_rate=init_stop_rate,
        dynamic_adjustment_interval=dynamic_adjustment_interval,
        is_order_break=is_order_break,
        allowed_loss_streak=allowed_loss_streak,
        loss_recovery_interval=loss_recovery_interval,
        comparison=comparison,
        absolute=absolute,
        value=value,
        percent=target_percent,
        quote_type=quote_type,
        is_profit_preservation=is_profit_preservation,
    )

    asyncio.run(ins_backtest.run())
    analyze_statistics = TradeComputation.ResultEvaluator(ins_backtest.ins_portfolio)
    analyze_statistics.run_analysis()
