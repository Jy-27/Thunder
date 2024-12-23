from typing import List, Dict, Optional, Union, Final
from functools import lru_cache
from dataclasses import dataclass, fields
import time


@dataclass
class TradingLog:
    """
    거래 발생시 거래내역에 대한 자세한 정보를 정리한다. 각종 손익비용에 대한 정보를 기록하여 분석할 수 있는 데이터로 활용한다.
    """

    symbol: str
    start_timestamp: int  # 시작 시간
    entry_price: Union[float, int]  # 진입 가격 [Open]
    position: int  # 포지션 (1: Long, 2: Short)
    quantity: Union[float, int]  # 수량
    leverage: int  # 레버리지
    trade_scenario: Optional[str]  # 적용 시나리오 값.
    adj_start_price: Optional[float] = None
    fee_rate: float = 0.05  # 수수료율
    stop_price: Optional[float] = None# 포지션 종료 가격 지정.
    exit_signal: bool = False
    last_timestamp: Optional[int] = None  # 종료 시간 or 현재시간
    high_price: Optional[Union[float, int]] = None  # 거래 시작 후 종료까지 최고 가격 [High]
    low_price: Optional[Union[float, int]] = None  # 거래 시작 후 종료까지 최저 가격 [Low]
    current_price: Optional[Union[float, int]] = None  # 현재 가격 [Close]
    initial_value: Optional[float] = None  # 초기 가치
    current_value: Optional[float] = None  # 현재 가치
    profit_loss: [float] = None  # 손익 금액
    break_even_price: Optional[float] = None  # 손익분기점 가격
    entry_fee: Union[float, int] = None  # 진입 수수료
    exit_fee: Optional[Union[float, int]] = None  # 종료 수수료

    def __post_init__(self):
        # 현재가를 진입가에 맞춘다. (close)
        if self.current_price is None:
            self.current_price = self.entry_price
        # 최고가를 진입가에 맞춘다. (high)
        if self.high_price is None:
            self.high_price = self.entry_price
        # 최저가를 진입가에 맞춘다. (high)
        if self.low_price is None:
            self.low_price = self.entry_price
        # 마지막 시간을 시작시간을 현재시간에 맞춘다.
        if self.last_timestamp is None:
            self.last_timestamp = self.start_timestamp
        # 진입가가 0이하면 오류발생
        if self.entry_price <= 0:
            raise ValueError(
                f'진입가는 최소 0보다 커야 함. 현재 값: {self.entry_price}'
            )
        # 레버리지가 1미만이면 또는 int가 아니면 오류 발생
        if self.leverage <= 0:
            raise ValueError(
                f"레버리지는 최소 1 이상이어야 함. 현재 값: {self.leverage}"
            )
        if not isinstance(self.leverage, int):
            raise ValueError(
                f'레버리지는 정수만 입력가능. 현재 타입: {type(self.leverage)}'
            )
        
        self.__calculate_fees()
        self.__calculate_trade_values()

    def __calculate_fees(self):
        adjusted_fee_rate = self.fee_rate / 100
        self.entry_fee = (
            self.entry_price * adjusted_fee_rate * self.quantity  # * self.leverage
        )
        self.exit_fee = (
            self.current_price * adjusted_fee_rate * self.quantity  # * self.leverage
        )
        total_fees = self.entry_fee + self.exit_fee
        self.break_even_price = self.entry_price + (total_fees / self.quantity)

    def __calculate_trade_values(self):
        # self.initial_value = (self.entry_price * self.quantity) / self.leverage
        self.high_price = max(self.high_price, self.current_price)
        self.low_price = min(self.low_price, self.current_price)
        
        self.initial_value = (self.quantity / self.leverage) * self.entry_price
        self.current_value = (self.current_price * self.quantity) / self.leverage
        
        self.profit_loss = self.current_value - self.initial_value
        
        total_fees = self.entry_fee + self.exit_fee
        # self.profit_loss = self.current_value - self.initial_value - total_fees
        if self.position == 1:
            self.profit_loss = (
                self.quantity * (self.current_price - self.entry_price) - total_fees
            )
        elif self.position == 2:
            self.profit_loss = (
                self.quantity * (self.entry_price - self.current_price) - total_fees
            )

    def update_trade_data(
        self,
        current_price: Union[float, int],
        # stop_price: Union[float, int],
        current_timestamp: Optional[int]=None,
    ):
        # self.stoploss = stop_price
        self.last_timestamp = current_timestamp
        self.current_price = current_price
        self.__calculate_fees()
        self.__calculate_trade_values()

    def to_list(self):
        return list(self.__dict__.values())


