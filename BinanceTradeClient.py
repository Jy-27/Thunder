import aiohttp
import asyncio
import time
import hashlib
import hmac
import json
import os
import utils
import math
import requests
from MarketDataFetcher import SpotAPI, FuturesAPI
from typing import Dict, Optional, List, Union, Any, cast
from decimal import Decimal, ROUND_UP


class BinanceOrderManager:
    BASE_URL = ""  # 자식 클래스에서 URL을 설정해야 합니다.

    def __init__(self):
        data = self.load_api_keys()

        if data is None:
            raise ValueError("API 키와 시크릿 키를 로드할 수 없습니다.")

        self._api_key = data["apiKey"]
        self._secret_key = data["secret"]
        self.account_balance: Optional[Union[Dict]] = None
        self.market_type: str = self.__class__.__name__.split("OrderManager")[0]

    # API-key정보 json파일 로드.
    def load_api_keys(self) -> Optional[Dict[str, str]]:
        """
        1. 기능 : API주문에 필요한 API-key와 Secret-key 저장파일(json)을 불러온다.
        2. 매개변수 : 해당없음.
        """
        current_file_path = os.getcwd()
        parent_directory = os.path.dirname(current_file_path)
        file_name = "binance.json"
        file_path = os.path.join(parent_directory, "API", file_name)

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if "apiKey" in data and "secret" in data:
                return data
            else:
                print("JSON 파일에 'apiKey' 또는 'secret' 키가 없습니다.")
        except FileNotFoundError:
            print(f"'{file_name}' 파일이 'API' 디렉토리에 없습니다.")
        except json.JSONDecodeError:
            print(f"'{file_name}' 파일이 올바른 JSON 형식이 아닙니다.")
        return None

    # API필요한 headers생성
    async def _get_headers(self) -> Dict[str, str]:
        """
        1. 기능 : API에 필요한 headers생성
        2. 매개변수 : 해당없음.
        """
        return {"X-MBX-APIKEY": self._api_key}

    # API 요청의 매개변수 서명 추가
    async def _sign_params(self, params: Dict) -> Dict:
        """
        1. 기능 : Binance API 요청의 매개변수에 서명을 추가
        2. 매개변수
            1) 각 함수별 수집된 params
        """
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        signature = hmac.new(
            self._secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    # API 요청 생성 및 서버 전송, 응답처리
    async def _send_request(self, method: str, endpoint: str, params: dict) -> dict:
        """
        1. 기능 : API 요청을 생성 및 서버로 전송, 응답처리
        2. 매개변수
            1) method : 각 함수별 요청내용
            2) endpoint : 각 함수별 ENDPOINT
            3) params : 각 함수별 수집된 params
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = await self._get_headers()
        params = await self._sign_params(params)

        # TEST ZONE - 요청 정보와 시그니처 출력
        # print("Request URL:", url)
        # print("Headers:", headers)
        # print("Params:", params)

        response = requests.request(method, url, headers=headers, params=params)

        # TEST ZONE - 응답 상태 코드와 응답 메시지 출력
        # print("Response Status Code:", response.status_code)
        # print("Response Text:", response.text)

        response.raise_for_status()
        return response.json()

    # 현물시장, 선물시장 계좌 잔고 조회
    async def fetch_account_balance(self) -> Dict:
        """
        1. 기능 : Market별 재고현황을 수신 및 반환한다.
        2. 매개변수 : 해당없음.
        """
        endpoint = (
            "/api/v3/account"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v2/account"
        )
        params: dict = {"timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    # Ticker의 미체결 주문상태 조회 및 반환
    async def fetch_order_status(self, symbol: Optional[str] = None) -> Dict:
        """
        1. 기능 : Ticker 미체결 주문상태를 조회 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
        """
        symbol = symbol.upper() if symbol else None
        endpoint = (
            "/api/v3/openOrders"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/openOrders"
        )
        params: dict = {"timestamp": int(time.time() * 1000)}
        if symbol:
            params["symbol"] = symbol
        return await self._send_request("GET", endpoint, params)

    # Ticker의 전체 주문내역 조회 및 반환
    async def fetch_order_history(self, symbol: str, limit: int = 500) -> Dict:
        """
        1. 기능 : 전체 주문 내역(체결, 미체결, 취소된 주문 등등..)을 조회 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) limit : 조회량 (MAX 500)
        """
        symbol = symbol.upper()
        endpoint = (
            "/api/v3/allOrders"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/allOrders"
        )
        params = {
            "symbol": symbol,
            "limit": limit,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("GET", endpoint, params)

    # Ticker의 거래내역 조회 및 반환
    async def fetch_trade_history(self, symbol: str, limit: int = 500) -> Dict:
        """
        1. 기능 : 개별 거래 내역을 조회 및 반환한다.
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) limit : 조회량 (MAX 500)
        """
        symbol = symbol.upper()
        endpoint = (
            "/api/v3/myTrades"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/userTrades"
        )
        params = {
            "symbol": symbol,
            "limit": limit,
            "timestamp": int(time.time() * 1000),
            "recvWindow": 5000,
        }
        return await self._send_request("GET", endpoint, params)

    # 현재 주문상태를 상세 조회(체결, 미체결 등등...)
    async def fetch_order_details(self, symbol: str, order_id: int) -> Dict:
        """
        1. 기능 : 현재의 주문 상태를 자세히 조회한다. (체결, 미체결, )
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) order_id : get_open_orders에서 조회할 수 있음.
        """
        endpoint = (
            "/api/v3/order"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/order"
        )
        params = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("GET", endpoint, params)

    # 미체결 취소 주문 생성 및 제출
    async def submit_cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        1. 기능 : 현재 미체결된 주문을 취소한다.
        2. 매개변수
            1) order_id : get_open_orders에서 조회할 수 있음.
        """
        endpoint = (
            "/api/v3/order"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/order"
        )
        params = {
            "symbol": symbol.upper(),
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("DELETE", endpoint, params)


class SpotOrderManager(BinanceOrderManager):
    BASE_URL = "https://api.binance.com"

    def __init__(self, spot_api: Optional[SpotAPI] = None):
        super().__init__()
        self.spot_api = SpotAPI()

    async def get_min_trade_quantity(self, symbol: str) -> Union[int, float]:
        exchange_info_data = await self.spot_api.fetch_exchange_info(symbol=symbol)
        for filter in exchange_info_data["symbols"][0]["filters"]:
            if filter["filterType"] == "LOT_SIZE":
                min_qty = float(filter["minQty"])  # 최소 수량
                step_size = float(filter["stepSize"])  # 최소 거래 단위
                return max(min_qty, step_size)
        return 0

    # Spot 전체 잔고 수신 후 보유 내역값만 반환
    async def get_account_balance(self) -> Optional[Dict[str, Dict[str, float]]]:
        """
        1. 기능 : Spot 전체 잔고 수신 후 보유내역만 후처리 하여 반환
        2. 매개변수 : 해당없음.
        """
        balance_result = {}
        response = await self.fetch_account_balance()
        account_balances = response.get("balances")

        # account_balances가 None이 아닐 때만 utils._collections_to_literal 호출
        parsed_balances: List[Dict[str, Any]] = (
            utils._collections_to_literal(account_balances)
            if account_balances is not None
            else []
        )

        for asset_data in parsed_balances:
            asset = asset_data.get("asset")
            if not asset:
                continue  # asset이 None일 경우 건너뜀

            # 기본값을 설정하여 None이 반환되지 않도록 함
            free_balance = asset_data.get("free", 0.0)  # 기본값 0.0 설정
            locked_balance = asset_data.get("locked", 0.0)  # 기본값 0.0 설정
            total_balance = free_balance + locked_balance

            if total_balance != 0:
                balance_result[asset] = {"free": free_balance, "locked": locked_balance}

        return balance_result if balance_result else None

    # Spot 시장의 주문(매수/매도)신호를 보낸다.
    async def submit_spot_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Dict:
        """
        1. 기능 : 현물시장에 구매(매도) 주문을 넣는다.
        2. 매개변수
            1) symbol : 쌍거래 자산
            2) side : 주문 방향 결정
                >> "BUY" : 매수
                >> "SELL" : 매도
            3) order_type : 주문 타입
                >> "LIMIT" : 지정가
                >> "MARKET" : 시장가
                >> "STOP_MARKET" : StopLoss 설정시
                >> "TAKE_PROFIT_MARKET" : 수익실현 설정시, 지정가 도달시 시장가 주문 실행
            4) quantity : 거래 주문 수량
            5) price : 주문 단가 (type : LIMIT일때만)
        """
        endpoint = "/api/v3/order"  # 현물 시장 API 엔드포인트

        # 공통 파라미터 설정
        params = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "type": order_type.lower(),
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
        }

        # 지정가 주문일 경우 추가 파라미터
        if order_type == "LIMIT":
            params["timeInForce"] = time_in_force
        if price:
            params["price"] = price

        return await self._send_request("POST", endpoint, params)


