# from abc import ABC, abstractmethod

from .OrderProcessor import OrderProcessor
from typing import Union, Optional, Dict
import os


import sys
sys.path.append(os.path.abspath("../../../"))
import Utils.TradingUtils as futures_utils
import Client.Queries.Public.Futures as public_api
import Client.Queries.Private.Futures as private_api

ins_public_api = public_api.API()
ins_private_api = private_api.API()


class Orders(OrderProcessor):
    TEST_MODE = False

    def __init__(self):
        super().__init__(test_mode=self.TEST_MODE)

    @classmethod
    def position_size(
        cls, symbol: str, mark_price: float, leverage: int, balance: float
    ) -> float:
        """
        ⭕️ 매개 변수 조건에 의한 진입 가능한 포지션 수량을 계산한다.

        Args:
            symbol (str): 'BTCUSDT'
            mark_price (float): 진입 가격
            leverage (int): 레버리지
            balance (float): 진입 금액
            test_mode (bool): 테스트 모드 여부

        Notes:
            반환값의 minSize(바이낸스 최소 주문 주문량), maxSize(보유금액 최대 주문 가능량), finalSize(실제 주문가능량)을 의미함.

        Returns:
            Dict: size연산값
        """
        exchange_data = futures_utils.Selector.exchange_info(test_mode=cls.TEST_MODE)
        # symbol_detail = futures_utils.Extractor.symbol_detail(symbol, exchange_data)
        filter_data = futures_utils.Extractor.refine_exchange_data(
            symbol=symbol, exchange_data=exchange_data
        )
        min_qty = filter_data["minQty"]
        step_size = filter_data["stepSize"]
        notional = filter_data["notional"]

        min_position_size = futures_utils.Calculator.min_position_size(
            mark_price=mark_price,
            min_qty=min_qty,
            step_size=step_size,
            notional=notional,
        )

        max_position_size = futures_utils.Calculator.max_position_size(
            mark_price=mark_price,
            leverage=leverage,
            step_size=step_size,
            balance=balance,
        )

        if min_position_size > max_position_size:
            final_size = 0
        else:
            final_size = max_position_size

        return {
            "minSize": min_position_size,
            "maxSize": max_position_size,
            "finalSize": final_size,
        }

    @classmethod
    def set_leverage(cls, symbol: str, leverage: int) -> Dict:
        """
        ⭕️ symbol의 레버리지 값을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 레버리지

        Notes:
            API 수신 데이터를 활용하여 기존 레버리지 값과 설정하고자 하는 레버리지값을 비교 후
            레버리지 설정여부 결정하려 했으나, 결국 API호출이 불가피하므로 반복 재설정하는걸로 결정함.

        Returns:
            Dict: 피드백 데이터
        """
        validate_leverage = cls.check_leverage(symbol=symbol, leverage=leverage)
        return ins_private_api.set_leverage(symbol=symbol, leverage=validate_leverage)

    @classmethod
    def set_margin_type(cls, symbol: str, is_isolated: bool) -> Dict:
        """
        ⭕️ symbol의 마진 타입을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            is_isolated (bool):
                True: "ISOLATED"
                False: "CROSSED"

        Returns:
            Dict: 결과 피드백
        """
        account_balance = ins_private_api.fetch_account_balance()
        position_detail = futures_utils.Extractor.position_detail(
            symbol=symbol, account_data=account_balance
        )
        is_margin_type = position_detail["isolated"]

        if is_margin_type != is_isolated:
            if is_isolated:
                margin_type = "ISOLATED"
            else:
                margin_type = "CROSSED"
            return ins_private_api.set_margin_type(
                symbol=symbol, margin_type=margin_type
            )
        return {"code": None, "msg": "unchanged"}

    @classmethod
    def close_partial_position(
        cls, symbol: str, quantity: float, account_balance: Dict
    ) -> Dict:
        """
        ⭕️ 지정 symbol의 일부만 포지션 종료(매도) 처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            quantity (float): 매도 수량
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        symbol_position = next(
            data for data in account_balance["positions"] if data["symbol"] == symbol
        )
        return ins_private_api.position_market_order(
            symbol=symbol,
            side="BUY" if float(symbol_position["positionAmt"]) < 0 else "SELL",
            quantity=abs(quantity),
            position_side="BOTH",
            reduce_only=True,
        )

    @classmethod
    def close_position(cls, symbol: str, account_balance: Dict) -> Dict:
        """
        ⭕️ 지정 심볼의 포지션을 종료(매도)처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        symbol_position = next(
            data for data in account_balance["positions"] if data["symbol"] == symbol
        )
        position_data = {"positions": [symbol_position]}
        position_amount = int(symbol_position["positionAmt"])
        return cls.close_partial_position(
            symbol=symbol, quantity=position_amount, account_balance=position_data
        )

    @classmethod
    def close_all_positions(cls, account_balance: Dict) -> Dict:
        """
        ⭕️ 보유한 모든 포지션을 시장가 종료(매도)한다.

        Args:
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        position_data = {}
        for data in account_balance["positions"]:
            if float(data["positionAmt"]) != 0:
                position_data["positions"] = [data]
                symbol = data["symbol"]
                cls.close_position(symbol, position_data)

    @classmethod
    def open_market_position(cls, symbol: str, side: str, balance: float, leverage: int) -> Dict:
        """
        ⭕️ 금액을 이용하여 시장가 주문을 실행한다.
        레버리지 타입까지 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            balance (float): 진입 금액(개별 단가 아님)
            position_side (str): 기본 "BOTH"
            leverage (int): 레버리지

        Returns:
            _type_: _description_
        """
        cls.set_leverage(symbol=symbol, leverage=leverage)
        ticker_price = ins_public_api.fetch_mark_price(symbol=symbol)
        mark_price = float(ticker_price['markPrice'])
        
        validate_leverage = futures_utils.Validator.args_leverage(leverage=leverage)
        bracket_data = ins_private_api.fetch_leverage_brackets(symbol=symbol)
        max_leverage = futures_utils.Extractor.max_leverage(brackets_data=bracket_data)
        final_leverage = min(leverage, validate_leverage)
        cls.set_leverage(symbol=symbol, leverage=final_leverage)
        
        quantity = cls.position_size(symbol=symbol,
                                     mark_price=mark_price,
                                     leverage=final_leverage,
                                     balance=balance)
        
        return ins_private_api.position_market_order(symbol=symbol,
                                                     side=side,
                                                     quantity=quantity['finalSize'],
                                                     position_side="BOTH",
                                                     reduce_only=False)
        
    @classmethod
    def open_limit_order(cls):
        ...