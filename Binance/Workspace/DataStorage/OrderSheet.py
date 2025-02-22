from dataclasses import dataclass, field
from typing import Optional, List, Dict, Union

@dataclass
class OrderSheet:
    """
    주문과 관련된 정보를 저장한다.

    Raises:
        ValueError: 매개변수 오입력시.
    """
    market:str
    symbol:str
    side:str    # "BUY" or "SELL"
    quantity:Union[float, int]
    order_type:str  #"CLOSE" or "OPEN"
    is_market_order:bool # 시장가 거래, 지정가 거래
    close_position:bool # 매도(매각)일경우 True
    timestamp:int   #ms_timestamp
    strategy_type:str   # 전략 클라스명
    leverage:int = field(default=1)
    
    def __post_init__(self):
        if self.market not in ("FUTURES", "SPOT"):
            raise ValueError(f"market 입력 오류: {self.market}")
        
        if not isinstance(self.is_market_order, bool):
            raise ValueError(f"limit 입력 오류: {self.symbol}")
        
        if not isinstance(self.symbol, str):
            raise ValueError(f"symbol 입력 오류: {self.symbol}")
        
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side 입력 오류: {self.side}")
        
        if not isinstance(self.quantity, (int, float)):
            raise ValueError(f"quantity 입력 오류: {self.quantity}")
        
        if self.order_type not in ("CLOSE", "OPEN"):
            raise ValueError(f"order_type 입력 오류: {self.order_type}")
        
        if not isinstance(self.close_position, bool):
            raise ValueError(f"close position 입력 오류: {self.close_position}")
        
        if not isinstance(self.timestamp, int):
            raise ValueError(f"timesetamp 입력 오류: {self.timestamp}")
        
        if not isinstance(self.strategy_type, str):
            raise ValueError(f"strategy type 입력 오류: {self.strategy_type}")
        
        if self.leverage is not None and (not isinstance(self.leverage, int) or not 1<= self.leverage <= 125):
            raise ValueError(f"leverage 입력 오류: {self.leverage}")