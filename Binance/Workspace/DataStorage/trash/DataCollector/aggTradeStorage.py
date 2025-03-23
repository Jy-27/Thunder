from collections import deque
from typing import List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils
from SystemConfig import Streaming

class aggTradeStorage:
    """
    Websocket stream (aggTrade) 데이터를 저장하기 위한 저장소이다.
    매물대 계산을 위해 틱거래 내역을 저장한다.

    Raises:
        AttributeError: 속성값 오입력시

    Returns:
        list: 트레이딩 데이터
    """
    execution_types = ["taker", "maker"]
    __slots__ = [attr + "_" + symbol for attr in execution_types for symbol in Streaming.symbols]
    
    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, deque())
    
    def __validate_attr(self, attr_name:str):
        if attr_name not in self.__slots__:
            raise AttributeError(f"🚨 '{attr_name}' 속성이 존재하지 않음..")
    
    def add_data(self, data):
        """지정된 symbol과 execution_type에 데이터 추가"""
        symbol, execution_type, data = tr_utils.Convertor.agg_trade_message(data)
        attr_name = f"{execution_type}_{symbol}"
        self.__validate_attr(attr_name)
        getattr(self, attr_name).append(data)
    
    def get_data(self, symbol: str, execution_type: str) -> List:
        attr_name = f"{execution_type}_{symbol}"
        self.__validate_attr(attr_name)
        deque_ = getattr(self, attr_name)
        if deque_:
            deque_.popleft()
        else:
            return None
    
    def clear(self, symbol:str, execution_type: str):
        attr_name = f"{execution_type}_{symbol}"
        self.__validate_attr(attr_name)
        getattr(self, attr_name).clear()
    
    def get_all_data(self, symbol:str, execution_type:str) -> List:
        attr_name = f"{execution_type}_{symbol}"
        self.__validate_attr(attr_name)
        deque_ = getattr(self, attr_name)
        if deque_:
            data = list(getattr(self, attr_name))
            self.clear(symbol, execution_type)
            return data
        else:
            return None

from collections import deque

class AggTradeDeque:
    __slots__ = ("latest_data", "deque")

    def __init__(self, maxlen: int = 300):
        self.latest_data = None
        self.deque = deque(maxlen=maxlen)

    def update(self, data):
        """데이터 업데이트 및 deque에 추가"""
        self.latest_data = data
        self.deque.append(data)

    def get_latest_data(self):
        """가장 최근 데이터를 반환"""
        return self.latest_data

    def get_all_data(self):
        """deque의 모든 데이터를 반환"""
        return list(self.deque)

    def __repr__(self):
        return f"AggTradeDeque(latest_data={self.latest_data}, deque_length={len(self.deque)})"


if __name__ == "__main__":
    from Workspace.Services.PublicData.Receiver.FuturesMarketWebsocket import FuturesMarketWebsocket
    from SystemConfig import Streaming
    import asyncio
    
    storage = aggTradeStorage()
    stream = 'aggTrade'
    count = 100
    async def main():
        obj = FuturesMarketWebsocket(Streaming.symbols)
        print(f"  ⏳ Websocket({stream}) 연결중...")
        await obj.open_stream_connection(stream)
        print(f"  🔗 Websocket({stream}) 연결 성공")
        
        print(f"  🚀 Websocket({stream}) {count} 번 수신 시작")
        for i in range(count):
            # print(i)
            data = await obj.receive_message()    
            storage.add_data(data)
            if i > 80:
                print(data)
        
        print(f"  ✅ Websocket({stream}) {count} 번 수신 완료")
        await obj.close_connection()
        print(f"  ⛓️‍💥 Websocket({stream}) 연결 해제")
        
    asyncio.run(main())
