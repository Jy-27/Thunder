import os, sys
from typing import Dict

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming

symbols = Streaming.symbols
keys = [
    "initialMargin",
    "maintMargin",
    "unrealizedProfit",
    "positionInitialMargin",
    "openOrderInitialMargin",
    "leverage",
    "isolated",
    "entryPrice",
    "breakEvenPrice",
    "maxNotional",
    "positionSide",
    "positionAmt",
    "notional",
    "isolatedWallet",
    "updateTime",
    "bidNotional",
    "askNotional",
]
class SubStatus:
    """
    심볼에 저장될 자세한 정보사항을 저장하는 스토리지다.

    Raises:
        AttributeError: 매개변수에 field값 누락시
        ValueError: 키값이 존재하지 않을 시

    Returns:
        _type_: _description_
    """
    __slots__ = tuple(keys)
    
    def set_data(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__slots__:  # 유효한 필드만 설정
                setattr(self, k, v)

    def to_dict(self):
        return {slot: getattr(self, slot) for slot in self.__slots__}

    def get_data(self, key: str):
        if key not in self.__slots__:
            raise ValueError(f"key 입력 오류: {key}")
        return getattr(self, key)

    def get_fields(self):
        return self.__slots__

    def __repr__(self):
        return str(self.to_dict())


class PositionsStatus:
    __slots__ = tuple(symbols)

    def __init__(self):
        self.clear()

    def set_data(self, data: Dict):
        """
        심볼에 해당 데이터를 저장한다.

        Args:
            symbol (str): 심볼값
            data (Dict): 데이터값

        Raises:
            ValueError: 심볼값 오입력시
        """
        symbol = data["symbol"]
        if symbol not in self.__slots__:
            raise ValueError(f"{symbol}은 존재하지 않는 심볼입니다.")
        setattr(self, symbol, SubStatus())
        getattr(self, symbol).set_data(**data)
        
    def get_symbol_data(self, symbol: str):
        """
        심볼에 저장된 값을 Dict형태로 불러온다

        Args:
            symbol (str): 심볼값

        Raises:
            ValueError: 심볼값 오입력시

        Returns:
            Dict: dict 형태 데이터
        """
        if symbol not in self.__slots__:
            raise ValueError(f"{symbol}은 존재하지 않는 심볼입니다.")
        return getattr(self, symbol).to_dict()
    
    def get_field_data(self, symbol: str, field: str):
        """
        심볼에 저장된 지정 값만 반환한다.

        Args:
            symbol (str): 심볼값
            field (str): key값

        Raises:
            ValueError: 심볼입력 오류시

        Returns:
            any: 지정값
        """
        if symbol not in self.__slots__:
            raise ValueError(f"{symbol}은 존재하지 않는 심볼입니다.")
        return getattr(self, symbol).get_data(field)
    
    def get_main_fields(self):
        """
        slots에 저장된 symbol 리스트를 반환한다.

        Returns:
            List : 속성명
        """
        return list(self.__slots__)
    
    def to_dict(self):
        """
        저장된 전체(하위 포함) 데이터를 Dict형태로 변환하여 반환한다.

        Returns:
            Dict: 전체 데이터
        """ 
        result = {}
        for symbol in self.__slots__:
            symbol_data = getattr(self, symbol)
            if isinstance(symbol_data, list):
                result[symbol] = None
            else:
                result[symbol] = symbol_data.to_dict()
        return result                
    
    def clear(self):
        for attr in self.__slots__:
            # setattr(self, attr, SubStatus())
            setattr(self, attr, [])
    
    def __repr__(self):
        """
        출력용

        Returns:
            _type_: _description_
        """
        return str(self.to_dict())