class StopLoss:
    """
    
    
    """
    def __init__(
        self,
        initial_stop_rate: float = 0.015,
        final_stop_rate: Optional[float] = None,
        scale_stop_ratio: Optional[float] = 0.75,
        adjust_rate: Optional[float] = 0.0001,
        adjust_interval: str = "3m",
    ):
        # 초기 포지션 종료 비율
        self.initial_stop_rate = initial_stop_rate
        # 마지막 포지션 종료 비율(지정형)
        self.final_stop_rate = final_stop_rate
        # 마지막 포지션 종료 비율(능동형)
        self.scale_stop_ratio = scale_stop_ratio
        # 시간 흐름에 따른 변경 비율
        self.adjust_rate = adjust_rate
        # 변경비율 타임 간격
        self.adjust_interval = adjust_interval
        # 거래중인 항목을 저장
        self.trading_log: Dict[str, TradingLog] = {}

        # 각 interval별로 밀리언초 값을 래핑한다.
        self.INTERVAL_MS_SECONDS: Final[dict] ={
            '1m': 60_000,
            '3m': 180_000,
            '5m': 300_000,
            '15m': 900_000,
            '30m': 1_800_000,
            '1h': 3_600_000,
            '2h': 7_200_000,
            '4h': 14_400_000,
            '6h': 21_600_000,
            '8h': 28_800_000,
            '12h': 43_200_000,
            '1d': 86_400_000,
            '3d': 259_200_000,
            '1w': 604_800_000,
            '1M': 2_592_000_000
            }

        if self.adjust_interval not in self.INTERVAL_MS_SECONDS:
            raise ValueError(f"adjust_interval 값이 유효하지 않음 : {self.adjust_interval}")
        # final_stop_rate 설정 시 조건 검증
        if self.final_stop_rate is not None and (
            self.scale_stop_ratio is not None or self.adjust_rate is not None
        ):
            raise ValueError(
                "final_stop_rate를 설정할 경우 scale_stop_ratio와 adjust_rate 값을 지정할 수 없음."
            )

    # 현재가격과 종료 가격을 비교하여 포지션 종료 여부를 결정한다.
    def __create_exit_signal(self, symbol:str):
        """
        1. 기능 : 현재 가격과 StopLoss가격을 비교하여 position종료 여부를 결정한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        3. Memo
            self.__calculate_stop_price를 계산해야 사용 가능하다.
        """
        # trading_log데이터에 symbol값이 존재하는지 확인한다.
        if symbol not in self.trading_log:
            # 없으면 아무것도 하지 않는다.
            return

        # 포지션 정보를 확인한다.
        position = self.trading_log[symbol].position
        # 마지막 가격을 확인한다.
        close_price = self.trading_log[symbol].current_price
        # stoploss 가격을 확인한다.
        stop_price = self.trading_log[symbol].stop_price

        # 포지션이 Long이면
        if position == 1:
            # stoploss 가격이 마지막 가격보다 클 경우
            if stop_price >= close_price:
                return True
            else:
                return False
        elif position == 2:
            # stoploss 가격이 마지막 가격보다 작을 경우
            if stop_price <= close_price:
                return True
            else:
                return False
        # 포지션 정보 오입력시 에러 발생.
        else:
            raise ValueError(f'position은 1:long/buy, 2:short/sell만 입력가능: {position}')


    # StopLoss가격을 계산한다.
    def __calculate_stop_price(self, symbol:str):
        """
        1. 가격 : 수집된 가격정보를 연산하여 StopLoss가격을 계산한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        3. Memo
            지속 업데이트 필요함.
        """
        # trading_log데이터에 symbol값이 존재하는지 확인한다.
        if symbol not in self.trading_log:
            # 없으면 아무것도 하지 않는다.
            return
        
        # 포지션 정보를 확인한다.
        position = self.trading_log[symbol].position
        # 마지막 가격을 확인한다.
        close_price = self.trading_log[symbol].current_price
        # 최고가를 확인한다.
        high_price = self.trading_log[symbol].high_price
        # 최저가를 확인한다.
        low_price = self.trading_log[symbol].low_price
        
        # 거래 시작 타임스템프를 확인한다.
        start_timestamp = self.trading_log[symbol].start_timestamp
        # 현재 시간 타임슽메프를 확인한다.
        last_timestamp = self.trading_log[symbol].last_timestamp
        
        # 현재시간과 시작시간의 차이를 구한다.
        time_diff = last_timestamp - start_timestamp
        
        # 손절율 지정시.
        if not self.final_stop_rate is None:
            if position == 1: #long 포지션
                # 지정 손절율을 최고가에 반영한다.
                return high_price * (1 - self.final_stop_rate)
            elif position == 2:
                # 지정 손절율을 최저가에 반영한다.
                return low_price * (1 + self.final_stop_rate)

        # 스케일 손절율 지정시.
        if not self.scale_stop_ratio is None and time_diff >= 0:
            # interval에 해당하는 ms초를 조회한다.
            target_ms_seconds = self.INTERVAL_MS_SECONDS.get(self.adjust_interval)
            # adjust_interval을 잘못입력시 오류발생시킨다.
            if target_ms_seconds is None:
                # 이미 검증을 했지만, 혹시 모를 재검증.
                raise ValueError(f'interval값이 유효하지 않음: {self.adjust_interval}')
            
            # 소수점 버림처리
            # 
            dynamic_rate = int(time_diff / target_ms_seconds) * self.adjust_rate
            # 초기 손절율을 반영한다. 시간의 흐름에 따라 초기 손절율을 증가한다.
            # 증가된 손절율을 scale_stop_ratio에 영향을 미친다.abs
            # 횡보발생에 대한 대책이다.
            start_rate = self.initial_stop_rate - dynamic_rate
            
            # 롱 포지션시
            if position == 1:
                # 보정 시작가를 계산한다.
                adj_start_price = close_price * (1 - start_rate)
                print(adj_start_price)
                # 보정 시작가에 scale_stop_ratio를 반영한다.
                return adj_start_price + ((high_price-adj_start_price) * self.scale_stop_ratio)
            elif position == 2:
                # 보정 시작가를 계산한다.
                adj_start_price = close_price * (1 + start_rate)
                # 보정 시작가에 scale_stop_ratio를 반영한다.
                return adj_start_price - ((adj_start_price - low_price) * self.__calculate_close_price)
            # 포지션 정보 오입력시 오류를 발생시킨다.
            else:
                raise ValueError(f'position은 1:long/buy, 2:short/sell만 입력가능: {position}')


    # 초기 데이터를 추가한다.
    def initialize_data(self, trading_log: TradingLog):
        """
        1. 기능 : 초기 데이터 등록하는 함수
        2. 매개변수
            1) trading_log : class TradingLog 데이터
        3. Memo        
        """
        symbol = trading_log.symbol
        self.trading_log[symbol] = trading_log

    # 데이터를 삭제한다.
    def remove_data(self, symbol: str):
        """
        1. 기능 : 거래가 종료된 항목의 데이터를 반환 및 삭제한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        3. Memo
            self.get_close_signal 함수에 본 함수를 추가할까 고민중...
        """
        # trading_log데이터에 symbol값이 존재하는지 확인한다.
        if symbol in self.trading_log:
            # 데이터를 반환하고 삭제를 동시에 실행한다.
            return self.trading_log.pop(symbol)
        # symbol값이 없을경우 아무것도 하지 않는다.
        return

    # trading log data를 업데이트한다.
    def update_trading_log(self, symbol: str, current_price: float, current_timestamp:int):
        """
        1. 기능 : websocket으로 수신된 실시간 데이터를 반영하여 거래중인 데이터를 업데이트한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) current_price : 현재 가격
        3. Memo
        """
        # 밀리세컨드 값을 지정한다.
        MILLISECONDS_PER_SECOND = 1000
        # 현재 타임스템프 값을 확보한다.
        # current_timestamp = int(time.time() * MILLISECONDS_PER_SECOND)
        # trading_log정보를 업데이트 한다.
        self.trading_log[symbol].update_trade_data(
            current_price=current_price, current_timestamp=current_timestamp
        )
        # 종료 가격을 계산한다.
        self.trading_log[symbol].stop_price = self.__calculate_stop_price(symbol)
        # 현재가격과 종료 가격을 비교하여 포지션 종료 여부를 결정한다.
        self.trading_log[symbol].exit_signal = self.__create_exit_signal(symbol)

    # StopLoss가격을 확인하여 현재 포지션을 종료결정 여부 데이터를 반환한다.
    def get_close_signal(self, symbol):
        """
        1. 기능 : 현재 포지션의 종료 결정 여부를 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        3. Memo
        """
        if symbol in self.trading_log:
            return self.trading_log[symbol].exit_signal

