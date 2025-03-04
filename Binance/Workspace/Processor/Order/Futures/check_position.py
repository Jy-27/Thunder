import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet

class OrderValaidate:
    def __init__(self, pending_order:PendingOrder, wallet:Wallet):
        self.pending_order = pending_order
        
    def check_limit_order(self, symbol:str) -> bool:
        pending_order = self.pending_order.get_pending_order(symbol)
        return True if pending_order["LIMIT"] is not None else False
    
    def check_holding_position(self, symbol:str) -> bool:
        pending_order = self.pending_order.get_pending_order(symbol)
        return pending_order["IS_HOLDING"]
    
    