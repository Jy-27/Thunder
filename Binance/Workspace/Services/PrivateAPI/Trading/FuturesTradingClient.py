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

    # Ticker의 leverage 정보 수신 및 반환
    def fetch_leverage_brackets(self, symbol: str) -> Dict:
        """
        ⭕️ symbol별 레버리지 구간 정보를 조회 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'

        Notes:
            API-KEY가 필요한 endpoint다.
        
        Returns:
            Dict: symbol레버리지 구간별 정보
        """
        endpoint = "/fapi/v1/leverageBracket"
        params = {"symbol": symbol, "timestamp": int(time.time() * 1000)}
        return self._send_request("GET", endpoint, params)

    def fetch_historical_trades(
        self, symbol: str, limit: Optional[int] = None, from_id: Optional[int] = None
    ) -> Dict:
        """
        ⭕️ 과거 체결 내역을 상세 조회 및 반환한다.

        Args:
            symbol (str): _description_
            limit (Optional[int], optional): _description_. Defaults to None.
            from_id (Optional[int], optional): _description_. Defaults to None.

        Returns:
            Dict: id별 체결내역 상세
        """

        endpoint = "/fapi/v1/historicalTrades"
        params = {"symbol": symbol}
        if limit:
            params["limit"] = limit
        if from_id:
            params["fromId"] = from_id

        return self._send_request("GET", endpoint, params)

    # Ticker의 leverage값 설정
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        ⭕️ 지정 symbol에 대하여 레버리지 값을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 125

        Notes:
            현재 설정상태와 동일한 설정 시도시 오류발생한다.
            상태를 먼저 확인하고 실행해야한다.

        Returns:
            Dict: 설정결과에 대한 피드백
        """
        endpoint = "/fapi/v1/leverage"
        params = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("POST", endpoint, params)

    # Ticker의 margin type 설정
    def set_margin_type(self, symbol: str, margin_type: str) -> Dict:
        """
        ⭕️ 마진 타입을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            margin_type (str):
                - "CROSSED" : 교차마진
                - "ISOLATED" : 격리마진

        Notes:
            현재 설정상태와 동일한 설정 시도시 오류발생한다.
            상태를 먼저 확인하고 실행해야한다.

        Returns:
            Dict: _description_
        """
        endpoint = "/fapi/v1/marginType"
        ms_timestamp = int(time.time() * 1_000)
        params = {
            "symbol": symbol,
            "marginType": margin_type,
            "timestamp": ms_timestamp,
        }
        return self._send_request("POST", endpoint, params)

    # 시장가 포지션 주문
    def position_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        position_side: str,
        reduce_only: bool,
    ) -> Dict:  #
        """
        ⭕️ 시장가 포지션 OPEN or CLOSE 주문을 생성한다.

        Args:
            symbol (str): 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            quantity (float): 주문수량
            position_side (int): 포지션 방향
                - "BOTH" : 방향을 지정하지 않고 포지션 유지
                - "LONG" : 롱 포지션
                - "SHORT" : 숏 포지션
            reduce_only (bool):
                - True : 포지션 종료시
                - False : 포지션 진입시

        Notes:
            position_side는 기본값 "BOTH"이며 hedge거래시 side값과 반대값을 입력한다.

        Returns:
            Dict: 주문내역
        """
        endpoint = "/fapi/v1/order"
        ms_timestamp = int(time.time() * 1_000)
        order_type = "MARKET"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "positionSide": position_side,
            "reduceOnly": reduce_only,
            "type": order_type,
            "timestamp": ms_timestamp,
        }
        return self._send_request("POST", endpoint, params)

    # 지정가 포지션 주문
    def position_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        position_side: str,
        price: float,
        time_in_force: str,
        reduce_only: bool,
    ) -> Dict:
        """
        ⭕️ 지정가 포지션 오픈 주문을 생성한다.

        Args:
            symbol (str): 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            quantity (float): 주문 수량
            position_side (str): 포지션 방향 설정
                - "BOTH" : 방향을 지정하지 않고 포지션 유지 (Hedge: False)
                - "LONG" : 롱 포지션 (Hedge: True)
                - "SHORT" : 숏 포지션 (Hedge: True)
            price (float): 주문 가격
            time_in_force (str): 주문유효기간
                - "GTC (Good Till Cancel)" : 사용자가 취소할떄까지 유지 (기본값 추천)
                    >> LIMIT, STOP_MARKET, TAKE_PROFIT_LIMIT
                - "IOC (Immediate Or Cancel)" : 주문 즉시 체결 가능한 부분만 체결, 나머지 취소
                    >> LIMIT, TAKE_PROFIT_LIMIT
                - "FOK (Fill Or Kill)" : 주문 전체가 체결되지 않으면 주문을 취소
                    >> TAKE_PROFIT_LIMIT
                - "GTX (Post-Only)" : 즉시 체결되면 주문이 취소됨 (Maker 거래만 가능)
                    >> LIMIT
            reduce_only (bool):
                - True : 포지션 종료시
                - False : 포지션 진입시

        Returns:
            Dict: 주문내역
        """
        endpoint = "/fapi/v1/order"
        ms_timestamp = int(time.time() * 1_000)
        order_type = "LIMIT"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "positionSide": position_side,
            "price": price,
            "timeInForce": time_in_force,
            "reduceOnly": reduce_only,
            "type": order_type,
            "timestamp": ms_timestamp,
        }
        return self._send_request("POST", endpoint, params)

    # 시장가 손절
    def stop_loss_market_order(self, symbol:str, side:str, quantity:float, stop_price:float) -> Dict:
        """
        ⭕️ 스탑 가격 도달시 시장가 포지션 종료(매도) 한다

        Args:
            symbol (str): 'BTCUSDT'
            side (str): 'BUY' or 'SELL'
            quantity (str): 주문 수량
            stop_price (float): 타겟 스탑 가격 (SIDE가 BUY일 경우 현재가보다 높아야하며, 반대의 경우 낮아야 한다.)

        Notes:
            stop_loss Limit은 Futures시장에서 지원하지 않는다.
            stop_price 주문시 (SIDE가 BUY일 경우 현재가보다 높아야하며, 반대의 경우 낮아야 한다.) 조건 위배시 오류발생한다.

        Returns:
            Dict: 주문내역
        """
        endpoint = "/fapi/v1/order"
        ms_timestamp = int(time.time() * 1_000)
        order_type = "STOP_MARKET"
        time_in_force = "GTC"
        params = {
            "symbol":symbol,
            "side":side,
            "quantity":quantity,
            "stopPrice":stop_price,
            "timeInForce":time_in_force,
            "type":order_type,
            "timestamp":ms_timestamp
        }
        return self._send_request("POST", endpoint, params)
        
    # 지정가 익절
    def take_profit_limit_order(self, symbol:str, side:str, quantity:float, limit_price:float, stop_price:float, time_in_force:str) -> Dict:
        """
        ⭕️ 목표 금액(수익) 도달시 지정가 종료(매도) 주문을 생성한다.

        Args:
            symbol (str): 'BTCUSDT'
            side (str): 'BUY' or 'SELL' (현재 포지션과 반대 입력)
            quantity (float): 매도 수량
            limit_price (float): 주문 금액
            stop_price (float): 목표 금액
            time_in_force (str): 주문유효기간
                - "GTC (Good Till Cancel)" : 사용자가 취소할떄까지 유지 (기본값 추천)
                    >> LIMIT, STOP_MARKET, TAKE_PROFIT_LIMIT
                - "IOC (Immediate Or Cancel)" : 주문 즉시 체결 가능한 부분만 체결, 나머지 취소
                    >> LIMIT, TAKE_PROFIT_LIMIT

        Notes:
            position_limit_order 함수로 주문시 예수금 부족할 경우 오류발생한다. 용도에 맞게 구분하여 사용해야한다.
            (개념 추가정리가 필요하다.)

            현재 포지션이 Long일경우 Limit_price < stop_price
            현재 포지션이 SHort일경우 Limit_price > stop_price
            
        Returns:
            Dict: 주문내역
        """
        endpoint = "/fapi/v1/order"
        ms_timestamp = int(time.time() * 1_000)
        order_type = "TAKE_PROFIT"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "price":limit_price,
            "stopPrice": stop_price,
            "timeInForce": time_in_force,
            "type":order_type,
            "timestamp": ms_timestamp,
        }
        return self._send_request("POST", endpoint, params)
    
    # 시장가 잉ㄱ절
    def take_profit_market_order(self, symbol:str, side:str, quantity:float, stop_price:float) -> Dict:
        """
        ⭕️ 목표 금액(수익) 도달시 현재가 종료(매도) 주문을 생성한다.

        Args:
            symbol (str): 'BTCUSDT''
            side (str): 'BUY' or 'SELL' (현재 포지션과 반대 입력))
            quantity (float): 매도 수량
            stop_price (float): 목표 금액

        Notes:
            position_market_order는 현재가에 즉시 거래이며, 본 함수는 목표가 도달시 즉시 매도한다.
            (개념 추가정리가 필요하다.)

        Returns:
            Dict: 주문내역
        """
        endpoint = "/fapi/v1/order"
        ms_timestamp = int(time.time() * 1_000)
        order_type = "TAKE_PROFIT_MARKET"
        params = {
            "symbol": symbol,
            "side": side,
            "quantity": quantity,
            "stopPrice": stop_price,
            "type":order_type,
            "timestamp": ms_timestamp,
        }

        return self._send_request("POST", endpoint, params)