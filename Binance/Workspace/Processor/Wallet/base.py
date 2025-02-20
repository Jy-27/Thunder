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
        