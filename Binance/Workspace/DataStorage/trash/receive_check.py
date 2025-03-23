from typing import List


class ReceiveCheck:
    """
    ❌websocket 데이터 수신결과를 체크하는 클라스다.
    
    웹소켓 수신 완료시 타임슬립을 주기 위하여 구현하였다.
    
    폐기사유 : 웹소켓에는 time.sleep은 오히려 오버헤드를 증가시킴
    """
    def __init__(self, symbols:List, intervals:List):
        self.init_setup(symbols, intervals)
        
    def init_setup(self, symbols:List, intervals:List):
        for symbol in symbols:
            for interval in intervals:
                setattr(self, f"{symbol}_{interval}", False)
                
    def clear(self):
        for attr in self.__dict__:
            setattr(self, attr, False)

    def update(self, ws_data):
        kline_data = ws_data['k']
        symbol = kline_data['s']
        interval = kline_data['i']
        attr_name = f"{symbol}_{interval}"
        setattr(self, attr_name, True)
        
    def status(self):
        result = []
        for status in self.__dict__:
            result.append(getattr(self, status))
        if all(result):
            self.clear()
            return True
        return False



class SymbolDataSubset:
    """
    ❌ storage 코드 수정되면서 동작 불가함.
    특정 심볼 데이터의 서브셋을 생성하는 클래스"""

    def __init__(self, *symbols:tuple(str), storage:storage):
        """선택한 심볼만 포함하는 객체 생성"""
        self.__class__.__slots__ = symbols  # ✅ __slots__을 동적으로 지정
        for symbol in symbols:
            setattr(self, symbol, getattr(storage, symbol))  # ✅ 해당 심볼 데이터 저장

    def get_data_symbol(self, symbol:str):
        return getattr(self, symbol)

    def get_data_detail(self, symbol: str, interval: str):
        """특정 심볼의 특정 interval 데이터를 가져옴"""
        symbol_obj = getattr(self, symbol)
        interval_key = f"interval_{interval}"
        return getattr(symbol_obj, interval_key)

    def clear(self):
        """저장된 데이터를 초기화"""
        for slot in self.__slots__:
            setattr(self, slot, None)  # ✅ 데이터를 None으로 초기화


if __name__ =="__main__":
    symbols = ['BTCUSDT', 'XRPUSDT', 'TRXUSDT']
    intervals = ['1m', '3m', '5m']
    
    storage_ = ReceiveCheck(symbols, intervals)
    
    