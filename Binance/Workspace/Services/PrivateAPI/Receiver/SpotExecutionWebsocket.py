from .ExecutionWebsocket import ExecutionWebsocket


class SoptExcutionWebsocket(ExecutionWebsocket):
    market_base_url = "https://api.binance.com"
    websocket_base_url = "wss://stream.binance.com/ws/"
    endpoint = "/api/v3/userDataStream"
    def __init__(self, api_key:str):
        super().__init__(api_key, self.market_base_url, self.websocket_base_url, self.endpoint)