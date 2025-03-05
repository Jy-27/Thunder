import aiohttp
import asyncio
import time
import hashlib
import hmac
from typing import Dict, Optional

class TradingClient:
    """
    🔥 트레이딩과 관련된 클라이언트다. 코드를 최대한 간단하고 핵심기능만 부여한다.
    
    Alias: Tr_client
    """
    BASE_URL = ""  # 자식 클래스에서 URL을 설정해야 합니다.

    def __init__(self, api_key: str, secret: str):
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

    def _sign_params(self, params: Dict) -> Dict:
        """
        👻 API 요청의 매개변수에 서명을 추가한다.
        """
        query_string = "&".join([f"{key}={value}" for key, value in params.items()])
        signature = hmac.new(
            self._secret_key.encode("utf-8"),
            query_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        params["signature"] = signature
        return params

    async def _send_request(self, method: str, endpoint: str, params: dict) -> dict:
        """
        👻 API 요청 생성 및 서버 전송, 응답 처리한다.
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        params = self._sign_params(params)
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, headers=headers, params=params) as response:
                response.raise_for_status()
                return await response.json()

    async def send_fund_transfer(self, amount: float, transfer_type: int, asset: str = "USDT") -> Dict:
        """⭕️ Spot 🔄 Futures 지갑간 자금이체를 처리한다."""
        url = "https://api.binance.com/sapi/v1/futures/transfer"
        params = {
            "asset": asset.upper(),
            "amount": amount,
            "type": transfer_type,
            "timestamp": int(time.time() * 1000),
        }
        return await self._send_request("POST", url, params)

    async def fetch_account_balance(self) -> Dict:
        """현물시장, 선물시장 계좌 잔고 조회"""
        endpoint = "/api/v3/account" if "https://api.binance.com" in self.BASE_URL else "/fapi/v2/account"
        params = {"timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    async def fetch_order_status(self, symbol: Optional[str] = None) -> Dict:
        """미체결 주문상태 조회 및 반환"""
        endpoint = "/api/v3/openOrders" if "https://api.binance.com" in self.BASE_URL else "/fapi/v1/openOrders"
        params = {"timestamp": int(time.time() * 1000)}
        if symbol:
            params["symbol"] = symbol
        return await self._send_request("GET", endpoint, params)

    async def fetch_order_history(self, symbol: str, limit: int = 500) -> Dict:
        """전체 주문 내역을 조회"""
        endpoint = "/api/v3/allOrders" if "https://api.binance.com" in self.BASE_URL else "/fapi/v1/allOrders"
        params = {"symbol": symbol, "limit": limit, "timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    async def fetch_trade_history(self, symbol: str, limit: int = 500) -> Dict:
        """⭕️ 지정 심볼값의 거래내역을 조회한다."""
        endpoint = "/api/v3/myTrades" if "https://api.binance.com" in self.BASE_URL else "/fapi/v1/userTrades"
        params = {"symbol": symbol, "limit": limit, "timestamp": int(time.time() * 1000), "recvWindow": 5000}
        return await self._send_request("GET", endpoint, params)

    async def fetch_order_details(self, symbol: str, order_id: int) -> Dict:
        """현재 주문 상태를 상세히 조회한다. (체결, 미체결)"""
        endpoint = "/api/v3/order" if "https://api.binance.com" in self.BASE_URL else "/fapi/v1/order"
        params = {"symbol": symbol, "orderId": order_id, "timestamp": int(time.time() * 1000)}
        return await self._send_request("GET", endpoint, params)

    async def send_cancel_order(self, symbol: str, order_id: int) -> Dict:
        """미체결 주문을 취소한다."""
        endpoint = "/api/v3/order" if "https://api.binance.com" in self.BASE_URL else "/fapi/v1/order"
        params = {"symbol": symbol, "orderId": order_id, "timestamp": int(time.time() * 1000)}
        return await self._send_request("DELETE", endpoint, params)