class FuturesOrderManager(BinanceOrderManager):
    BASE_URL = "https://fapi.binance.com"

    def __init__(self, futures_api: Optional[FuturesAPI] = None):
        super().__init__()
        self.futures_api = FuturesAPI()

    # Ticker의 leverage 정보 수신 및 반환
    async def _get_leverage_brackets(self, symbol: str) -> Dict:
        """
        1. 기능 : 선물거래 레버리지 설정값 정보 수신
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
        3. 반환
            - 각 심볼에 대한 레버리지 구간 정보를 포함한 리스트
        """
        endpoint = "/fapi/v1/leverageBracket"
        params = {"symbol": symbol.upper(), "timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    # Ticker의 MAX leverage값 반환
    async def get_max_leverage(self, symbol: str) -> int:
        """
        1. 기능 : 선물거래 ticker에 대한 MAX leverage값 반환
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
        """
        brackets_data = await self._get_leverage_brackets(symbol=symbol)

        # brackets_data와 필드 검증
        if (
            brackets_data
            and "brackets" in brackets_data[0]
            and isinstance(brackets_data[0]["brackets"], list)
        ):
            max_leverage = brackets_data[0]["brackets"][0].get(
                "initialLeverage", 1
            )  # 기본값 1 설정
            if isinstance(max_leverage, (int, float)):
                return int(max_leverage)

        raise ValueError(f"{symbol}에 대한 유효한 레버리지 정보를 찾을 수 없습니다.")

    # Ticker의 leverage값 설정
    async def set_leverage(self, symbol: str, leverage: int) -> dict:
        """
        1. 기능 : 선물거래 레버리지값 설정
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
            2) leverage : 정수타입 숫자 입력 MAX 125배. 초과입력시 자동조정
        """
        symbol = symbol.upper()

        # max_leverage = self._get_max_leverage(symbol=symbol)

        # if leverage > max_leverage:
        #     leverage = max_leverage
        #     print(f'leverage 설정값 최대치 초과 :{max_leverage}로 조정')

        endpoint = "/fapi/v1/leverage"
        params = {
            "symbol": symbol,
            "leverage": leverage,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    # Ticker의 margin type 설정
    async def set_margin_type(self, symbol: str, margin_type: str) -> Union[str, Any]:
        """
        1. 기능 : 마진 타입 설정
        2. 매개변수
            1) margin_type
                >> "CROSSED" : 교차 마진
                >> "ISOLATED" : 격리 마진
        """
        # 심볼과 마진 타입을 대문자로 변환
        symbol = symbol.upper()
        margin_type = margin_type.upper()

        response = await self.fetch_account_balance()
        account_balances = response.get("positions")

        if account_balances is None:
            return f"fetch_account_balance함수 수신정보 없음."

        # 계정 데이터에서 심볼에 해당하는 포지션 정보 추출
        position_data = next(
            (data for data in account_balances if data.get("symbol") == symbol), None
        )

        if position_data is None:
            raise ValueError(f"심볼 '{symbol}'을(를) 계정 포지션에서 찾을 수 없습니다.")

        # 현재 포지션의 격리 상태 확인
        current_isolated_status = position_data.get("isolated")

        # 입력된 마진 타입과 현재 상태가 일치하는지 확인
        if (current_isolated_status and margin_type == "ISOLATED") or (
            not current_isolated_status and margin_type == "CROSSED"
        ):
            return f"마진 타입이 이미 설정된 상태입니다 - {margin_type}"

        # 마진 타입 설정 요청
        endpoint = "/fapi/v1/marginType"
        params = {
            "symbol": symbol,
            "marginType": margin_type,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", endpoint, params)

    # Futures 전체 잔고 수신 후 보유 내역값만 반환
    async def get_account_balance(self) -> Union[str, Dict[str, Dict[str, float]]]:
        """
        1. 기능 : Futures 전체 잔고 수신 후 보유내역만 후처리 하여 반환
        2. 매개변수 : 해당없음.
        """
        balance_result: Dict = {}
        response = await self.fetch_account_balance()
        account_balances = response.get("positions")

        if account_balances is None:
            return f"fetch_account_balance함수 수신정보 없음."

        for position_data in account_balances:
            parsed_balances = utils._collections_to_literal([position_data])[0]
            if parsed_balances.get("positionAmt") != 0:
                symbol = parsed_balances.get("symbol")
                balance_result[symbol] = {}
                for key, nested_data in parsed_balances.items():
                    if key == "symbol":
                        ...
                    else:
                        balance_result[symbol][key] = nested_data
        return balance_result

    # Futures 시장의 주문(long/short)신호를 보낸다.
    async def submit_order(
        self,
        symbol: str,
        side: str,
        order_type: str,
        quantity: float,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
        position_side: str = "BOTH",
        reduce_only: bool = False,
    ) -> Dict:
        """
        1. 기능 : 선물시장 주문을 넣는다.
        2. 매개변수
            1) symbol : 쌍거래 자산
            2) side : 주문 방향 결정
                >> "BUY" : 매수
                >> "SELL" : 매도
            3) order_type : 주문 타입
                >> "LIMIT" : 지정가
                >> "MARKET" : 시장가
                >> "STOP_MARKET" : StopLoss 설정시
                >> "TAKE_PROFIT_MARKET" : 수익실현 설정시, 지정가 도달시 시장가 주문 실행
            4) quantity : 거래 주문 수량
            5) price : 주문 단가 (type : LIMIT일때만)
            6) time_in_force : 주문유효기간
                >> "GTC" : 사용자가 취소할떄까지 유지
                >> "IOC" : 주문 즉시 체결 가능한 부분만 체결, 나머지 취소
                >> "FOK" : 주문 전체가 체결되지 않으면 주문을 취소
            7) position_side : 포지션 방향 설정
                >> "BOTH" : 방향을 지정하지 않고 포지션 유지
                >> "LONG" : 롱 포지션
                >> "SHORT" : 숏 포지션
            8) reduce_only : 포지션 청산시에 사용.
                >> True : 소량 자산 포지션 종료.
                >> False : 일반 주문
        """
        endpoint = "/fapi/v1/order"  # 선물 시장 API 엔드포인트

        # 공통 파라미터 설정
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),
            "type": order_type,
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
        }

        # 지정가 주문일 경우 추가 파라미터
        if order_type == "LIMIT":
            params["timeInForce"] = time_in_force
        if price:
            params["price"] = price

        # 선물거래의 경우에만 positionSide와 reduceOnly 설정
        params["positionSide"] = position_side
        params["reduceOnly"] = "true" if reduce_only else "false"

        return await self._send_request("POST", endpoint, params)

    # 선물 시장의 symbol별 최소 거래 수량을 계산한다.
    async def get_min_trade_quantity(self, symbol: str) -> float:
        symbol = symbol.upper()
        exchange_info = await self.futures_api.fetch_exchange_info()

        # 심볼 정보 필터링
        # 기본값 []로 symbols 데이터 처리
        symbols = exchange_info.get("symbols", [])
        symbol_info = next(
            (item for item in symbols if item.get("symbol") == symbol),
            None,  # 기본값 None을 설정하여 찾지 못했을 때 대비
        )

        # symbol_info가 None이 아닌지 확인 후 filters 처리
        filters = symbol_info.get("filters", []) if symbol_info else []

        # 필터에서 필요한 정보 추출
        min_qty, step_size, notional = None, None, None

        # filters가 None이 아닌지 확인 후 반복
        if filters:
            for filter_item in filters:
                if filter_item.get("filterType") in ["LOT_SIZE", "MARKET_LOT_SIZE"]:
                    min_qty = float(filter_item.get("minQty", 0))  # 기본값 0
                    step_size = (
                        filter_item.get("stepSize") or "1"
                    )  # None일 경우 문자열 "1" 기본값
                elif filter_item.get("filterType") == "MIN_NOTIONAL":
                    notional = float(filter_item.get("notional", 0))  # 기본값 0

        # 현재 가격 가져오기
        # 기본값 0을 설정하여 current_price_data가 None일 경우 대비
        current_price_data = (
            await self.futures_api.fetch_ticker_price(symbol=symbol) or {}
        )
        current_price = float(
            current_price_data.get("price", 0)
        )  # None일 경우 기본값 0

        # notional이 None일 경우 기본값 0.0으로 설정하여 연산 오류 방지
        required_quantity: float = (notional or 0.0) / current_price
        min_trade_quantity = float(
            Decimal(required_quantity).quantize(
                Decimal(step_size or 1), rounding=ROUND_UP
            )
        )

        return min_trade_quantity

    # # 포지션 종료 order신고 발생
    async def submit_close_position(
        self,
        symbol: str,
        order_type: str,
        quantity: Optional[float] = None,
        price: Optional[float] = None,
        time_in_force: str = "GTC",
    ) -> Optional[Dict]:
        # account_balance 가져오고, dict인지 확인
        account_balance = await self.get_account_balance()
        print(account_balance)
        # account_balance가 dict인지 확인하고 아니라면 None 반환
        if not isinstance(account_balance, dict):
            return None

        # 포지션 데이터 가져오기
        position_data: Optional[Dict[str, Any]] = account_balance.get(symbol.upper())

        if not position_data:
            return None

        # 포지션 양 가져오기
        position_amount = position_data.get("positionAmt")
        if position_amount is None or position_amount == 0:
            return None  # 닫을 포지션이 없음

        # 포지션 방향에 따라 주문 방향 설정
        side = "BUY" if position_amount < 0 else "SELL"

        # 수량이 주어지지 않은 경우 포지션 양의 절대값 사용
        if quantity is None:
            quantity = abs(position_amount)

        # TEST ZONE
        print(symbol, side, order_type, quantity, price)

        # reduce_only 플래그를 사용하여 포지션 청산 주문 제출
        return await self.submit_order(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            time_in_force=time_in_force,
            reduce_only=True,
        )


if __name__ == "__main__":
    spot_obj = SpotOrderManager()
    futures_obj = FuturesOrderManager()

    target_symbol = "xrpusdt"
    spot_data = spot_obj.fetch_order_status(target_symbol)  # symbol=target_symbol)
    futures_data = futures_obj.fetch_order_status(
        target_symbol
    )  # symbol=target_symbol)

    max_lever = futures_obj.get_max_leverage(symbol="adausdt")
