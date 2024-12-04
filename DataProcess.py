from typing import List, Dict, Optional, Union
from functools import lru_cache


class InvalidPositionError(ValueError):
    """Position 값 오류 예외"""
    pass


class InvalidDataError(ValueError):
    """기초 데이터 오류 예외"""
    pass

class InvalidParameterError(ValueError):
    """파라미터 변수값 입력 오류 예외"""
    pass
    
class TradeStopper:
    """
    Spot 마켓 또는 Futures 마켓에서 주문에 의한 매입(포지션 open) 시
    매각(포지션 off)가격을 현재 가격을 반영하여 실시간으로 지정해준다.
    """
    def __init__(self, profit_ratio: float=0.015, risk_ratio: float=0.85):
        self.profit_ratio = profit_ratio
        self.risk_ratio = risk_ratio
        self.trading_data: Dict[str, Dict[str, Union[str, float]]] = {}

    def __validate_data_existence(self, symbol: str) -> bool:
        symbol = symbol.upper()
        return isinstance(self.trading_data.get(symbol), dict) and bool(
            self.trading_data[symbol]
        )

    def __validate_and_get_data(self, symbol: str) -> Dict[str, Union[str, float]]:
        symbol = symbol.upper()
        if not self.__validate_data_existence(symbol):
            raise InvalidDataError(f"Symbol {symbol}에 대한 유효한 데이터가 없습니다.")
        return self.trading_data[symbol]

    def __validate_key_existence(self, symbol: str, key: str) -> bool:
        symbol = symbol.upper()
        return self.__validate_data_existence(symbol) and key in self.trading_data[symbol]

    def __calculate_target_price(
        self, entry_price: float, reference_price: float, position: str
    ) -> float:
        position = position.upper()
        if position not in ["LONG", "BUY", "SELL", "SHORT"]:
            raise InvalidPositionError(f"유효하지 않은 포지션: {position}")
        if position in ["LONG", "BUY"]:
            dead_line_price = entry_price + (
                (reference_price - entry_price) * self.risk_ratio
            )
            return dead_line_price * (1 - self.profit_ratio)
        elif position in ["SHORT", "SELL"]:
            dead_line_price = entry_price - (
                (entry_price - reference_price) * self.risk_ratio
            )
            return dead_line_price * (1 + self.profit_ratio)
        else:
            raise InvalidParameterError(f'position입력오류 : {position}')

    def remove_trading_data(self, symbol: str) -> None:
        symbol = symbol.upper()
        if self.__validate_data_existence(symbol):
            del self.trading_data[symbol]

    def initialize_trading_data(
        self, symbol: str, position: str, entry_price: float
    ) -> Dict[str, Union[str, float]]:
        valid_positions = ["LONG", "BUY", "SELL", "SHORT"]
        position = position.upper()
        symbol = symbol.upper()
        if position not in valid_positions:
            raise InvalidPositionError(f"유효하지 않은 포지션 값: {position}")
        self.trading_data[symbol] = {
            "position": position,
            "entryPrice": entry_price,
            "referencePrice": entry_price,
        }
        return self.trading_data[symbol]

    @lru_cache(maxsize=30)
    def get_trading_stop_signal(self, symbol: str, current_price: float) -> bool:
        symbol = symbol.upper()
        data = self.__validate_and_get_data(symbol)
        position = data["position"]
        reference_price = data["referencePrice"]
        entry_price = data["entryPrice"]

        # Reference price 업데이트
        if position in ["LONG", "BUY"]:
            reference_price = max(reference_price, current_price)
        elif position in ["SHORT", "SELL"]:
            reference_price = min(reference_price, current_price)

        self.trading_data[symbol]["referencePrice"] = reference_price

        # Target price 계산
        target_price:float = self.__calculate_target_price(
            entry_price=entry_price, reference_price=reference_price, position=position
        )
        self.trading_data[symbol]["targetPrice"] = target_price

        # 종료 조건
        if position in ["LONG", "BUY"] and current_price <= target_price:
            # self.remove_trading_data(symbol)
            self.get_trading_stop_signal.cache_clear()
            return True
        elif position in ["SHORT", "SELL"] and current_price >= target_price:
            # self.remove_trading_data(symbol)
            self.get_trading_stop_signal.cache_clear()
            return True

        return False

    def clear_all_trading_data(self) -> None:
        """모든 트레이딩 데이터를 삭제"""
        self.trading_data.clear()

