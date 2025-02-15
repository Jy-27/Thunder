import aiohttp
import json
import asyncio
import datetime
from typing import Final, Dict, List, Union, Optional


class ReciverAPI:
    """
    Binance OPEN API 데이터를 수신한다. 별도의 API KEY가 필요 없다.
    """

    def __init__(self, base_url: str, intervals: Union[list, str]):
        self.BASE_URL: str = base_url
        self.asyncio_queue: asyncio.Queue = asyncio.Queue()
        self.stream_type: Optional[str] = None

        self.stop_event = asyncio.Event()
        # KLINE(OHLCV) 데이터를 수신하기 위한 interval 값으로, 앞에 'kline_' 접두사를 추가로 붙여야 한다.
        self.intervals: Final[List] = [
            intervals if isinstance(intervals, str) else intervals
        ]
        # OPEN API 데이터 수신을 위한 ENDPOINT, kline의 경우 for 함수를 이용하여 별도로 붙였다.
        self.ENDPOINT: Final[List[str]] = [
            "ticker",
            "trade",
            "miniTicker",
            *[f"kline_{i}" for i in intervals],
            "depth",
            "24hrTicker",
            "aggTrade",
        ]

    # endpoint 유효성 검사 후 반환
    def _normalize_endpoint(self, endpoint: str) -> str:
        """
        1. 기능 : 최종 base url + endpoint 생성전 유효성 검사.
        2. 매개변수
            1) endpoint : 각 용도별 endpoint 입력
        3. 반환값 : 없음.
        """

        if endpoint in self.ENDPOINT:
            return endpoint
        else:
            raise ValueError(
                f"endpoint 입력오류: '{endpoint}'는 지원되지 않는 타입입니다."
            )

    # websocket 연결하고자 하는 url 생성 및 반환
    def _streams(self, symbols: Union[list, str], ws_type: Union[list, str]) -> str:
        """
        1. 기능 : websocket 타입별 url 생성
        2. 매개변수
            1) symbols : List 또는 str타입으로 쌍거래 심볼 입력
            2) ws_type : kline 또는 stream
        3. 반환값 : 없음.
        """
        if isinstance(symbols, str):
            symbols = [symbol]# for symbol in symbols]
        if isinstance(ws_type, str):
            ws_type = [ws_type]# for type_ in ws_type]

        endpoints = [self._normalize_endpoint(endpoint) for endpoint in ws_type]
        return self.BASE_URL + "/".join(
            [
                f"{symbol.lower()}@{endpoint}"
                for symbol in symbols
                for endpoint in endpoints
            ]
        )

    # websocket 데이터 수신 메시지 발생기
    async def _handler_message(self, ws) -> None:
        """
        1. 기능 : websocket 데이터 수신 및 queue.put처리
        2. 매개변수
            1) ws : websocket 정보
        3. 반환값 : 없음.
        """

        self.stop_event.clear()
        while not self.stop_event.is_set():
            message = await ws.receive()
            if message.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(message.data)
                # DEBUG
                print(data)
                await self.asyncio_queue.put(data)
            elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                break
        await ws.close()
        print("WebSocket connection closed.")

    # websocket 함수 집합 및 실행
    async def _start_websocket(self, url: str) -> None:
        """
        1. 기능 : websocket 실행
        2. 매개변수
            1) url : 함수 __streams에서 생성 및 반환값
        3. 반환값 : 없음.
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print("WebSocket connection opened.")
                await self._handler_message(ws)

    # websocket stream type 최종 실행
    async def connect_stream(self, symbols: list, stream_type: str):
        """
        ⭕️ 지정하는 stream 타입별로 데이터를 수신한다.

        Args:
            symbols (list): ['BTCUSDT', 'XRPUSDT']
            stream_type (str): self.ENDPOINT(kline 외) 참조
        """
        self.stream_type = stream_type
        url = self._streams(symbols=symbols, ws_type=stream_type)
        await self._start_websocket(url)

    # websocket kline type 최종 실행
    async def connect_kline_limit(self, symbols: list, intervals: Optional[Union[str, list]]=None):
        """
        ⭕️ Kline(OHLCV)형태의 데이터를 수신한다.

        Args:
            symbols (list): ['BTCUSDT', 'XRPUSDT']
            intervals (Optional[Union[str, list]], optional): 'kline_3m'
        
        Notes:
            intervals값을 None으로 할 경우 매개변수의 intervals값 전체를 수신하고, 지정 interval 필요시
            선언된 매개변수(interval)값 내에서 지정해야함.
        """
        self.stream_type = "kline"
        if intervals is None:
            intervals = [interval for interval in self.ENDPOINT if self.stream_type in interval]
        url = self._streams(symbols=symbols, ws_type=intervals)
        await self._start_websocket(url)