# class TradeHistory:
    

# class TradeStopper:
#     """
#     Spot 마켓 또는 Futures 마켓에서 주문에 의한 매입(포지션 open) 시
#     매각(포지션 off)가격을 현재 가격을 반영하여 실시간으로 지정해준다.
#     """

#     def __init__(self, profit_ratio: float = 0.015, risk_ratio: float = 0.85):
#         self.profit_ratio = profit_ratio
#         self.risk_ratio = risk_ratio
#         self.trading_data: Dict[str, Dict[str, Union[str, float]]] = {}

#     def __validate_data_existence(self, symbol: str) -> bool:
#         symbol = symbol.upper()
#         return isinstance(self.trading_data.get(symbol), dict) and bool(
#             self.trading_data[symbol]
#         )

#     def __validate_and_get_data(self, symbol: str) -> Dict[str, Union[str, float]]:
#         symbol = symbol.upper()
#         if not self.__validate_data_existence(symbol):
#             raise ValueError(f"Symbol {symbol}에 대한 유효한 데이터가 없습니다.")
#         return self.trading_data[symbol]

#     def __validate_key_existence(self, symbol: str, key: str) -> bool:
#         symbol = symbol.upper()
#         return (
#             self.__validate_data_existence(symbol) and key in self.trading_data[symbol]
#         )

