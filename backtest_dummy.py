from dataclasses import dataclass, fields
from typing import List, Optional, Union, Any, Dict
import numpy as np

@dataclass
class TradeOrder:
    symbol: str
    start_timestamp: int  # 시작 시간
    entry_price: Union[float, int]  # 진입 가격
    position: int  # 포지션 (1: Long, -1: Short)
    quantity: Union[float, int]  # 수량
    leverage: int  # 레버리지
    fee_rate: float = 0.05  # 수수료율
    end_time: Optional[int] = None  # 종료 시간
    initial_value: Optional[float] = None  # 초기 가치
    current_value: Optional[float] = None  # 현재 가치
    profit_loss: Optional[float] = None  # 손익 금액
    current_price: Optional[Union[float, int]] = None  # 현재 가격
    break_even_price: Optional[float] = None  # 손익분기점 가격
    entry_fee: Optional[Union[float, int]] = None  # 진입 수수료
    exit_fee: Optional[Union[float, int]] = None  # 종료 수수료

    def __post_init__(self):
        if self.current_price is None:
            self.current_price = self.entry_price
        if self.leverage <= 0:
            raise ValueError(f"레버리지는 최소 1 이상이어야 합니다. 현재 값: {self.leverage}")
        if self.end_time is None:
            self.end_time = self.start_timestamp
        self.__update_fees()
        self.__update_values()

    def __update_fees(self):
        adjusted_fee_rate = self.fee_rate / 100
        self.entry_fee = self.entry_price * adjusted_fee_rate * self.quantity * self.leverage
        self.exit_fee = self.current_price * adjusted_fee_rate * self.quantity * self.leverage
        total_fees = self.entry_fee + self.exit_fee
        self.break_even_price = self.entry_price + (total_fees / self.quantity)

    def __update_values(self):
        self.initial_value = (self.entry_price * self.quantity) / self.leverage
        self.current_value = (self.current_price * self.quantity) / self.leverage
        total_fees = self.entry_fee + self.exit_fee
        self.profit_loss = self.current_value - self.initial_value - total_fees

    def update_trade_data(self, current_price: Union[float, int], current_time: int):
        self.current_price = current_price
        self.end_time = current_time
        self.__update_fees()
        self.__update_values()

    def to_list(self):
        return list(self.__dict__.values())


class TradeAnalysis:
    def __init__(self, initial_balance: float = 1_000):
        self.closed_positions: Dict[str, List[List[Any]]] = {}
        self.open_positions: Dict[str, List[List[Any]]] = {}

        self.number_of_stocks: int = 0

        self.initial_balance: float = initial_balance  # 초기 자산
        self.total_balance: float = initial_balance  # 총 평가 자산
        self.active_value: float = 0  # 거래 중 자산 가치
        self.cash_balance: float = initial_balance  # 사용 가능한 예수금
        self.profit_loss: float = 0  # 손익 금액
        self.profit_loss_ratio: float = 0  # 손익률

    def add_closed_position(self, trade_order_data: list):
        symbol = trade_order_data[0]
        if symbol not in self.closed_positions:
            self.closed_positions[symbol] = [trade_order_data[1:]]
        else:
            self.closed_positions[symbol].append(trade_order_data[1:])
        del self.open_positions[symbol]
        self.update_wallet()
        return self.closed_positions

    def update_open_position(self, trade_order_data: list):
        symbol = trade_order_data[0]
        self.open_positions[symbol] = trade_order_data[1:]
        self.update_wallet()
        return self.open_positions

    def update_wallet(self):
        all_trades_data = []
        open_trades_data = []

        if self.closed_positions:
            for _, trades_close in self.closed_positions.items():
                all_trades_data.extend(trades_close)

        if self.open_positions:
            for idx, (_, trades_open) in enumerate(self.open_positions.items()):
                all_trades_data.append(trades_open)
                open_trades_data.append(trades_open)
                self.number_of_stocks = idx +1

        if not self.closed_positions and not self.open_positions:
            self.active_value = 0
            self.cash_balance = self.total_balance
            return

        all_trades_data_array = np.array(all_trades_data)
        open_trades_data_array = np.array(open_trades_data)

        if all_trades_data_array.ndim == 1:
            # 2차원 배열로 변환 (행 기준)
            all_trades_data_array = all_trades_data_array.reshape(1, -1)
            
        if open_trades_data_array.ndim == 1:
            # 2차원 배열로 변환 (행 기준)
            open_trades_data_array = open_trades_data_array.reshape(1, -1)


        sunk_cost = np.sum(all_trades_data_array[:, [12, 13]])
        entry_cost = np.sum(all_trades_data_array[:, 7])
        total_cost = sunk_cost + entry_cost
        recovered_value = np.sum(all_trades_data_array[:, 8])

        # 현재 거래중인 자산 초기화
        if open_trades_data_array.size > 0:
            self.active_value = np.sum(open_trades_data_array[:,8])
        else:
            self.active_value = 0

        self.cash_balance = self.initial_balance - self.active_value
        self.profit_loss = np.sum(all_trades_data_array[:, 9])
        self.profit_loss_ratio = round((self.profit_loss / self.initial_balance) * 100, 3)
        self.total_balance = self.cash_balance + self.active_value + self.profit_loss
        
        
        if self.cash_balance < 0:
            raise ValueError(f'주문 오류 : 진입금액이 예수금을 초과함.')
        
        # 계좌 가치가 0 미만이면 청산신호 발생 및 프로그램 중단.
        if self.total_balance < 0:
            raise ValueError(f'청산발생 : 계좌잔액 없음.')


