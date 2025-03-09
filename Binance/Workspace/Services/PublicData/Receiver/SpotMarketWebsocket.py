from .MarketWebsocket import MarketWebsocket
from typing import Union, List, Final
import asyncio
import aiohttp
import json


class SpotMarketWebsocket(MarketWebsocket):
    """
    ℹ️ Futures 거래내역 웹소켓이다.
    매개변수의 session은 변할일이 없을것으로 판단되어,
    의존성 생성처리 하였다.

    Alias: futures_mk_ws

    Args:
        symbols (List): 심볼 리스트
    """

    def __init__(self, symbols: List):
        super().__init__(base_url="wss://fstream.binance.com::9443", symbols=symbols)