#     def __calculate_target_price(
#         self, entry_price: float, reference_price: float, position: str
#     ) -> float:
#         position = position.upper()
#         if position not in ["LONG", "BUY", "SELL", "SHORT"]:
#             raise ValueError(f"유효하지 않은 포지션: {position}")
#         if position in ["LONG", "BUY"]:
#             dead_line_price = entry_price + (
#                 (reference_price - entry_price) * self.risk_ratio
#             )
#             return dead_line_price
#         elif position in ["SHORT", "SELL"]:
#             dead_line_price = entry_price - (
#                 (entry_price - reference_price) * self.risk_ratio
#             )
#             return dead_line_price
#         else:
#             raise ValueError(f"position입력오류 : {position}")

#     def remove_trading_data(self, symbol: str) -> None:
#         symbol = symbol.upper()
#         if self.__validate_data_existence(symbol):
#             del self.trading_data[symbol]

#     def initialize_trading_data(
#         self, symbol: str, position: str, entry_price: float
#     ) -> Dict[str, Union[str, float]]:
#         valid_positions = ["LONG", "BUY", "SELL", "SHORT"]
#         position = position.upper()
#         symbol = symbol.upper()
#         if position not in valid_positions:
#             raise ValueError(f"유효하지 않은 포지션 값: {position}")
#         self.trading_data[symbol] = {
#             "position": position,
#             "entryPrice": entry_price,
#             "referencePrice": entry_price,
#         }
#         return self.trading_data[symbol]

#     # @lru_cache(maxsize=30)
#     def get_trading_stop_signal(self, symbol: str, current_price: float) -> bool:
#         symbol = symbol.upper()
#         data = self.__validate_and_get_data(symbol)
#         position = data["position"]
#         reference_price = data["referencePrice"]
#         entry_price = data["entryPrice"]

#         # Reference price 업데이트
#         if position in ["LONG", "BUY"]:
#             reference_price = max(reference_price, current_price)
#         elif position in ["SHORT", "SELL"]:
#             reference_price = min(reference_price, current_price)

#         self.trading_data[symbol]["referencePrice"] = reference_price

#         # Target price 계산
#         target_price: float = self.__calculate_target_price(
#             entry_price=entry_price, reference_price=reference_price, position=position
#         )
#         self.trading_data[symbol]["targetPrice"] = target_price

#         # 종료 조건
#         if position in ["LONG", "BUY"] and current_price <= target_price:
#             self.remove_trading_data(symbol)
#             # self.get_trading_stop_signal.cache_clear()
#             return True
#         elif position in ["SHORT", "SELL"] and current_price >= target_price:
#             self.remove_trading_data(symbol)
#             # self.get_trading_stop_signal.cache_clear()
#             return True

#         return False

#     def clear_all_trading_data(self) -> None:
#         """모든 트레이딩 데이터를 삭제"""
#         self.trading_data.clear()


