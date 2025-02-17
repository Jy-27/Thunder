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
    BASE_URL = ""  # 자식 클래스에서 URL을 설정해야 합니다.

    def __init__(self, api_file_path: str):
        """API 키 파일을 로드하고, API 키와 시크릿 키를 설정"""
        data = self._load_api_keys(api_file_path)

        self._api_key = data["apiKey"]
        self._secret_key = data["secret"]

    def _load_api_keys(self, api_file_path: str) -> Dict[str, str]:
        """API 주문에 필요한 API-key와 Secret-key를 저장한 JSON 파일을 불러옴"""
        try:
            with open(api_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if "apiKey" not in data or "secret" not in data:
                raise KeyError("JSON 파일에 'apiKey' 또는 'secret' 키가 없습니다.")

            return data

        except FileNotFoundError:
            raise FileNotFoundError(f"파일이 존재하지 않습니다: {api_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"올바른 JSON 형식이 아닙니다: {api_file_path}")

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

        # if response.status_code != 200:
        #     print("Error Response:", response.text)
        #     response.raise_for_status()

        # TEST ZONE - 응답 상태 코드와 응답 메시지 출력
        # print("Response Status Code:", response.status_code)
        # print("Response Text:", response.text)

        response.raise_for_status()
        return response.json()

    def send_fund_transfer(
        self, amount: float, transfer_type: int, asset: str = "USDT"
    ) -> Dict:
        """
        1. 기능: 잔액을 Spot과 Futures 계좌 간 전송한다.
        2. 매개변수:
            1) asset: 전송할 자산명 (예: USDT)
            2) amount: 전송할 금액
            3) transfer_type: 전송 유형 (1: Spot → Futures, 2: Futures → Spot)
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
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("GET", endpoint, params)

    # 미체결 취소 주문 생성 및 제출
    def send_cancel_order(self, symbol: str, order_id: int) -> Dict:
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
            "symbol": symbol,
            "orderId": order_id,
            "timestamp": int(time.time() * 1000),
        }
        return self._send_request("DELETE", endpoint, params)