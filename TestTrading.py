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
        self.closing_indices_data: Optional[DataStoreage.DataContainer] = None
        self.current_timestamp: int = 0
        
        
        self.max_qty = {}
        self.step_size = {}
        self.notional = {}
        
    