# class IntervalManager:
#     def __init__(self):
#         # 속성을 초기화하지 않아도 동적 관리 가능
#         self.interval_1m = None
#         self.interval_3m = None
#         self.interval_5m = None
#         self.interval_15m = None
#         self.interval_30m = None
#         self.interval_1h = None
#         self.interval_2h = None
#         self.interval_4h = None
#         self.interval_6h = None
#         self.interval_8h = None
#         self.interval_12h = None
#         self.interval_1d = None
#         self.interval_3d = None
#         self.interval_1w = None
#         self.interval_1M = None

#     def add_interval(self, interval_name, data):
#         """동적으로 속성을 생성하고 데이터를 추가"""
#         setattr(self, interval_name, data)

#     def get_interval(self, interval_name):
#         """입력받은 이름과 매칭되는 속성 반환"""
#         if hasattr(self, interval_name):
#             return getattr(self, interval_name)
#         else:
#             raise AttributeError(f"No attribute named '{interval_name}'")


# class OrderConstraint:
#     """주문시 제약사항을 생성한다."""

#     # def __init__ (self):
#     #     self.target_count_min = 1
#     #     self.target_count_max = 10

#     #     self.account_amp_min = 10
#     #     self.account_step = 5

#     #     self.safety_account_ratio = 0.32

#     # 보유가능한 항목과, 안전금액, 거래가능금액을 계산한다.
#     def calc_fund(self, funds: float, rate: float = 0.35, count_max: int = 6) -> dict:
#         """
#         총 자금과 안전 비율을 기반으로 보유 가능량과 다음 기준 금액 계산.

#         Args:
#             funds (float): 사용 가능한 총 자금.
#             ratio (float): 안전 비율. 기본값은 0.35.

#         Returns:
#             dict: 계산 결과를 담은 딕셔너리.
#         """
#         # 자금이 10 미만일 경우 초기값 반환

#         init_safety_value = round(10 * rate, 3)
#         init_usable_value = 10 - init_safety_value
#         init_trade_value = min(6, init_usable_value)

#         if funds < 10:
#             return {
#                 "count": 1,  # 보유 가능량
#                 "targetValue": 10,  # 다음 기준 금액
#                 "safetyValue": init_safety_value,  # 안전 금액
#                 "usableValue": init_usable_value,  # 유효 금액
#                 "tradeValue": init_trade_value,  # 회당 거래대금
#             }

#         steps = [2, 3]  # 증가 단계
#         target = 5  # 초기 목표 금액
#         count = 0  # 보유 가능량
#         last_valid_target = 0  # 초과 이전의 유효한 목표 금액

#         # 증가율 순환
#         for step in steps:
#             while target <= funds:
#                 last_valid_target = target  # 초과 전 단계 값 저장
#                 target *= step
#                 count += 1
#                 if target > funds:
#                     break

#         # count최대값을 지정한다. 너무 높면 회당 주문금액이 낮아진다.
#         count = min(count, count_max)

#         # 안전 금액 및 유효 금액 계산
#         safety_value = last_valid_target * rate
#         usable_value = last_valid_target - safety_value
#         trade_value = usable_value / count if count > 0 else 0

#         # 결과 반환
#         return {
#             "count": count,  # 보유 가능량
#             "targetValue": last_valid_target,  # 다음 기준 금액
#             "safetyValue": safety_value,  # 안전 금액
#             "usableValue": usable_value,  # 유효 금액
#             "tradeValue": trade_value,  # 회당 거래대금
#         }

#     # # 거래가능횟수를 제한한다. 필요한가?
#     # def get_transaction_capacity(self)

#     # # 현재 보유금액에 다른 계산식을 만든다.
#     # def calc_holding_limit(self)

#     # # 회당 주문금액 계산
#     # def calc_max_trade_amount(self)

#     # total_balance_ =
#     # available_balance_ =


# if __name__ == "__main__":
#     obj = TradeStopper(profit_ratio=0.015, risk_ratio=0.75)

#     symbol = "XRPUSDT"
#     position = "long"
#     entry_price = 90.32

#     obj.initialize_trading_data(
#         symbol=symbol, position=position, entry_price=entry_price
#     )

#     print(obj.get_trading_stop_signal(symbol=symbol, current_price=90.0))
#     print(obj.get_trading_stop_signal(symbol=symbol, current_price=92.0))
