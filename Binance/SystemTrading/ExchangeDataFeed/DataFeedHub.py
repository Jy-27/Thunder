class ExchangeDataRouter:
    def __init__(self):
        self.public_rest_fetcher = PublicRestFetcher()
        self.private_rest_fetcher = PrivateRestFetcher()
        self.public_ws_receiver = PublicWebsocketReceiver()
        self.private_ws_receiver = PrivateWebsocketReceiver()

# REST Fetchers
class PublicRestFetcher:
    def __init__(self):
        pass  # 퍼블릭 REST API 요청 초기화



class PrivateRestFetcher:
    def __init__(self):
        pass  # 프라이빗 REST API 요청 초기화

# Websocket Receivers
class PublicWebsocketReceiver:
    def __init__(self):
        pass  # 퍼블릭 웹소켓 수신 초기화

class PrivateWebsocketReceiver:
    def __init__(self):
        pass  # 프라이빗 웹소켓 수신 초기화
