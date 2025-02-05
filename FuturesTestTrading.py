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
import Futures
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
        self.closing_indices_data: Optional[DataStoreage.DataContainer] = None
        self.current_timestamp: int = 0
        
        
        self.min_qty:Dict[str, float] = {}
        self.step_size:Dict[str, float] = {}
        self.notional:Dict[str, float] = {}
        
        self.api_max_leverage:Dict[str, int] = {}
        
        
    async def set_symbols_data(self):
        exchange_info_data = await Futures.INS_MARKET_FUTURES.fetch_exchange_info()
        for symbol in self.symbols:
            extract_symbols_data = Futures.extract_exchange_symbols_info(symbol, exchange_info_data)
            self.min_qty[symbol] = float(extract_symbols_data['minQty'])
            self.step_size[symbol] = float(extract_symbols_data['stepSize'])
            self.notional[symbol] = float(extract_symbols_data['notional'])
            brackets = await Futures.INS_CLIENT_FUTURES.fetch_leverage_brackets(symbol)
            self.api_max_leverage[symbol] = Futures.extract_max_leverage(brackets)
            
            
    def calculate_position_size(self, symbol:str, mark_price:float, leverage:int, balance:float):
        step_size = self.step_size[symbol]
        min_qty = self.min_qty[symbol]
        notional = self.notional[symbol]
        
        max_position_size = Futures.calculate_max_position_size(mark_price, leverage, step_size, balance)
        min_position_size = Futures.calculate_min_position_size(mark_price, min_qty, step_size, notional)
        
        if max_position_size > min_position_size:
            return max_position_size
        else:
            return 0
    
    def _check_hedge(self, symbol:str, position:Union[int, str]):
        b_position = self.ins_wallet.check_position_status(symbol, 1)
        s_position = self.ins_wallet.check_position_status(symbol, 2)
        if position == 1 and s_position:
            return True
        elif position == 2 and b_position:
            return True
        else:
            return False

    
    def create_trading_log(self, signal:List[int], position_size:float, hedge_trade:bool):
        """
        승인이 났다는 가정하에 진행하는 건임.
        """
        symbol = signal[0]
        position = signal[1]
        
        index_close_price = 4
        index_target_data = -1
        price = self.kline_datasets[symbol].get_data(self.intervals[0])[index_target_data][index_close_price]
        
        leverage = ConfigSetting.OrderConfig.reference_leverage.value
        balance = ConfigSetting.OrderConfig.order_allocation_amount.value
        
        strategy_no = signal[2]

        imr = Futures.calculate_imr(leverage)
        init_margin = Futures.calculate_initial_margin(position_size, price, imr)
        
        create_log = DataStoreage.TradingLog(
            symbol=symbol,
            position=position,
            position_size=position_size,
            hedge_enable=hedge_trade,
            open_price=price,
            high_price=price,
            low_price=price,
            close_price=price,
            strategy_no=strategy_no,
            start_timestamp=int(self.current_timestamp),
            end_timestamp=int(self.current_timestamp),
            initial_stop_rate=ConfigSetting.StopLossConfig.initial_stop_loss_rate.value,
            initial_margin=init_margin
        )
        return create_log
    
    def open_order(signal:List[int]):
        
    
    
    self.calculate_position_size(symbol, price, leverage, balance)
    hedge_trade = self._check_hedge(symbol, position)