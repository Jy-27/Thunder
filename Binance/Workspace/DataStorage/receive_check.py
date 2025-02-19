from typing import List


class ReceiveCheck:
    """
    websocket 데이터 수신결과를 체크하는 클라스다.
    
    웹소켓 수신 완료시 타임슬립을 주기 위하여 구현하였다.
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

if __name__ =="__main__":
    symbols = ['BTCUSDT', 'XRPUSDT', 'TRXUSDT']
    intervals = ['1m', '3m', '5m']
    
    storage_ = ReceiveCheck(symbols, intervals)