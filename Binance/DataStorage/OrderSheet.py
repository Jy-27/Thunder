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
    timestamp:int   #ms_timestamp
    strategy_type:str   # 전략 클라스명
    leverage:Optional[int] = field(default=None)
    
    def __post_init__(self):
        if self.market not in ("FUTURES", "SPOT"):
            raise ValueError(f"market 입력 오류: {self.market}")
        
        if not isinstance(self.symbol, str):
            raise ValueError(f"symbol 입력 오류: {self.symbol}")
        
        if self.side not in ("BUY", "SELL"):
            raise ValueError(f"side 입력 오류: {self.side}")
        
        if not isinstance(self.quantity, (int, float)):
            raise ValueError(f"quantity 입력 오류: {self.quantity}")
        
        if self.order_type not in ("CLOSE", "OPEN"):
            raise ValueError(f"order_type 입력 오류: {self.order_type}")
        
        if not isinstance(self.timestamp, int):
            raise ValueError(f"timesetamp 입력 오류: {self.timestamp}")
        
        if not isinstance(self.strategy_type, str):
            raise ValueError(f"strategy type 입력 오류: {self.strategy_type}")
        
        if self.leverage is not None and (not isinstance(self.leverage, int) or not 2<= self.leverage <= 125):
            raise ValueError(f"leverage 입력 오류: {self.leverage}")