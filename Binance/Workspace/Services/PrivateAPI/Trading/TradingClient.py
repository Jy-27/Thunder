import aiohttp
import asyncio
import time
import hashlib
import hmac
import json
import os
import math
import requests
from typing import Dict, Optional, List, Union, Any, cast
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from abc import ABC, abstractmethod

class TradingClient:
    """
    🔥 트레이딩과 관련된 클라이언트다. 코드를 최대한 간단하고 핵심기능만 부여한다.
    
    Alias: Tr_client
    """
    BASE_URL = ""  # 자식 클래스에서 URL을 설정해야 합니다.

    def __init__(self, api_key:str, secret:str):
        """API 키 파일을 로드하고, API 키와 시크릿 키를 설정"""
        self._api_key = api_key
        self._secret_key = secret

    def _get_headers(self) -> Dict[str, str]:
        """
        👻 API에 필요한 headers를 생성한다.

        Returns:
            Dict[str, str]: headers값
        """
        return {"X-MBX-APIKEY": self._api_key}

    # API 요청의 매개변수 서명 추가
    def _sign_params(self, params: Dict) -> Dict:
        """
        👻 API 요청의 매개변수에 서명을 추가한다.

        Args:
            params (Dict): 요청관련 정보

        Returns:
            Dict: 서명추가 params
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
        👻 API 요청 생성 및 서버 전송, 응답 처리한다.

        Args:
            method (str): 수행 작업 지시
            endpoint (str): endpoint 주소
            params (dict): 함수별 수집된 params

        Returns:
            dict: 처리결과 피드백
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        params = self._sign_params(params)

        response = requests.request(method, url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def send_fund_transfer(
        self, amount: float, transfer_type: int, asset: str = "USDT"
    ) -> Dict:
        """
        ⭕️ Spot 🔄 Futures 지갑간 자금이체를 처리한다.

        Args:
            amount (float): 이체하고자 하는 금액 (asset설정 기준)
            transfer_type (int): 이체 방향
                - 1: Spot 👉🏻 Futures
                - 2: Futures 👉🏻 Spot
            asset (str, optional): 전송할 자산명(예: USDT)

        Returns:
            Dict: 처리결과 피드백
        """
        # futures base url은 지원 안함.
        url = "https://api.binance.com/sapi/v1/futures/transfer"
        params = {
            "asset": asset.upper(),
            "amount": amount,
            "type": transfer_type,
            "timestamp": int(time.time() * 1000),
        }
        method = "POST"

        headers = self._get_headers()
        params = self._sign_params(params)

        response = requests.request(method, url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    # 현물시장, 선물시장 계좌 잔고 조회
    def fetch_account_balance(self) -> Dict:
                

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
        미체결 주문상태를 조회한다.

        Args:
            symbol (str, optional): 심볼값
        
        Returns:
            _type_: 조회 결과값
        """

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
        전체 주문 내역을 조회한다.(체결, 미체결, 취소 등등)

        Args:
            symbol (str): 심볼값
            limit (int, optional): 검색량 (max 500)

        Returns:
            Dict: 주문내역 결과값
        """
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
        ⭕️ 지정 심볼값의 거래내역을 조회한다.

        Args:
            symbol (str): 심볼값
            limit (int, optional): 검색량 (max 500)

        Returns:
            Dict: 조회 결과
        """

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

    # 현재 주문상태를 상세 조회(체결, 미체결 등등...)
    def fetch_order_details(self, symbol: str, order_id: int) -> Dict:
        """
        현재 주문 상태를 상세히 조회한다. (체결, 미체결)

        Args:
            symbol (str): 심볼값
            order_id (int): 주문 ID (fetch_order_history에서 조회)

        Returns:
            Dict: 결과값
        """
        endpoint = (
            "/api/v3/order"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/order"
        )
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("GET", endpoint, params)

    # 미체결 취소 주문 생성 및 제출
    def send_cancel_order(self, symbol: str, order_id: int) -> Dict:
        """
        미체결 주문을 취소한다.

        Args:
            symbol (str): 심볼값
            order_id (int): 주문 ID (fetch_order_history에서 조회)

        Returns:
            Dict: 결과 피드백
        """
        endpoint = (
            "/api/v3/order"
            if "https://api.binance.com" in self.BASE_URL
            else "/fapi/v1/order"
        )
        params = {
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("DELETE", endpoint, params)
    
    
