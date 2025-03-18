from SystemConfig import Streaming
from typing import Dict

symbols = Streaming.symbols
order_types = ("STOP_MARKET", "TAKE_PROFIT_MARKET", "LIMIT")
data_keys = ('orderId', 'status', 'clientOrderId', 'price', 'avgPrice', 'origQty', 'executedQty', 'cumQuote',
             'timeInForce','type', 'reduceOnly', 'closePosition', 'side', 'positionSide', 'stopPrice', 'workingType',
             'priceProtect', 'origType', 'priceMatch', 'selfTradePreventionMode', 'goodTillDate', 'time', 'updateTime')

class OrderStatus:
    """
    미체결 주문을 기록한다.

    Returns:
        _type_: _description_
    """
    __slots__ = tuple(symbols)
    def __init__(self):
        self.clear()
    
    def clear(self):
        for attr in self.__slots__:
            setattr(self, attr, SymbolStorage())

    def set_data(self, data:Dict):
        symbol = data["symbol"]
        getattr(self, symbol).set_data(data)
    
    def get_data(self, symbol:str, order_type:str):
        symbol_data = getattr(self, symbol)
        if hasattr(symbol_data, order_type):
            return symbol_data.get_data(order_type)
        else:
            return None
    
    def get_fields(self):
        return list(self.__slots__)
    
    def to_dict(self):
        result = {}
        for attr in self.__slots__:
            data = getattr(self, attr)
            if isinstance(data, list):
                continue
            result[attr] = getattr(self, attr).to_dict()
        return result

    def __repr__(self):
        return str(self.to_dict())

class SymbolStorage:
    """
    중간 위치 저장 storage다.

    Returns:
        _type_: _description_
    """
    __slots__ = order_types
    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, [])
    
    def set_data(self, data):
        order_type = data['type']
        setattr(self, order_type, TypeStoreage())
        getattr(self, order_type).set_data(**data)
        
        ### DEBUG ###
        print(getattr(self, order_type))
    
    def get_data(self, order_type:str):
        return getattr(self, order_type)
    
    def get_data_detail(self, order_type:str, last_key:str):
        return getattr(self, order_type).get_data(last_key)
    
    def get_fields(self):
        return list(self.__slots__)
    
    def to_dict(self):
        result = {}
        for attr in self.__slots__:
            if isinstance(getattr(self, attr), list):
                continue
            result[attr] = getattr(self, attr).to_dict()
        return result

class TypeStoreage:
    """
    최하위 저장 storage

    Returns:
        _type_: _description_
    """
    __slots__ = data_keys
    def __init__(self):
        for attr in self.__slots__:
            setattr(self, attr, None)
    
    def set_data(self, **kwargs):
        for k, v in kwargs.items():
            if k in self.__slots__:  # 유효한 필드만 설정
                setattr(self, k, v)
    
    def get_data(self, field:str):
        return getattr(self, field)
    
    def get_fields(self):
        return list(self.__slots__)
    
    def to_dict(self):
        result = {}
        for attr in self.__slots__:
            result[attr] = getattr(self, attr)
        return result