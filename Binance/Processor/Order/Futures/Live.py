# from abc import ABC, abstractmethod

from .OrderProcessor import Processor
from typing import Union, Optional, Dict
import os


import sys
sys.path.append(os.path.abspath("../../../"))
import Utils.TradingUtils as futures_utils
import API.Public.Futures
import API.Private.Futures



ins_public_api = API.Public.Futures.API()
ins_private_api = API.Private.Futures.API()

class Orders(Processor):
    TEST_MODE = False
    
    def __init__(self):
        super().__init__(test_mode = self.TEST_MODE)
        
        
    @classmethod
    # @abstractmethod
    def open_market_order(cls, symbol:str, mark_price:float, leverage:int, position_size:float):
        ...
    
    @classmethod
    # @abstractmethod
    def open_limit_order(cls):
        ...
    
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
        # symbol_detail = futures_utils.Extractor.symbol_detail(symbol, exchange_data)
        filter_data = futures_utils.Extractor.refine_exchange_data(symbol, exchange_data)
        min_qty = filter_data['minQty']
        step_size = filter_data['stepSize']
        notional = filter_data['notional']

        min_position_size = futures_utils.Calculator.min_position_size(mark_price=mark_price, min_qty=min_qty, step_size=step_size, notional=notional)
        max_position_size = futures_utils.Calculator.max_position_size(mark_price=mark_price, leverage=leverage, step_size=step_size, balance=balance)

        if min_position_size > max_position_size:
            final_size = 0
        else:
            final_size = max_position_size
        
        return {"minSize":min_position_size,
                "maxSize":max_position_size,
                "finalSize":final_size}

    @classmethod
    def set_leverage(cls, symbol:str, leverage:int) -> Dict:
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
        validate_leverage = cls.check_leverage(symbol, leverage)
        return ins_private_api.set_leverage(symbol, validate_leverage)

    @classmethod
    def set_margin_type(cls, symbol:str, is_isolated:bool) -> Dict:
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
        position_detail = futures_utils.Extractor.position_detail(symbol, account_balance)
        is_margin_type = position_detail["isolated"]
        
        if is_margin_type != is_isolated:
            if is_isolated:
                margin_type = "ISOLATED"
            else:
                margin_type = "CROSSED"
            return ins_private_api.set_margin_type(symbol, margin_type)
        return {"code":None, "msg":"unchanged"}

    @classmethod
    def close_partial_position(cls, symbol:str, quantity:float, account_balance:Dict) -> Dict:
        """
        ⭕️ 지정 symbol의 일부만 포지션 종료(매도) 처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            quantity (float): 매도 수량
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: _description_
        """
        symbol_position = next(data for data in account_balance["positions"] if data["symbol"] == symbol)
        return ins_private_api.position_market_order(symbol=symbol,
                                                     side="BUY" if float(symbol_position['positionAmt'])<0 else "SELL",
                                                     quantity=abs(quantity),
                                                     position_side="BOTH",
                                                     reduce_only=True)

    @classmethod
    def close_position(cls, symbol:str, account_balance:Dict) -> Dict:
        """
        ⭕️ 지정 심볼의 포지션을 종료(매도)처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        symbol_position = next(data for data in account_balance["positions"] if data["symbol"] == symbol)
        position_data = {"positions":[symbol_position]}
        position_amount = int(symbol_position['positionAmt'])
        return cls.close_partial_position(symbol, position_amount, position_data)
        
    @classmethod
    def close_all_positions(cls, account_balance:Dict) -> Dict:
        """
        ⭕️ 보유한 모든 포지션을 시장가 종료(매도)한다.

        Args:
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        position_data = {}
        for data in account_balance['positions']:
            if float(data['positionAmt']) != 0:
                position_data['positions'] = [data]
                symbol = data['symbol']
                cls.close_position(symbol, position_data)

# # class LiveTrade(TradeManager):
# #     @classmethod
# #     def create_open_order(
# #         cls,
# #         symbol: str,
# #         side: Union[str, int],
# #         position_size: float,
# #         price: Optional[float] = None,
# #         test_mode: bool = False,
# #     ):
# #         account_balance = await Selector.account_balance(test_mode)
# #         exchange_info = await Selector.exchange_info(test_mode)

# #         kwargs = {
# #             "symbol": symbol,
# #             "side": "BUY" if Validator.contains(position, BUY_TYPE) else "SELL",
# #             "order_type": "MARKET",
# #             "quantity": position_size,
# #             "price": price,
# #             "time_in_force": "GTC",
# #             "position_side": "BOTH",
# #             "reduce_only": False,
# #         }

# #         signal = await FakeSignalGenerator.order_signal(test_mode, **kwargs)



# class FuturesProcessor:
#     @classmethod
#     async def get_positions_size(
#         cls,
#         symbol: str,
#         mark_price: float,
#         balance: float,
#         leverage: int,
#         test_mode: bool = False,
#     ) -> float:
#         symbol = symbol.upper()
#         exchange_info = await Selector.exchange_info(test_mode)
#         trading_symbols = Extractor.trading_symbols(exchange_info)

#         symbol_info = Extractor.exchange_symbol_info(symbol, exchange_info)

#         min_qty = symbol_info["minQty"]
#         step_size = symbol_info["stepSize"]
#         notional = symbol_info["notional"]

#         min_position_size = Calculator.min_position_size(
#             mark_price, min_qty, step_size, notional
#         )
#         max_position_size = Calculator.max_position_size(
#             mark_price, leverage, step_size, balance
#         )

#         if min_position_size > max_position_size:
#             return 0
#         else:
#             return max_position_size

#     @classmethod
#     async def get_leverage(cls, symbol: str, leverage: int, test_mode: bool):
#         brackets_data = Selector.brackets_data(test_mode)
#         max_leverage = Extractor.max_leverage(brackets_data)
#         if MIN_LEVERAGE <= max_leverage <= config_max_leverage:
#             return max_leverage
#         elif config_max_leverage < max_leverage:
#             return config_max_leverage
#         else:
#             return MIN_LEVERAGE

#     @classmethod
#     async def create_open_order(
#         cls,
#         symbol: str,
#         side: Union[str, int],
#         position_size: float,
#         price: Optional[float] = None,
#         test_mode: bool = False,
#     ):
#         account_balance = await Selector.account_balance(test_mode)
#         exchange_info = await Selector.exchange_info(test_mode)

#         kwargs = {
#             "symbol": symbol,
#             "side": "BUY" if Validator.contains(position, BUY_TYPE) else "SELL",
#             "order_type": "MARKET",
#             "quantity": position_size,
#             "price": price,
#             "time_in_force": "GTC",
#             "position_side": "BOTH",
#             "reduce_only": False,
#         }

#         signal = await FakeSignalGenerator.order_signal(test_mode, **kwargs)
