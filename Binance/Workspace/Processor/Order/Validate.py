import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Processor.Order.PendingOrder import PendingOrder
from Workspace.Processor.Wallet.Wallet import Wallet

class OrderValaidate:
    """
    Create Order 진행 전 주문가능여부를 검토한다.
    """
    def __init__(self, pending_order:PendingOrder, wallet:Wallet):
        self.pending_order = pending_order
        self.wallet = wallet
        
    def check_limit_order(self, symbol:str) -> bool:
        """
        미체결 주문 확인

        Args:
            symbol (str): 심볼

        Returns:
            bool: 미체결 주문 있으면 True, 아니면 False
        """
        pending_order = self.pending_order.get_pending_order(symbol)
        return True if pending_order["LIMIT"] is not None else False
    
    def check_holding_position(self, symbol:str) -> bool:
        """
        포지션 보유여부 확인

        Args:
            symbol (str): 심볼

        Returns:
            bool: 보유중이면 True, 미보유중이면 False
        """
        pending_order = self.pending_order.get_pending_order(symbol)
        return pending_order["IS_HOLDING"]
    
    def check_available(self, balance:float) -> bool:
        """
        예수금 주문가능여부 확인

        Args:
            balace (float): 주문 금액

        Returns:
            bool: 주문 가능시 True, 불가시 False
        """
        return self.wallet.get_balance("free") > balance