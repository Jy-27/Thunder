import requests
import time
import hashlib
import hmac
import json
import os
import utils
from typing import Dict, Optional, List, Union, Any


class BinanceOrderManager:
    BASE_URL = ""  # 자식 클래스에서 URL을 설정해야 합니다.

    def __init__(self):
        data = self.load_api_keys()

        if data is None:
            raise ValueError("API 키와 시크릿 키를 로드할 수 없습니다.")

        self._api_key = data["apiKey"]
        self._secret_key = data["secret"]
        self.account_balance: Optional[Union[Dict]] = None

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
    def _get_headers(self) -> Dict[str, str]:
        """
        1. 기능 : API에 필요한 headers생성
        2. 매개변수 : 해당없음.
        """
        return {"X-MBX-APIKEY": self._api_key}

    # API 요청의 매개변수 서명 추가
    def _sign_params(self, params: Dict) -> Dict:
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
    def _send_request(self, method: str, endpoint: str, params: dict) -> dict:
        """
        1. 기능 : API 요청을 생성 및 서버로 전송, 응답처리
        2. 매개변수
            1) method : 각 함수별 요청내용
            2) endpoint : 각 함수별 ENDPOINT
            3) params : 각 함수별 수집된 params
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        params = self._sign_params(params)

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
    def fetch_account_balance(self) -> Dict:
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
        return self._send_request("GET", endpoint, params)

    # Ticker의 미체결 주문상태 조회 및 반환
    def fetch_order_status(self, symbol: Optional[str] = None) -> Dict:
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
        return self._send_request("GET", endpoint, params)

    # Ticker의 전체 주문내역 조회 및 반환
    def fetch_order_history(self, symbol: str, limit: int = 500) -> Dict:
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
        return self._send_request("GET", endpoint, params)

    # Ticker의 거래내역 조회 및 반환
    def fetch_trade_history(self, symbol: str, limit: int = 500) -> Dict:
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
        return self._send_request("GET", endpoint, params)

    # 현물시장 또는 선물시장 주문 생성 및 제출
    def submit_market_order(
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
        1. 기능 : 현물시장 또는 선물시장 주문을 넣는다.ABC
        2. 매개변수
            1) 공통
                - symbol : 쌍거래 자산
                - type : 주문 타입
                    >> "LIMIT" : 지정가
                    >> "MARKET" : 시장가
                    >> "STOP_MARKET" : StopLoss 설정시
                    >> "TAKE_PROFIT_MARKET" : 수익실현 설정시, 지정가 도달시 시장가 주문 실행
                - quantity : 거래 주문 수량
                - price : 주문 단가 (type : LIMIT일때만)

            2) 현물거래 (Spot)
                - side : 주문 방향 결정
                    >> "BUY" : 매수
                    >> "SELL" : 매도
            3) 선물거래 (Futures)
                - time_in_force : 주문유효기간
                    >> "GTC" : 사용자가 취소할떄까지 유지
                    >> "IOC" : 주문 즉시 체결 가능한 부분만 체결, 나머지 취소
                    >> "FOK" : 주문 전체가 체결되지 않으면 주문을 취소
                - position_side : 포지션 방향 설정
                    >> "BOTH" : 방향을 지정하지 않고 포지션 유지
                    >> "LONG" : 롱 포지션
                    >> "SHORT" : 숏 포지션
                - reduce_only : 포지션 청산시에 사용.
                    >> True : 소량 자산 포지션 종료.
                    >> False : 일반 주문
        """
        endpoint = (
            "/fapi/v1/order"
            if "https://fapi.binance.com" in self.BASE_URL
            else "/api/v3/order"
        )

        # 공통 및 선물 거래 파라미터
        params = {
            "symbol": symbol.upper(),
            "side": side.upper(),  # BUY or SELL
            "type": order_type,  # LIMIT, MARKET, etc.
            "quantity": quantity,
            "timestamp": int(time.time() * 1000),
        }
        # 지정가 주문과 선물 거래 시 필요한 추가 파라미터 설정
        if order_type == "LIMIT":
            params["timeInForce"] = time_in_force  # 기본값은 GTC

        if price:
            params["price"] = price  # 가격이 있을 경우 지정가 주문으로 처리

        # 선물 거래 옵션
        params["positionSide"] = position_side  # 포지션 방향
        params["reduceOnly"] = "true" if reduce_only else "false"

        return self._send_request("POST", endpoint, params)

    # 현재 보유중인 자산 전체를 매각 정리한다.
    # def sumit_liquidate_all_holdings(self):

    # 현재 주문상태를 상세 조회(체결, 미체결 등등...)
    def fetch_order_details(self, symbol: str, order_id: int) -> Dict:
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
        return self._send_request("GET", endpoint, params)

    # 미체결 취소 주문 생성 및 제출
    def submit_cancel_order(self, symbol: str, order_id: int) -> Dict:
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
        return self._send_request("DELETE", endpoint, params)


class SpotOrderManager(BinanceOrderManager):
    BASE_URL = "https://api.binance.com"


class FuturesOrderManager(BinanceOrderManager):
    BASE_URL = "https://fapi.binance.com"

    # Ticker의 leverage 정보 수신 및 반환
    def _get_leverage_brackets(self, symbol: str) -> Dict:
        """
        1. 기능 : 선물거래 레버리지 설정값 정보 수신
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
        3. 반환
            - 각 심볼에 대한 레버리지 구간 정보를 포함한 리스트
        """
        endpoint = "/fapi/v1/leverageBracket"
        params = {"symbol": symbol.upper(), "timestamp": int(time.time() * 1000)}
        return self._send_request("GET", endpoint, params)

    # Ticker의 MAX leverage값 반환
    def get_max_leverage(self, symbol: str) -> int:
        """
        1. 기능 : 선물거래 ticker에 대한 MAX leverage값 반환
        2. 매개변수
            1) symbol : BTCUSDT (symbols 타입 입력안됨.)
        """
        brackets_data = self._get_leverage_brackets(symbol=symbol)

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
    def set_leverage(self, symbol: str, leverage: int) -> dict:
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
        return self._send_request("POST", endpoint, params)

    # Ticker의 margin type 설정
    def set_margin_type(self, symbol: str, margin_type: str) -> dict:
        """
        1. 기능 : 마진 타입 설정
        2. 매개변수
            1) margin_type
                >> "CROSSED" : 교차 마진
                >> "ISOLATED" : 격리 마진
        """
        margin_type = margin_type.upper()
        endpoint = "/fapi/v1/marginType"
        params = {
            "symbol": symbol.upper(),
            "marginType": margin_type,  # "ISOLATED" 또는 "CROSSED"
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("POST", endpoint, params)


if __name__ == "__main__":
    spot_obj = SpotOrderManager()
    futures_obj = FuturesOrderManager()

    target_symbol = "xrpusdt"
    spot_data = spot_obj.fetch_order_status(target_symbol)  # symbol=target_symbol)
    futures_data = futures_obj.fetch_order_status(
        target_symbol
    )  # symbol=target_symbol)

    max_lever = futures_obj.get_max_leverage(symbol="adausdt")
