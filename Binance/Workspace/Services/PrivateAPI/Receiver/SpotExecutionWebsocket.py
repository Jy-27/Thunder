from .ExecutionWebsocket import ExecutionWebsocket


class SoptExcutionWebsocket(ExecutionWebsocket):
    """
    Spot 시장의 사용자 체결정보를 웹소켓으로 실시간 수신받는다.
    
    Alias: spot_exe_ws

    Args:
        ExecutionWebsocket (class): 클라스 상속
    """
    market_base_url = "https://api.binance.com"
    websocket_base_url = "wss://stream.binance.com/ws/"
    endpoint = "/api/v3/userDataStream"
    def __init__(self, api_key:str):
        super().__init__(api_key, self.market_base_url, self.websocket_base_url, self.endpoint)