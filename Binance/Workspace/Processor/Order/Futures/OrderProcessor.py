from abc import ABC, abstractmethod
from typing import Dict

import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils

# 힌트
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import (
    FuturesTradingClient as futures_tr_client,
)
from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher as futures_mk_fetcher,
)


class OrderProcessor:
    def __init__(
        self,
        futures_tr_client: futures_tr_client,
        futures_mk_fetcher: futures_mk_fetcher,
    ):
        self.ins_trading_client = futures_tr_client
        self.ins_market_fetcher = futures_mk_fetcher

    def position_size(
        self, symbol: str, mark_price: float, leverage: int, balance: float
    ):
        exchange_data = self.ins_market_fetcher.fetch_exchange_info()
        filter_data = tr_utils.Extractor.refine_exchange_data(symbol, exchange_data)

        min_qty = filter_data["minQty"]
        step_size = filter_data["stepSize"]
        notional = filter_data["notional"]

        min_position_size = tr_utils.Calculator.min_position_size(
            mark_price=mark_price,
            min_qty=min_qty,
            step_size=step_size,
            notional=notional,
        )
        max_position_size = tr_utils.Calculator.max_position_size(
            mark_price=mark_price,
            leverage=leverage,
            step_size=step_size,
            balance=balance,
        )

        if min_position_size > max_position_size:
            return 0
        return max_position_size

    def check_leverage(self, symbol: str, leverage: int) -> int:
        """
        ⭕️ 설정하고자 하는 레버리지값의 유효성을 검사하고 적용가능한 레버리지값을 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 적용하고자 하는 레버리지
            test_mode (bool): 테스트 모드 여부

        Returns:
            int: 적용가능한 레버리지값
        """
        brackets_data = self.ins_trading_client.fetch_leverage_brackets(symbol)
        max_leverage = tr_utils.Extractor.max_leverage(brackets_data)

        min_leverage = 2

        if min_leverage <= leverage <= max_leverage:
            return leverage
        elif leverage > max_leverage:
            return max_leverage
        else:
            return min_leverage

    def set_leverage(self, symbol: str, leverage: int) -> Dict:
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
        validate_leverage = self.check_leverage(symbol, leverage)
        return self.ins_trading_client.set_leverage(symbol, validate_leverage)
        
    def set_margin_type(self, symbol:str, is_isolated:bool) -> Dict:
        account_balance = self.ins_trading_client.fetch_account_balance()
        position_detail = tr_utils.Extractor.position_detail(symbol, account_balance)
        is_margin_type = position_detail["isolated"]

        if is_margin_type != is_isolated:
            if is_isolated:
                margin_type = "ISOLATED"
            else:
                margin_type = "CROSSED"
            return ins_private_client.set_margin_type(
                symbol=symbol, margin_type=margin_type
            )
        return {"code": None, "msg": "unchanged"}
    
    def close_partial_position_at_market(self, symbol:str, quantity:float) -> Dict:
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
        return ins_private_client.position_market_order(
            symbol=symbol,
            side="BUY" if float(symbol_position["positionAmt"]) < 0 else "SELL",
            quantity=abs(quantity),
            position_side="BOTH",
            reduce_only=True,
            )
        
    def close_position_at_market(self, symbol:str):
        """
        ⭕️ 지정 심볼의 포지션을 종료(매도)처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        account_balance = self.ins_trading_client.fetch_account_balance()
        symbol_position = next(
            data for data in account_balance["positions"] if data["symbol"] == symbol
        )
        position_data = {"positions": [symbol_position]}
        position_amount = int(symbol_position["positionAmt"])
        return cls.close_partial_position(
            symbol=symbol, quantity=position_amount, account_balance=position_data
        )
    
    def close_position_at_market(self, symbol: str) -> Dict:
        """
        ⭕️ 지정 심볼의 포지션을 종료(매도)처리한다.

        Args:
            symbol (str): 'BTCUSDT'
            account_balance (Dict): 함수 fetch_account_balance() 반환값

        Returns:
            Dict: 결과 피드백
        """
        account_balance = self.ins_trading_client.fetch_account_balance()
        symbol_position = next(
            data for data in account_balance["positions"] if data["symbol"] == symbol
        )
        position_data = {"positions": [symbol_position]}
        position_amount = int(symbol_position["positionAmt"])
        return cls.close_partial_position(
            symbol=symbol, quantity=position_amount, account_balance=position_data
        )
    
    def close_all_position_at_market(self):
        account_balance = self.ins_trading_client.fetch_account_balance()
        position_data = {}
        for data in account_balance["positions"]:
            if float(data["positionAmt"]) != 0:
                position_data["positions"] = [data]
                symbol = data["symbol"]
                cls.close_position(symbol, position_data)
                
    def open_position_at_market(self, symbol: str, side: str, balance: float, leverage: int) -> Dict:
        self.set_leverage(symbol, leverage)
        mark_price = self.ins_market_fetcher.fetch_mark_price(symbol)
        quantity = self.position_size(symbol, mark_price, leverage, balance)
        return self.ins_trading_client.position_market_order(symbol=symbol,
                                                             side=side,
                                                             quantity=quantity['finalSize'],
                                                             position_side="BOTH",
                                                             reduce_only=False)
    
    def limit_orders(self, symbol:str, side:str, balance: float, price:float, leverage:int, reduce_only:bool) -> Dict:
        positions_side = "BOTH"
        quantity = self.position_size(symbol, price, leverage, balance)
        return self.ins_trading_client.position_limit_order(symbol=symbol,
                                                            side=side,
                                                            quantity=quantity,
                                                            position_side=positions_side,
                                                            price=price,
                                                            time_in_force='GTC',
                                                            reduce_only=reduce_only)
    