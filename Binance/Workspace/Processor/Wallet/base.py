from dataclasses import dataclass, field

@dataclass
class TradeOrder:
    """주문 실행시 발생하는 메시지"""
    orderId:int
    symbol:str
    status:str
    clientOrderId:str
    price:float
    avgPrice:float
    origQty:float
    executedQty:float
    cumQuote:float
    timeInForce:str
    type:str
    reduceOnly:bool
    closePosition:bool
    side:str
    positionSide:str
    stopPrice:float
    workingType:str
    priceProtect:bool
    origType:str
    priceMatch:Optional[Any]
    selfTradePreventionMode:str
    goodTillDate:float
    time:int
    updateTime:int

@dataclass
class TradingPosition:
    symbol:str
    initialMargin:float
    maintMargin:float
    unrealizedProfit:float
    positionInitialMargin:float
    openOrderInitialMargin:float
    leverage:int
    isolated:bool
    entryPrice:float
    breakEvenPrice:float
    maxNotional:Union[float, int]
    positionSide:str
    positionAmt:float
    notional:float
    isolatedWallet:float
    updateTime:int
    bidNotional:int
    askNotional:int
    

class OrderLog:
    def __init__(self, *symbols:tuple):
        self.__slots__ = symbols

        
    

class Wallet:
    def __init__(self):
        self.total_balance:float = 0
        self.margin_balance:float = 0
        self.available_balance:float = 0

from typing import Optional
from SystemConfig import Path
from asyncio import Queue
import Workspace.Utils.BaseUtils as base_utils
from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import FuturesTradingClient as futures_tr_client
from Workspace.DataStorage.NodeStorage
from SystemConfig import Path


class Wallet:
    def __init__(self, init_balance: float, queue: Queue, futures_trading_client: futures_tr_client, ):
        self.init_balance: float = init_balance
        self.total_balance: float = self.init_balance
        self.free_balance: float = self.init_balance
        self.lock_balance: float = 0
        self.margin_balance: float = 0
        self.pnl_balance: float = 0
        self.unrealized_pnl_balance: float = 0
        self.pnl_ratio: float = 0
        self.queue = queue
        self.futures_tr_client = futures_trading_client

    async def update_balance(self):
        """
        🐣 API에서 계좌 잔고를 가져와 Wallet 정보를 업데이트하는 함수
        """
        data = await asyncio.to_thread(self.futures_tr_client.fetch_account_balance)

        self.total_balance = float(data["totalMarginBalance"])
        self.margin_balance = float(data["totalInitialMargin"])
        self.free_balance = float(data["availableBalance"])
        self.lock_balance = float(data["totalOpenOrderInitialMargin"])
        self.unrealized_pnl_balance = float(data["totalUnrealizedProfit"])
        self.pnl_balance = float(data["totalCrossUnPnl"])

        # ZeroDivisionError 방지
        self.pnl_ratio = (self.pnl_balance / self.init_balance) if self.init_balance != 0 else 0
    
    
    def get_balance(self, key: str) -> float:
        """
        🔎 잔고 관련 특정 값을 조회하는 함수
        """
        balance_dict = {
            "total": self.total_balance,
            "free": self.free_balance,
            "lock": self.lock_balance,
            "margin": self.margin_balance,
            "pnl": self.pnl_balance,
            "unrealized_pnl": self.unrealized_pnl_balance,
            "pnl_ratio": self.pnl_ratio * 100,
        }
        return balance_dict.get(key, None)  # 없는 키 입력 시 None 반환

    def reset_balance(self):
        """
        🧹 잔고를 초기 상태로 리셋하는 함수
        """
        self.total_balance = self.init_balance
        self.free_balance = self.init_balance
        self.lock_balance = 0
        self.margin_balance = 0
        self.pnl_balance = 0
        self.unrealized_pnl_balance = 0
        self.pnl_ratio = 0

    def __repr__(self):
        """
        🖨️ print함수 적용시 출력 내용
        """
        return (
            f"1. seed money: {self.init_balance:,.2f} usdt\n"
            f"2. total balance: {self.total_balance:,.2f} usdt\n"
            f"3. margin: {self.margin_balance:,.2f} usdt\n"
            f"4. free: {self.free_balance:,.2f} usdt\n"
            f"5. lock: {self.lock_balance:,.2f} usdt\n"
            f"6. un_pnl: {self.unrealized_pnl_balance:,.2f}\n"
            f"7. pnl: {self.pnl_balance:,.2f}\n"
            f"8. pnl ratio: {self.pnl_ratio * 100:,.2f} %\n"
        )