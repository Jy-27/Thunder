import aiohttp
import json
import asyncio
import utils
import datetime
from typing import Union, Final, Dict, List, Union, Optional


class BinanceHandler:
    KLINE_INTERVALS: Final[List] = [
        "1m",
        "3m",
        "5m",
        "15m",
        "30m",
        "1h",
        "2h",
        "4h",
        "6h",
        "8h",
        "12h",
        "1d",
        "3d",
        "1w",
        "1M",
    ]
    ENDPOINT: Final[List[str]] = [
        "ticker",
        "trade",
        "miniTicker",
        *[f"kline_{i}" for i in KLINE_INTERVALS],
        "depth",
        "24hrTicker",
        "aggTrade",
    ]

    def __init__(self, base_url: str):
        self.BASE_URL: str = base_url
        self.asyncio_queue: asyncio.Queue = asyncio.Queue()
        self.stream_type: Optional[str] = None

        self.stop_event = asyncio.Event()

    # endpoint 유효성 검사 후 반환
    def _normalize_endpoint(self, endpoint: str) -> str:
        """
        1. 기능 : 최종 base url + endpoint 생성전 유효성 검사.
        2. 매개변수
            1) endpoint : 각 용도별 endpoint 입력
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
        """
        symbols = utils._str_to_list(symbols)
        ws_type = utils._str_to_list(ws_type)
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
        """

        self.stop_event.clear()
        while not self.stop_event.is_set():
            message = await ws.receive()
            if message.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(message.data)
                await self.asyncio_queue.put(data)
                # print(type(data))
            elif message.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR):
                break
        await ws.close()
        print("WebSocket connection closed.")

    # websocket break 신고 발생기
    async def pause_and_resume_loop(self, sleep_duration: int = 1):
        """
        1. 기능 : tickers 업데이트 stop 신호 발생 또는 진행 신호 발생
        2. 매개변수
            1) sleep_duration : stop 후 대기시간(sec)
        """
        self.stop_event.set()
        await utils._wait_time_sleep(time_unit="second", duration=sleep_duration)
        self.stop_event.clear()
        return utils._get_time_component()

    # websocket 함수 집합 및 실행
    async def _start_websocket(self, url: str) -> None:
        """
        1. 기능 : websocket 실행
        2. 매개변수
            1) url : 함수 _streams에서 생성 및 반환값
        """
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(url) as ws:
                print("WebSocket connection opened.")
                await self._handler_message(ws)

    # websocket stream type 최종 실행
    async def connect_stream(self, symbols: list, stream_type: str):
        """
        1. 기능 : stream type websocket 실행전 url 구성 및 websocket start 함수 실행
        2. 매개변수
            1) symbols : list 또는 str 타입 쌍거래 심볼
            2) ws_type : stream 타입.ENDPOINT 속성의 kline타입 외 전체 참조

        """
        self.stream_type = stream_type
        url = self._streams(symbols=symbols, ws_type=stream_type)
        await self._start_websocket(url)

    # websocket kline type 최종 실행
    async def connect_kline_limit(self, symbols: list, intervals: Union[str, list]):
        """
        1. 기능 : kline type websocket 실행전 url 구성 및 websocket start 함수 실행
        2. 매개변수
            1) symbols : list 또는 str 타입 쌍거래 심볼
            2) ws_type : kline 타입.ENDPOINT 속성의 kline타입 전체 참조

        """
        self.stream_type = "kline"
        url = self._streams(symbols=symbols, ws_type=intervals)
        await self._start_websocket(url)


class SpotHandler(BinanceHandler):
    def __init__(self):
        super().__init__(base_url="wss://stream.binance.com:9443/ws/")


class FuturesHandler(BinanceHandler):
    def __init__(self):
        super().__init__(base_url="wss://fstream.binance.com/ws/")

    # def _streams(self, symbols: Union[list, str], ws_type: Union[list, str]) -> str:
    #     symbols = utils._str_to_list(data=symbols)
    #     ws_type = utils._str_to_list(data=ws_type)
    #     if self.stream_type == "kline":
    #         endpoint_str = "kline_"
    #         ws_type = [endpoint_str + interval for interval in ws_type]
    #     endpoints = [self._normalize_endpoint(endpoint) for endpoint in ws_type]
    #     return self.BASE_URL + "/".join(
    #         [
    #             f"{symbol.lower()}@{endpoint}"
    #             for symbol in symbols
    #             for endpoint in endpoints
    #         ]
    #     )


if __name__ == "__main__":
    spot = SpotHandler()
    futures = FuturesHandler()

    symbols = ["btcusdt", "adausdt", "xrpusdt", "ethusdt"]
    stream = spot.ENDPOINT[0]
    intervals = ["kline_1m", "kline_3m"]

    asyncio.run(spot.connect_kline_limit(symbols=symbols, intervals=intervals))