class TradeOrderManager:
    def __init__(self, initial_balance: float = 1_000):
        self.active_orders: List[TradeOrder] = []
        self.order_index_map = {}
        self.active_symbols: List[str] = []
        self.trade_analysis = TradeAnalysis(initial_balance=initial_balance)

    def __refresh_order_map(self):
        self.order_index_map = {order.symbol: idx for idx, order in enumerate(self.active_orders)}
        self.active_symbols = list(self.order_index_map.keys())

    def add_order(self, **kwargs):
        if kwargs.get('symbol') in self.order_index_map:
            return

        valid_keys = {field.name for field in fields(TradeOrder)}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        order = TradeOrder(**filtered_kwargs)

        self.active_orders.append(order)
        self.__refresh_order_map()

        order_signal = order.to_list()
        self.trade_analysis.update_open_position(order_signal)
        return order

    def remove_order(self, symbol: str):
        idx = self.order_index_map.get(symbol)
        order_signal = self.active_orders[idx].to_list()
        self.trade_analysis.add_closed_position(order_signal)
        del self.active_orders[idx]
        self.__refresh_order_map()

    def update_order_data(self, symbol: str, current_price: Union[float, int], current_time: int):
        idx = self.order_index_map.get(symbol)
        if idx is None:
            return
        self.active_orders[idx].update_trade_data(current_price=current_price, current_time=current_time)
        trade_order_data = self.active_orders[idx].to_list()
        self.trade_analysis.update_open_position(trade_order_data)

    def get_order(self, symbol: str):
        idx = self.order_index_map.get(symbol)
        return self.active_orders[idx]
    
if __name__ == "__main__":
    from pprint import pprint
    
    obj = TradeOrderManager()
    obj.add_order(symbol='ADAUSDT', start_timestamp=123, entry_price=0.5, position=1, quantity=1000, leverage=5)
    # obj.update_data(symbol='ADAUSDT', current_price=2, current_timestamp=123)
    obj.add_order(symbol='SOLUSDT', start_timestamp=123, entry_price=0.5102, position=1, quantity=1000, leverage=5)
    # obj.update_data(symbol='SOLUSDT', current_price=2, current_timestamp=123)
    obj.add_order(symbol='XRPUSDT', start_timestamp=123, entry_price=0.1052, position=1, quantity=1000, leverage=5)
    # obj.update_data(symbol='XRPUSDT', current_price=2, current_timestamp=123)
    obj.add_order(symbol='BTCUSDT', start_timestamp=123, entry_price=0.235, position=1, quantity=1000, leverage=5)
    # obj.update_data(symbol='BTCUSDT', current_price=2, current_timestamp=123)
    obj.remove_order(symbol='ADAUSDT')
    obj.remove_order(symbol='SOLUSDT')
    obj.remove_order(symbol='XRPUSDT')
    # obj.remove_order(symbol='BTCUSDT')
    
    pprint(obj.trade_analysis.__dict__)