class IntervalManager:
    def __init__(self):
        # 속성을 초기화하지 않아도 동적 관리 가능
        self.interval_1m = None
        self.interval_3m = None
        self.interval_5m = None
        self.interval_15m = None
        self.interval_30m = None
        self.interval_1h = None
        self.interval_2h = None
        self.interval_4h = None
        self.interval_6h = None
        self.interval_8h = None
        self.interval_12h = None
        self.interval_1d = None
        self.interval_3d = None
        self.interval_1w = None
        self.interval_1M = None

    def add_interval(self, interval_name, data):
        """동적으로 속성을 생성하고 데이터를 추가"""
        setattr(self, interval_name, data)

    def get_interval(self, interval_name):
        """입력받은 이름과 매칭되는 속성 반환"""
        if hasattr(self, interval_name):
            return getattr(self, interval_name)
        else:
            raise AttributeError(f"No attribute named '{interval_name}'")

class OrderConstraint:
    """ 주문시 제약사항을 생성한다. """
    
    # def __init__ (self):
    #     self.target_count_min = 1
    #     self.target_count_max = 10
        
    #     self.account_amp_min = 10
    #     self.account_step = 5
        
    #     self.safety_account_ratio = 0.32
    
    
    # 보유가능한 항목과, 안전금액, 거래가능금액을 계산한다.
    def calc_fund(self, funds: float, rate: float = 0.35) -> dict:
        """
        총 자금과 안전 비율을 기반으로 보유 가능량과 다음 기준 금액 계산.

        Args:
            funds (float): 사용 가능한 총 자금.
            ratio (float): 안전 비율. 기본값은 0.35.

        Returns:
            dict: 계산 결과를 담은 딕셔너리.
        """
        # 자금이 10 미만일 경우 초기값 반환
        
        init_safety_value = round(10 * rate, 3)
        init_usable_value = 10 - init_safety_value
        init_trade_value = min(6, init_usable_value)
        
        if funds < 10:
            return {
                "count": 1,            # 보유 가능량
                "targetValue": 10,     # 다음 기준 금액
                "safetyValue": init_safety_value,     # 안전 금액
                "usableValue": init_usable_value,     # 유효 금액
                "tradeValue": init_trade_value       # 회당 거래대금
            }

        steps = [2, 3]  # 증가 단계
        target = 5      # 초기 목표 금액
        count = 0       # 보유 가능량
        last_valid_target = 0  # 초과 이전의 유효한 목표 금액

        # 증가율 순환
        for step in steps:
            while target <= funds:
                last_valid_target = target  # 초과 전 단계 값 저장
                target *= step
                count += 1
                if target > funds:
                    break

        # 안전 금액 및 유효 금액 계산
        safety_value = last_valid_target * rate
        usable_value = last_valid_target - safety_value
        trade_value = usable_value / count if count > 0 else 0

        # 결과 반환
        return {
            "count": count,                  # 보유 가능량
            "targetValue": last_valid_target,  # 다음 기준 금액
            "safetyValue": safety_value,    # 안전 금액
            "usableValue": usable_value,    # 유효 금액
            "tradeValue": trade_value       # 회당 거래대금
        }
    
    
    
    
    
    # # 거래가능횟수를 제한한다. 필요한가?
    # def get_transaction_capacity(self)
    
    
    # # 현재 보유금액에 다른 계산식을 만든다.
    # def calc_holding_limit(self)
    
    
    # # 회당 주문금액 계산
    # def calc_max_trade_amount(self)
    
    
    # total_balance_ =
    # available_balance_ = 
    
    
    
    
    
    
    
    
    
    
    
    
    


if __name__ == "__main__":
    obj = TradeStopper(profit_ratio=0.015, risk_ratio=0.75)

    symbol = "XRPUSDT"
    position = "long"
    entry_price = 90.32

    obj.initialize_trading_data(symbol=symbol, position=position, entry_price=entry_price)

    print(obj.get_trading_stop_signal(symbol=symbol, current_price=90.0))
    print(obj.get_trading_stop_signal(symbol=symbol, current_price=92.0))
