from .ExecutionWebsocket import ExecutionWebsocket

class FuturesExecutionWebsocket(ExecutionWebsocket):
    market_base_url = "https://fapi.binance.com"
    websocket_base_url = "wss://fstream.binance.com/ws/"
    endpoint = "/fapi/v1/listenKey"
    def __init__(self, api_key:str):
        super().__init__(api_key, self.market_base_url, self.websocket_base_url, self.endpoint)
        
        
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