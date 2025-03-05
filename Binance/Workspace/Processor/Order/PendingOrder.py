from typing import Dict, List
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

import Workspace.DataStorage.NodeStorage as storage
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient as futures_tr_client
import SystemConfig



class PendingOrder:
    def __init__(self, trading_client):
        self.symbols = SystemConfig.Streaming.symbols
        self.pending_type = ["IS_HOLDING", "LIMIT", "TAKE_PROFIT", "TAKE_PROFIT_MARKET", "STOP_MARKET"]
        self.event_type = ["TRADE", "NEW", "CANCEL", "EXPIRED"]
        self.storage = storage.MainStorage(self.symbols, storage.SubStorage(self.pending_type))
        self.trading_client = trading_client

        self.init_update()
            
    def init_update(self):
        account_data = self.trading_client.fetch_account_balance()
        current_position = tr_utils.Extractor.current_positions(account_data)
        
        for symbol in self.symbols:
            order_status = self.trading_client.fetch_order_status(symbol)
            if order_status:
                for status in order_status:
                    order_type = status["type"]
                    price = max(float(status["price"]), float(status["stopPrice"]))
                    self.set_pending_order(symbol, order_type, price)
            
            if symbol in current_position:
                self.set_pending_order(symbol, self.pending_type[0], True)
            else:
                self.set_pending_order(symbol, self.pending_type[0], False)
                

    def validate_field(self, field:str):
        """
        🐣 필드 존재여부를 검토한다. 존재하지 않으면 오류를 발생시킨다.

        Args:
            field (str): 필드명

        Raises:
            ValueError: 필드가 존재 하지 않을 때
        """
        fields = self.storage.get_fields()
        if field not in fields:
            raise ValueError(f"field 입력 오류: {field}")

    def get_pending_order(self, symbol:str) -> Dict:
        """
        🐣 symbol별 pending 데이터를 조회하여 dict타입으로 반환한다.        

        Args:
            symbol (str): 심볼명

            Dict : pending 데이터
        """
        return getattr(self.storage, symbol).to_dict()

    def set_pending_order(self, symbol:str, pending_type:str, price:float):
        """
        🐣 신규 주문 발생시 필드를 업데이트한다.

        Args:
            symbol (str): main field
            pending_type (str): self.pending_type 참조
            price (float): 설정 금액
        """
        self.storage.set_data(symbol, pending_type, price)

    def clear_pending_order(self, symbol:str, pending_type:str):
        """
        🐣 주문 취소시 필드를 초기화 한다.

        Args:
            symbol (str): main field
            pending_type (str): self.pending_type 참조
        """
        self.storage.clear_field(symbol, pending_type)

    def update_order(self, message: Dict):
        """
        🚀 Execution Websocket 정보를 참조하여 업데이트 한다.

        Args:
            message (Dict): Execution Websocket 데이터
        """
        event_type = message.get("e")
        
        if event_type == "TRADE_LITE":  # 체결 발생
            symbol = message["s"]
            order_type = "IS_HOLDING"
            
            if self.storage.get_data(symbol, order_type):
                self.clear_pending_order(symbol, order_type)
            else:
                self.set_pending_order(symbol, order_type, True)
            return
        
        order = message.get("o")
        if not order:
            return
        
        symbol = order["s"]
        order_type = order["o"]
        execution_type = order["x"]
        
        if order_type not in self.pending_type:
            return
        
        if execution_type == "CANCELED":
            self.clear_pending_order(symbol, order_type)
        elif execution_type in {"TRADE", "NEW"}:
            price = max(float(order.get("p", 0)), float(order.get("sp", 0)))
            self.set_pending_order(symbol, order_type, price)


if __name__ == "__main__":
    import SystemConfig
    import Workspace.Utils.BaseUtils as base_utils
    
    path = SystemConfig.Path.bianace
    api = base_utils.load_json(path)
    client = futures_tr_client(**api)
    symbols = ['ADAUSDT', "XRPUSDT"]
    
    obj = PendingOrder(symbols, client)