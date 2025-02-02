import ConfigSetting
import WalletHandler
import asyncio
import numpy as np
import utils
import BackTestDataFactory
import os
import pickle
import DataStoreage
import Analysis_new
import datetime
import TradeClient
from typing import Optional, Dict, List, Union, Any


class BackTestManager:
    def __init__(self):
        # CONFIG SETTING
        # 분석에 쓰일 데이터 기간(day)
        self.kline_peiod: int = (
            ConfigSetting.SystemConfig.data_analysis_window_days.value
        )
        # 마켓 정보(큰 의미 없음.)
        self.market: str = ConfigSetting.SymbolConfig.market_type.value
        # 반복손실 발생 주문 거부
        self.rejetc_loss_orders_enabled: bool = (
            ConfigSetting.SafetyConfig.reject_repeated_loss_orders_enabled.value
        )
        # 연속 손실 기준 시간
        self.loss_reset_interval: str = (
            ConfigSetting.SafetyConfig.loss_streak_reset_interval.value
        )
        # 허용된 연속 손실 횟수(symbol기준)
        self.max_allowed_loss_streak: int = (
            ConfigSetting.SafetyConfig.max_allowed_loss_streak.value
        )
        # 허용된 연속 손실 횟수(전략기준)
        self.max_strategy_loss_streak: int = (
            ConfigSetting.SafetyConfig.max_strategy_loss_streak.value
        )
        # 수익 보존 가능 활성화 여부
        self.profit_preservation_enabled: bool = (
            ConfigSetting.SafetyConfig.profit_preservation_enabled.value
        )
        # 수익 보존 금액 기준
        self.profit_preservation_amount: float = (
            ConfigSetting.SafetyConfig.profit_preservation_amount.value
        )
        # 게좌 안전 비율(시스템 스탑)
        self.account_safety_ratio: float = (
            ConfigSetting.SafetyConfig.account_safety_ratio.value
        )
        # 헤지거래 설정
        self.hedge_trading_enabled: bool = (
            ConfigSetting.OrderConfig.hedge_trading_enabled.value
        )
        # 최대 레버리지
        self.max_leverage: int = ConfigSetting.OrderConfig.max_leverage.value
        # 최소 레버리지
        self.reference_leverage: Union[float, int] = (
            ConfigSetting.OrderConfig.reference_leverage.value
        )
        # 회당 주문 가능 금액 비율
        self.order_allocation_ratio: Optional[float] = (
            ConfigSetting.OrderConfig.order_allocation_ratio.value
        )
        # 회당 주문 가능 금액
        self.order_allocation_amount: Optional[float] = (
            ConfigSetting.OrderConfig.order_allocation_amount.value
        )
        # 포지션 동시보유가능 수
        self.max_held_symbols: int = (
            ConfigSetting.OrderConfig.max_concurrent_positions.value
        )
        # 손절비율 조정 활성화
        self.scaled_stop_loss_enabled: bool = (
            ConfigSetting.StopLossConfig.scaled_stop_loss_enabled.value
        )
        # 손절 비율
        self.stop_loss_threshold: float = (
            ConfigSetting.StopLossConfig.stop_loss_threshold.value
        )
        # 포지션 반대 캔들 영향 활성화
        self.negative_candle_effect_enabled: bool = (
            ConfigSetting.StopLossConfig.negative_candle_effect_enabled.value
        )
        # 손절비율 가중치 반영 활성화
        self.dynamic_stop_loss_enabled: bool = (
            ConfigSetting.StopLossConfig.dynamic_stop_loss_enabled.value
        )
        # 가중치 비율
        self.adjustment_rate: float = ConfigSetting.StopLossConfig.adjustment_rate.value
        # 가중치 적용 스텝
        self.adjustment_interval: str = (
            ConfigSetting.StopLossConfig.adjustment_interval.value
        )
        # 초기 스탑로스 비율
        self.init_stop_rate: float = (
            ConfigSetting.StopLossConfig.initial_stop_loss_rate.value
        )
        # 심볼정보
        self.symbols: list[str] = ConfigSetting.TestConfig.test_symbols.value
        # 초기자본금
        self.seed_money: Union[float, int] = ConfigSetting.TestConfig.seed_funds.value
        # 시작날짜
        self.start_date: str = ConfigSetting.TestConfig.start_datetime.value
        # 종료날짜
        self.end_date: str = ConfigSetting.TestConfig.end_datetime.value
        # 신규 다운로드 여부
        self.download_enabled: bool = ConfigSetting.TestConfig.download_new_data.value

        # config 초기 세팅
        ConfigSetting.InitialSetup.initialize()
        asyncio.run(ConfigSetting.run())

        # kline_data 처리
        # self.kline_datasets:DataStoreage.KlineData = {symbol: DataStoreage.KlineData() for symbol in self.symbols}
        self.kline_datasets: Dict[str, DataStoreage.KlineData] = {
            symbol: DataStoreage.KlineData() for symbol in self.symbols
        }

        # INSTANCE SETTING
        self.ins_analysis = Analysis_new.AnalysisManager(
            kline_datasets=self.kline_datasets
        )
        self.ins_client_futures = TradeClient.FuturesClient()
        self.ins_client_stpo = TradeClient.SpotClient()
        
        self.ins_wallet: WalletHandler.WalletManager = WalletHandler.WalletManager(
            current_timestamp=utils._convert_to_timestamp_ms(ConfigSetting.TestConfig.start_datetime.value),
            initial_balance=ConfigSetting.TestConfig.seed_funds.value,
            start_ago_hr=ConfigSetting.SystemConfig.trade_history_range.value,
        )
        self.ins_data_factory: BackTestDataFactory.FactoryManager = (
            BackTestDataFactory.FactoryManager()
        )

        self.intervals: List[str] = self.ins_data_factory.intervals

        # SIMULATE DATA
        self.closing_sync_data: Dict[str, Dict[str, np.ndarray]] = {}
        self.closing_indices_data: Optional[utils.DataContainer] = None
        self.current_timestamp: int = 0
        
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
        print(
            f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing_sync_data 검토완료."
        )

    async def get_simulate_data(self):
        """
        시뮬레이션에 적용할 데이터를 확보한다. kline_data, closing_sync_data, indices데이터 등을 수신 및 생성한다.
        
            1. 기능: 백테스트에 사용될 데이터를 확보.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음(즉시 속성값에 저장)
        """
        if self.download_enabled:
            kline_data = await self.ins_data_factory.generate_kline_interval_data()
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: 데이터 수신 완료"
            )
            self.closing_sync_data = self.ins_data_factory.generate_kline_closing_sync(
                kline_data=kline_data, save=True
            )
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing sync 데이터 생성 완료"
            )
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing indices 데이터 생성 시작"
            )
            self.closing_indices_data = self.ins_data_factory.get_indices_data(
                closing_sync_data=self.closing_sync_data, lookback_days=self.kline_peiod
            )
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing indices 데이터 생성 완료"
            )
        elif not self.download_enabled:
            path = ConfigSetting.SystemConfig.path_closing_sync_data.value
            if not os.path.isfile(path):
                raise ValueError(f"파일이 존재하지 않음: {path}")

            with open(path, "rb") as file:
                self.closing_sync_data = pickle.load(file)
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing_sync_data 로드 완료"
            )
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing indices 데이터 생성 시작"
            )
            self.closing_indices_data = self.ins_data_factory.get_indices_data(
                closing_sync_data=self.closing_sync_data, lookback_days=self.kline_peiod
            )
            print(
                f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: closing_indices_data 생성 완료"
            )
    async def __data_monitor(self, symbol:str, interval:str, sync_data:np.ndarray):
        if interval == self.intervals[0]:
            close_signal = await self.ins_wallet.update_position(symbol=symbol, kline_data=sync_data)

            # 종료 신호가 존재하면
            if close_signal:
                symbol:str = close_signal[0].split("_")[0]  # BTCUSDT의 형태
                position:str = close_signal[0].split("_")[1]    #1 or 2의 형태
                # 포지션 종료한다.
                await self.ins_wallet.remove_position(symbol=symbol, position=position)
            self.current_timestamp = sync_data[-1, 6]# + 32_400_000
            date = utils._convert_to_datetime(self.current_timestamp)
            utils._std_print(
                f"{date}    {self.ins_wallet.trading_count}         {self.ins_wallet.total_trade_count:,.0f}          {self.ins_wallet.profit_loss_ratio*100:,.2f} %             {self.ins_wallet.profit_loss:,.2f}             {self.ins_wallet.profit_preservation_balance:,.2f}"
                )
    
    def __open_position_validate(self, signal:List[Any]) -> bool:
        """
        포지션 오픈전 계좌상태를 점검하고 ConfigSetting에 위배여부를 확인한다.
        위배 사항 없을경우 진입입을 허용한다.
        
            1. 기능: 포지션 진입여부를 사전 검토
            2. 매개변수: 분석결과 시그널
            3. 반환값: bool타입의 참 or 거짓
        """
        symbol = signal[0]
        status = signal[1]
        position = signal[2]
        strategy = signal[3]
        score = signal[4]
        opp_Position = 2 if position == 1 else 1
                
        ##스폿 거래에 대한 대비는 아직 안했음.
        open_position:np.ndarray = np.array(self.ins_wallet.open_positions, float)

        if open_position.ndim == 1:
            open_position = open_position.reshape(-1, 1)
                    
        convert_to_decimal = utils._text_to_decimal(symbol)
        if open_position.size > 0:
            # 헤지거래 True일 경우        
            if ConfigSetting.OrderConfig.hedge_trading_enabled.value:
                # 심볼값으로 동일 포지션 보유 여부 index 확보
                condition = np.where((open_position[:,0]==convert_to_decimal)&
                                    (open_position[:,4]==position))[0]
            # 헤지거래 False일 경우
            else:
                # 심볼값으로 포지션 보유 여부 index 확보
                condition = np.where(open_position[:,0]==convert_to_decimal)[0]
            # 만약 포지션 보유가 있으면 fail
            if len(condition)>0:
                return False

            # 동시 거래가능 횟수 제한.
            if len(open_position) <= ConfigSetting.OrderConfig.max_concurrent_positions.value:
                return False

        # interval 값에 대한 타임스템프 확보
        ms_seconds = utils._get_interval_ms_seconds(ConfigSetting.SafetyConfig.loss_streak_reset_interval.value)
        # 현재 타임스템프 시간 확보
        current_timestamp = self.current_timestamp
        # 시작 타임스템프 확보
        target_timestamp = current_timestamp - ms_seconds

        closed_position:np.ndarray = np.array(self.ins_wallet.closed_positions, float)
        if closed_position.ndim == 1:
            closed_position = closed_position.reshape(-1, 1)

        if closed_position.size > 0:
            # 심볼 동일 시나리오 손실 횟수
            loss_symbol_condition = np.where((closed_position[:, 0]==convert_to_decimal)&# 동일 심볼
                                            (closed_position[:,1] >= target_timestamp)&# 타임스템프 이상
                                            (closed_position[:, 6]<=0)&# pnl손실 여부
                                            (closed_position[:, 2]==strategy))[0]# 전략번호
            if len(loss_symbol_condition) >= ConfigSetting.SafetyConfig.max_allowed_loss_streak.value:
                return False
            
            # 시나리오 제한 횟수
            loss_strategy_condition = np.where((closed_position[:,1]>= target_timestamp)&
                                            (closed_position[:,2]==strategy))[0]
            if len(loss_strategy_condition) >= ConfigSetting.SafetyConfig.max_strategy_loss_streak.value:
                return False
        return True

    async def __leverage_validate(self, symbol:str, target_leverage:int) -> int:
        api_max_leverage = await self.ins_client_futures.get_max_leverage(symbol)
        config_max_leverage = min(ConfigSetting.OrderConfig.max_leverage.value, target_leverage)
        config_min_leverage = max(ConfigSetting.OrderConfig.min_leverage.value, target_leverage)
        return min(api_max_leverage, config_max_leverage, config_min_leverage)

    async def __quantity_validate(self, symbol:str, leverage:int, balance:float) -> list[str, float]:
        # print(f'symbol : {symbol}')
        api_min_quantity = await self.ins_client_futures.get_min_trade_quantity(symbol)
        # print(f'min Qty: {api_min_quantity}')
        api_max_quantity = await self.ins_client_futures.get_max_trade_quantity(symbol=symbol, leverage=leverage, balance=balance)
        # print(f'max Qty: {api_max_quantity}')
        is_quantity = api_min_quantity <= api_max_quantity
        return [is_quantity, max(api_max_quantity, api_min_quantity)]

    def __available_balance_validate(self):
        use_balance = self.ins_wallet.total_wallet_balance * (1-ConfigSetting.SafetyConfig.account_safety_ratio.value)
        return use_balance > ConfigSetting.OrderConfig.order_allocation_amount.value


    async def run(self):
        await self.get_simulate_data()
        self.__validate_base_data()

        # 데이터 길이를 계산한다.
        data_length = len(self.closing_sync_data[self.symbols[0]][self.intervals[0]])

        # loop 시작
        for index in range(data_length):
            # 데이터 셋을 초기화 한다.
            if index < 960:
                continue
            # 분석자료 초기화
            self.ins_analysis.reset_signal()
            # symbol 값 순환
            for symbol in self.symbols:
                # 데이터 자료 초기화
                self.kline_datasets[symbol].reset_data()
                # interval 값 순환
                for interval in self.intervals:
                    # index 데이터를 확보한다.
                    indices = self.closing_indices_data.get_data(
                        f"interval_{interval}"
                    )[index]
                    
                    # sync 데이터에 index값 반영하여 분류
                    sync_data = self.closing_sync_data[symbol][interval][indices]
                    # 리스트 형태로 전환 후 데이터를 함수에 반영한다.
                    ### !!! ###
                    # live 트레이딩때는 정기적으로 kline을 업데이트하고 실시간 수신되는 데이터를
                    # update_data 함수를 사용해 누적 추가한다.
                    self.kline_datasets[symbol].set_data(list(sync_data))

                    await self.__data_monitor(symbol=symbol, interval=interval, sync_data=sync_data)
                        
            # 시그널 정보 확보
            signals = self.ins_analysis.run()


            if signals:
                # print(signals)
                for signal in signals:
                    # 조건 사항 검토 1 레버리지
                    get_leverage = await self.__leverage_validate(symbol=signal[0], target_leverage=ConfigSetting.OrderConfig.min_leverage.value)
                    # 조건 사항 검토 2 제한된 주문금액으로 포지션 진입가능 수량 검토
                    get_quantity = await self.__quantity_validate(symbol=signal[0], leverage=get_leverage, balance=ConfigSetting.OrderConfig.order_allocation_amount.value)
                    # 조건 사항 검토 3 예수금 보유 검토
                    is_available_balance = self.__available_balance_validate()
                    # 조건 사항 검토 4 현재 포지션 중복 또는 헤지거래 가능여부 검토
                    is_validate = self.__open_position_validate(signal=signal)
                    
                    # print(f'{self.__class__.__name__}')
                    # print(f'1. leverage :{get_leverage}')
                    # print(f'2. quantity :{type(get_quantity[1])}')
                    # print(f'2. quantity :{get_quantity[1]}')
                    # print(f'3. available :{is_available_balance}')
                    # print(f'4. open :{is_validate}')
                    
                    # raise ValueError('중간점검')
                    
                    
                    if is_validate and is_available_balance and get_quantity[0]:
                        trade_log = DataStoreage.TradingLog(
                            symbol=signal[0],
                            position=signal[2],
                            quantity=get_quantity[1],
                            hedge_enable=ConfigSetting.OrderConfig.hedge_trading_enabled.value,
                            leverage=get_leverage,
                            open_price=self.kline_datasets[signal[0]].get_data('1m')[-1][4],
                            high_price=self.kline_datasets[signal[0]].get_data('1m')[-1][4],
                            low_price=self.kline_datasets[signal[0]].get_data('1m')[-1][4],
                            close_price=self.kline_datasets[signal[0]].get_data('1m')[-1][4],
                            strategy_no=signal[3],
                            start_timestamp=int(self.current_timestamp),
                            end_timestamp=int(self.current_timestamp),
                            initial_stop_rate=ConfigSetting.StopLossConfig.initial_stop_loss_rate.value
                        )
                        
                        await self.ins_wallet.add_position(trade_log)
                        
                    # 몇가지 검증을 거친다.



if __name__ == "__main__":
    from pprint import pprint

    obj = BackTestManager()
    asyncio.run(obj.run())
    # print(obj.closing_indices_data.get_data('interval_5m')[1004])
    # pprint(vars(obj))
