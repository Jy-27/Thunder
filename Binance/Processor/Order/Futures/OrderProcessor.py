from abc import ABC, abstractmethod
from typing import Dict
import os

import sys
sys.path.append(os.path.abspath("../../../"))
import Utils.TradingUtils as futures_utils


class Processor(ABC):
    TEST_MODE:bool
    
    def __init__(self, test_mode:bool):
        TEST_MODE:bool = test_mode


    @classmethod
    def position_size(cls, symbol:str, mark_price:float, leverage:int, balance:float) -> float:
        """
        ⭕️ 매개 변수 조건에 의한 진입 가능한 포지션 수량을 계산한다.

        Args:
            symbol (str): 'BTCUSDT'
            mark_price (float): 진입 가격
            leverage (int): 레버리지
            balance (float): 진입 금액
            test_mode (bool): 테스트 모드 여부

        Notes:
            반환값이 0일경우 최소 진입 수량조차 미달됨(예수금 부족)
            TEST MODE와 겸용으로 사용한다.

        Returns:
            float: 진입 가능한 수량값 반환
        """
        exchange_data = futures_utils.Selector.exchange_info(cls.TEST_MODE)
        filter_data = futures_utils.Extractor.refine_exchange_data(symbol, exchange_data)
        min_qty = filter_data['minQty']
        step_size = filter_data['stepSize']
        notional = filter_data['notional']

        min_position_size = futures_utils.Calculator.min_position_size(mark_price=mark_price, min_qty=min_qty, step_size=step_size, notional=notional)
        max_position_size = futures_utils.Calculator.max_position_size(mark_price=mark_price, leverage=leverage, step_size=step_size, balance=balance)

        if min_position_size > max_position_size:
            return 0
        return max_position_size

    @classmethod
    def check_leverage(cls, symbol: str, leverage: int) -> int:
        """
        ⭕️ 설정하고자 하는 레버리지값의 유효성을 검사하고 적용가능한 레버리지값을 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 적용하고자 하는 레버리지
            test_mode (bool): 테스트 모드 여부

        Returns:
            int: 적용가능한 레버리지값
        """
        brackets_data = futures_utils.Selector.brackets_data(symbol, cls.TEST_MODE)        
        max_leverage = futures_utils.Extractor.max_leverage(brackets_data)

        min_leverage = 2
        
        if min_leverage <= leverage <= max_leverage:
            return leverage
        elif leverage > max_leverage:
            return max_leverage
        else:
            return min_leverage


    @classmethod
    @abstractmethod
    def set_leverage(cls, symbol:str, leverage:int) -> Dict:
        """
        레버리지 값을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 지정하려는 레버리지 값
            
        Notes:
            test모드의 일경우 exchange_info에 레버리지값 적용처리함.
            
        Return:
            Dict: 레버리지 설정값 피드백
        """
        pass

    
    @classmethod
    def set_margin_type(cls, symbol:str, margin_type:str) -> Dict:
        """
        마진 타입을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            margin_type (str): 지정하는 마진 타입

        Returns:
            Dict: 설정상태 피드백
        """
        pass