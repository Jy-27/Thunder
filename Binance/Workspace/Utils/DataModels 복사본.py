from typing import Optional, Dict
from dataclasses import dataclass
import os
import sys


sys.path.append(os.path.abspath("../../../"))
from SystemConfig import Streaming


class SymbolStorage(Streaming):
    """
    ⭕️ symbol별 KlineStorage데이터를 저장한다.

    Notes:
        kline data 저장용으로도 사용하지만, 웹소켓 메시지 저장용으로도 사용가능하다.

    Returns:
        _type_: _description_
    """

    __slots__ = tuple(Streaming.symbols)

    def __init__(self, storage_type):
        self.storage_type = storage_type
        for attr in self.__slots__:
            setattr(self, attr, ㄴㅅ())

    def __repr__(self):
        return "\n".join(f"{attr}: {getattr(self, attr)}" for attr in self.__slots__)

    def clear(self):
        for attr in self.__slots__:
            setattr(self, attr, KlineStorage())

    def update_data(self, symbol: str, interval: str, data: Dict):
        if symbol in self.__slots__:
            kline_data = getattr(self, symbol)
            kline_data.update_data(interval=interval, data=data)
        else:
            raise ValueError(f"지정 외 symbol입력됨: {symbol}")

    def get_data(self, symbol: str, interval: str):
        if symbol in self.__slots__:
            kline_data = getattr(self, symbol)
            return kline_data.get_data(interval=interval)
        else:
            raise ValueError(f"지정 외 symbol입력됨: {symbol}")

    def get_attr(self):
        return self.__slots__


class KlineStorage(Streaming):
    """
    ⭕️ Kline데이터를 interval별로 저장한다.

    Raises:
        ValueError: 잘못된 interval 입력시 오류 발생
    """

    __slots__ = tuple(f"interval_{interval}" for interval in Streaming.intervals)

    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, None)

    def __repr__(self):
        return "\n".join(f"{attr}: {getattr(self, attr)}" for attr in self.__slots__)

    def clear(self):
        # 구현은 했으나 사용하지 않는다.
        for attr in self.__slots__:
            setattr(self, attr, None)

    def update_data(self, interval: str, data: Dict):
        attr = f"interval_{interval}"
        if attr in self.__slots__:
            setattr(self, attr, data)
        else:
            raise ValueError(f"지정 외 interval입력됨: {interval}")

    def get_data(self, interval: str):
        attr = f"interval_{interval}"
        if attr in self.__slots__:
            return getattr(self, attr)
        else:
            raise ValueError(f"지정 외 interval입력됨: {interval}")

    def get_attr(self):
        return self.__slots__
