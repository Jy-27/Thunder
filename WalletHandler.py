from typing import List, Dict, Optional, Any, Union
from DataStoreage import *
from ConfigSetting import SystemConfig, InitialSetup, SymbolConfig
import os
import utils
import asyncio
import nest_asyncio
# import TradeClient
import importlib
from DataStoreage import TradingLog

nest_asyncio.apply()


class WalletManager:
    def __init__(self, initial_balance:float = 1_000):
        self.trade_history: List[Dict[str, Any]] = []
        self.closed_positions: Dict[str, List[List[Any]]] = {}
        self.open_positions: Dict[str, List[List[Any]]] = {}
        self.number_of_stocks: int = 0
        self.initial_balance: float = initial_balance  # 초기 자산
        self.total_wallet_balance: float = 0  # 총 평가 자산
        self.active_value: float = 0  # 거래 중 자산 가치
        self.available_balance: float = 0  # 사용 가능한 예수금
        self.profit_loss: float = 0  # 손익 금액
        self.profit_loss_ratio: float = 0  # 손익률
        self.trade_count: int = 0  # 총 체결 횟수
        
        ### system setting
        self.__log_data: List[TradingLog] = {1:{}, 2:{}}

    async def init_setting(self):
        """ 초기 설정을 비동기적으로 수행 """
        
        # 시스템 설정 초기화
        InitialSetup.initialize()
        is_test_mode = InitialSetup.mode  # 모드 상태 저장

        # 파일 경로 설정
        file_name = SystemConfig.test_trade_history.value if is_test_mode else SystemConfig.live_trade_history.value
        path = os.path.join(
            SystemConfig.parent_folder_path.value,
            SystemConfig.data_folder_name.value,
            file_name
        )

        # 거래 기록 불러오기
        if os.path.isfile(path):
            trade_history = utils._load_json(path)
            self.closed_positions.extend(trade.value for trade in trade_history)

        # 초기 지갑 잔고 설정
        if is_test_mode:
            balance = self.initial_balance
        else:
            ins_client_class = utils._get_import('TradeClient', f'{SymbolConfig.market_type.value}Client')
            balance = await ins_client_class().get_total_wallet_balance()

        self.initial_balance = self.total_wallet_balance = self.available_balance = balance

            