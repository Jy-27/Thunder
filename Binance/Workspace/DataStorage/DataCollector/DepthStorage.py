from collections import deque
from typing import List, Dict

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.Utils.TradingUtils as tr_utils
from SystemConfig import Streaming

class DepthStorage:
    """
    Websocket stream (depth) 데이터를 누적 저장한다.
    orderbook을 분석하기 위함이다.

    Raises:
        AttributeError: 속성값 오입력시

    Returns:
        Dict: 수신된 depth데이터 리스트
    """
    __slots__ = tuple(Streaming.symbols)
 
    def __init__(self, deque_len: int=300):
        for attr in self.__slots__:
            setattr(self, attr, deque(maxlen=deque_len))
    
    def __validate_attr(self, attr_name:str):
        """
        👻 속성값 존재여뷰 점검한다.

        Args:
            attr_name (str): 속성값 이름

        Raises:
            AttributeError: 속성값 없을시
        """
        if attr_name not in self.__slots__:
            raise AttributeError(f"🚨 '{attr_name}' 속성이 존재하지 않음..")
    
    def add_data(self, data:Dict):
        """
        데이터를 추가한다.

        Args:
            data (dict): websocket stream(depth) message
        """
        symbol = data["data"]["s"]
        self.__validate_attr(symbol)
        getattr(self, symbol).append(data)

    def get_data(self, symbol:str) -> Dict:
        """
        데이터를 불러온다. 불러온 데이터는 소거된다. (deque)

        Args:
            symbol (str): 속성값

        Returns:
            Dict: websocket stream(depth) message
        """
        self.__validate_attr(symbol)
        deque_ = getattr(self, symbol)
        if deque_:
            return getattr(self, symbol).popleft()
        else:
            return None
    
    def clear(self, symbol:str):
        """
        🧹 해당 속성값의 데이터를 지운다.

        Args:
            symbol (str): 속성값
        """
        self.__validate_attr(symbol)
        getattr(self, symbol).clear()
    
    def get_all_data(self, symbol:str) -> List:
        """
        원하는 속성값 전체를 리스트값으로 반환한다. 반환된 데이터는 소거된다.

        Args:
            symbol (str): 속성값

        Returns:
            List: 속성에 저장된 전체 값
        """
        self.__validate_attr(symbol)
        deque_ = getattr(self, symbol)
        if deque_:
            result = list(deque_)
            self.clear(symbol)
            return result
        else:
            return None
        
        

        
