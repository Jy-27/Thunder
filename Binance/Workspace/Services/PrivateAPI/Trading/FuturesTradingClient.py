from .TradingClient import TradingClient
from typing import Dict, Union, Any, Optional
import time
import asyncio


class FuturesTradingClient(TradingClient):
    """
    Binance Futures API와 관련된 함수의 집합이다. API-key가 반드시 필요하다.
    오류에 대한 검증코드는 포함되지 않았다. 그러므로 본 함수를 실행전 검증 기능의 코드를 구현해야한다.
    
    Alias: futures_tr_client
    """
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, **kwargs):
        api_key = kwargs["apiKey"]
        secret = kwargs["secret"]
        super().__init__(api_key=api_key, secret=secret)

    async def fetch_leverage_brackets(self, symbol: str) -> Dict:
        """
        ⭕️ symbol별 레버리지 구간 정보를 조회 및 반환한다.
        """
        endpoint = "/fapi/v1/leverageBracket"
        params = {"symbol": symbol, "timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    async def fetch_historical_trades(
        self, symbol: str, limit: Optional[int] = None, from_id: Optional[int] = None
    ) -> Dict:
        """
        ⭕️ 과거 체결 내역을 상세 조회 및 반환한다.
        """
        endpoint = "/fapi/v1/historicalTrades"
        params = {"symbol": symbol}
        if limit:
            params["limit"] = limit
        if from_id:
            params["fromId"] = from_id

        return await self._send_request("GET", endpoint, params)

    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        ⭕️ 지정 symbol에 대하여 레버리지 값을 설정한다.
        """
        endpoint = "/fapi/v1/leverage"
        params = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """
        ⭕️ 마진 타입을 설정한다.
        """
        endpoint = "/fapi/v1/marginType"
        params = {
            "symbol": symbol,
            "marginType": margin_type,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def position_market_order(
        self, symbol: str, side: str, quantity: float, position_side: str, reduce_only: bool
    ) -> Dict:
        """
        ⭕️ 시장가 포지션 OPEN or CLOSE 주문을 생성한다.
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "positionSide": position_side,
            "reduceOnly": reduce_only,
            "type": "MARKET",
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def position_limit_order(
        self, symbol: str, side: str, quantity: float, position_side: str, price: float, time_in_force: str, reduce_only: bool
    ) -> Dict:
        """
        ⭕️ 지정가 포지션 오픈 주문을 생성한다.
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "positionSide": position_side,
            "price": price,
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "type": "LIMIT",
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def stop_loss_market_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """
        ⭕️ 스탑 가격 도달시 시장가 포지션 종료(매도) 한다
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "stopPrice": stop_price,
            "timeInForce": "GTC",
            "type": "STOP_MARKET",
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def take_profit_limit_order(self, symbol: str, side: str, quantity: float, limit_price: float, stop_price: float, time_in_force: str) -> Dict:
        """
        ⭕️ 목표 금액(수익) 도달시 지정가 종료(매도) 주문을 생성한다.
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price": limit_price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
            "type": "TAKE_PROFIT",
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    async def take_profit_market_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Dict:
        """
        ⭕️ 목표 금액(수익) 도달시 현재가 종료(매도) 주문을 생성한다.
        """
        endpoint = "/fapi/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "stopPrice": stop_price,
            "type": "TAKE_PROFIT_MARKET",
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)
