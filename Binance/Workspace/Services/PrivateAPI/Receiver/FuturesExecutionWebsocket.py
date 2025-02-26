from .ExecutionWebsocket import ExecutionWebsocket

class FuturesExecutionWebsocket(ExecutionWebsocket):
    """
    Futures 시장의 사용자 체결정보를 웹소켓으로 실시간 수신받는다.
    
    Alias: futures_exe_ws

    Args:
        ExecutionWebsocket (class): 클라스 상속
    """
    market_base_url = "https://fapi.binance.com"
    websocket_base_url = "wss://fstream.binance.com/ws/"
    endpoint = "/fapi/v1/listenKey"
    def __init__(self, **kwarage):
        """
        Args:
            api_key (str): binance api key
        """
        super().__init__(kwarage['apiKey'], self.market_base_url, self.websocket_base_url, self.endpoint)
        
# 출력예시

# {'e': 'TRADE_LITE',
#  'E': 1740017265075,
#  'T': 1740017265075,
#  's': 'ADAUSDT',
#  'q': '7',
#  'p': '0.00000',
#  'm': False,
#  'c': 'ios_BWnHOM6ogm5sX3IdMdxe',
#  'S': 'SELL',
#  'L': '0.77680',
#  'l': '7',
#  't': 1405311723,
#  'i': 50561165509}