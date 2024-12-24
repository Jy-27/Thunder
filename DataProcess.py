from typing import List, Dict, Optional, Union, Final, Any
from functools import lru_cache
from dataclasses import dataclass, fields, field
import time
import utils
import numpy as np


@dataclass
class TradingLog:
    """
    거래 발생시 거래내역에 대한 자세한 정보를 정리한다. 각종 손익비용에 대한 정보를 기록하여 분석할 수 있는 데이터로 활용한다.
    현재가를 계속 업데이트하여 전체적인 정보를 업데이트하고 stop_price를 분석한다.
    """

    symbol: str  # 심볼
    start_timestamp: int  # 시작 시간
    entry_price: Union[float, int]  # 진입 가격 [Open]
    position: int  # 포지션 (1: Long, 2: Short)
    quantity: Union[float, int]  # 수량
    leverage: int  # 레버리지
    trade_scenario: int  # 적용 시나리오 값.
    test_mode: bool  # 현재 Log가 백테스트중일 경우 (last_timestamp값에 영향을 미친다.)
    stop_rate: float = 0.025  # 손절율
    fee_rate: float = 0.05  # 수수료율
    init_stop_rate: float = 0.015  # 초기(진입시) 손절율
    use_scale_stop: bool = True  # final 손절율 or scale손절율 적용 여부
    adj_rate: Optional[float] = (
        0.0001  # scale_stop_ratio option, 시계흐름에 따른 시작가 변화적용율
    )
    adj_interval: Optional[str] = "3m"  # scale_stop_ratio option, 시계흐름의 범위 기준
    adj_start_price: Optional[float] = None  # 최초 또는 시작가 변화율 적용 금액
    stop_price: Optional[float] = None  # 포지션 종료 가격 지정.
    stop_signal: bool = (
        False  # True시 종료신호로 해석되며, close position 실행 신호로 사용함.
    )
    last_timestamp: Optional[int] = None  # 종료 시간 or 현재시간
    high_price: Optional[Union[float, int]] = (
        None  # 거래 시작 후 종료까지 최고 가격 [High]
    )
    low_price: Optional[Union[float, int]] = (
        None  # 거래 시작 후 종료까지 최저 가격 [Low]
    )
    current_price: Optional[Union[float, int]] = None  # 현재 가격 [Close]
    initial_value: Optional[float] = None  # 초기 가치
    current_value: Optional[float] = None  # 현재 가치
    net_profit_loss: Optional[float] = None  # 수수료 제외한 손익
    gross_profit_loss: Optional[float] = None  # 수수료를 포함한 손익
    break_even_price: Optional[float] = None  # 손익분기점 가격
    entry_fee: Optional[Union[float, int]] = None  # 진입 수수료
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
        # 손절지정을 scale로 미설정시
        if not self.use_scale_stop:
            self.adj_rate = None
            self.adj_interval = None
        # 진입가가 0이하면 오류발생
        if self.entry_price <= 0:
            raise ValueError(
                f"진입가는 최소 0보다 커야 함. 현재 값: {self.entry_price}"
            )
        # 레버리지가 1미만이면 또는 int가 아니면 오류 발생
        if self.leverage <= 0:
            # 오류처리하고 프로그램을 중단한다.
            raise ValueError(
                f"레버리지는 최소 1 이상이어야 함. 현재 값: {self.leverage}"
            )
        # 레버리지의 타입은 int만 인정
        if not isinstance(self.leverage, int):
            # 오류처리하고 프로그램을 중단한다.
            raise ValueError(
                f"레버리지는 정수만 입력가능. 현재 타입: {type(self.leverage)}"
            )

        # 현재 가격과 현재 타임스템프 값을 업데이트한다.
        # 해당 업데이트는 기타 가치평가 연산값에 대입된다.
        self.update_trade_data(
            current_price=self.entry_price, current_timestamp=self.start_timestamp
        )  # , current_timestamp=self.last_timestamp)

    # 수수료를 계산한다.
    # 시장가와 지정가는 다른 수수료율이 적용되지만 시장가 기준으로 계산한다.
    def __calculate_fees(self):
        # 수수료율을 단위 변환한다.
        adjusted_fee_rate = self.fee_rate / 100
        # 진입 수수료를 계산 및 속성에 저장한다
        self.entry_fee = (
            self.entry_price * adjusted_fee_rate * self.quantity  # * self.leverage
        )
        # 종료 수수료를 계산 및 속성에 저장한다.
        self.exit_fee = (
            self.current_price * adjusted_fee_rate * self.quantity  # * self.leverage
        )

    # Log데이터의 각종 값을 계산한다.
    def __calculate_trade_values(self):
        # self.initial_value = (self.entry_price * self.quantity) / self.leverage
        # 최고가를 계산한다.
        self.high_price = max(self.high_price, self.current_price)
        # 최저가를 계산한다.
        self.low_price = min(self.low_price, self.current_price)

        # 거래 시작시 발생 비용을 계산한다. 수수료 제외
        self.initial_value = (self.quantity / self.leverage) * self.entry_price
        # 현재 가격 반영하여 가치 계산한다. 수수료 제외
        self.current_value = (self.current_price * self.quantity) / self.leverage

        # 총 수수료를 계산한다.
        total_fees = self.entry_fee + self.exit_fee
        # 수수료를 제외한 손익금
        self.net_profit_loss = self.current_value - self.initial_value
        # 수수료를 포함한 손익금(총 수수료 반영)
        self.gross_profit_loss = self.net_profit_loss - total_fees
        # 손익분기 가격
        self.break_even_price = self.entry_price + (total_fees / self.quantity)

        # 포지션이 Long일때
        if self.position == 1:
            # 손익 계산 및 속성 반영
            self.profit_loss = (
                self.quantity * (self.current_price - self.entry_price) - total_fees
            )
        # 포지션이 Short일때
        elif self.position == 2:
            # 손익 계산 및 속성 반영
            self.profit_loss = (
                self.quantity * (self.entry_price - self.current_price) - total_fees
            )

    # Stoploss가격을 계산한다. 포지션 종료의 기준이 가격이 된다.
    def __calculate_stop_price(self):
        # scale stop 미사용시 손절율을 최종가에 반영한다.
        if not self.use_scale_stop:
            # 시작 손절율을 0로 만든다. 시작 손절율은 self.stop_rate로 대체한다.
            self.init_stop_rate = 0
            # 시작 가격은 진입가로 대처한다.
            self.adj_start_price = self.entry_price
            # 포지션이 롱이면,
            if self.position == 1:
                #
                self.stop_price = self.high_price * (1 - self.stop_rate)
            elif self.position == 2:
                self.stop_price = self.low_price * (1 + self.stop_rate)
            # 발생할 수 없으나, 만일을 위해
            else:
                raise ValueError(f"position입력 오류: {self.position}")

        INTERVAL_MS_SECONDS: Final[dict] = {
            "1m": 60_000,
            "3m": 180_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "2h": 7_200_000,
            "4h": 14_400_000,
            "6h": 21_600_000,
            "8h": 28_800_000,
            "12h": 43_200_000,
            "1d": 86_400_000,
            "3d": 259_200_000,
            "1w": 604_800_000,
            "1M": 2_592_000_000,
        }

        time_diff = self.last_timestamp - self.start_timestamp

        target_ms_seconds = INTERVAL_MS_SECONDS.get(self.adj_interval)
        # adj_interval을 잘못입력시 오류발생시킨다.
        if target_ms_seconds is None:
            # 이미 검증을 했지만, 혹시 모를 재검증.
            raise ValueError(f"interval값이 유효하지 않음: {self.adj_interval}")

        dynamic_rate = int(time_diff / target_ms_seconds) * self.adj_rate
        print(dynamic_rate)
        print(target_ms_seconds)
        print(self.adj_rate)
        print(self.init_stop_rate)

        start_rate = self.init_stop_rate - dynamic_rate

        if self.position == 1:
            self.adj_start_price = self.current_price * (1 - start_rate)
            self.stop_price = self.adj_start_price + (
                (self.high_price - self.adj_start_price) * (1 - self.stop_rate)
            )
        elif self.position == 2:
            self.adj_start_price = self.current_price * (1 + start_rate)
            self.stop_price = self.adj_start_price - (
                (self.adj_start_price - self.low_price) * (1 + self.stop_rate)
            )
        else:
            raise ValueError(f"position입력 오류: {self.position}")

    def __calculate_stop_signal(self):
        """
        1. 기능 : 현재 가격과 StopLoss가격을 비교하여 position종료 여부를 결정한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        3. Memo
            self.__calculate_stop_price를 계산해야 사용 가능하다.
        """
        # trading_log데이터에 symbol값이 존재하는지 확인한다.

        # 포지션이 Long이면
        if self.position == 1:
            # stoploss 가격이 마지막 가격보다 클 경우
            self.stop_signal = self.stop_price >= self.current_price
        elif self.position == 2:
            # stoploss 가격이 마지막 가격보다 작을 경우
            self.stop_signal: bool = self.stop_price <= self.current_price
        # 포지션 정보 오입력시 에러 발생.
        else:
            raise ValueError(
                f"position은 1:long/buy, 2:short/sell만 입력가능: {self.position}"
            )

    def update_trade_data(
        self,
        current_price: Union[float, int],
        # stop_price: Union[float, int],
        current_timestamp: Optional[int] = None,
    ):
        # self.stoploss = stop_price
        if self.test_mode:
            if current_timestamp is None:
                raise ValueError(
                    f"백테트시 current_timestamp값 입력해야함: {current_timestamp}"
                )
        elif not self.test_mode:
            current_timestamp = int(time.time() * 1_000)

        self.last_timestamp = current_timestamp
        self.current_price = current_price
        self.__calculate_fees()
        self.__calculate_trade_values()
        self.__calculate_stop_price()
        self.__calculate_stop_signal()

    def to_list(self):
        return list(self.__dict__.values())


class TradeAnaylsis:
    def __init__(self, initial_balance: float = 1_000):
        self.data_container = utils.DataContainer()
        self.trade_history: List[TradingLog] = []
        self.closed_positions: Dict[str, List[List[Any]]] = {}
        self.open_positions: Dict[str, List[List[Any]]] = {}
        self.number_of_stocks: int = 0
        self.initial_balance: float = initial_balance  # 초기 자산
        self.total_balance: float = initial_balance  # 총 평가 자산
        self.active_value: float = 0  # 거래 중 자산 가치
        self.cash_balance: float = initial_balance  # 사용 가능한 예수금
        self.profit_loss: float = 0  # 손익 금액
        self.profit_loss_ratio: float = 0  # 손익률

    # TradingLog 클라스를 컨테이너 데이터에 저장한다.
    def add_log_data(self, log_data: TradingLog):
        # symbol정보를 조회한다.
        symbol = log_data.symbol
        # container name은 symbol로 정하고 데이터는 TradingLog를 넣는다.
        self.data_container.set_data(data_name=symbol, data=log_data)
        trade_data = self.__extract_valid_data(data=log_data)

        if self.open_positions.get(symbol):
            self.open_positions[symbol].append(trade_data)
        else:
            self.open_positions[symbol] = trade_data
        self.update_data()

    # 데이터를 업데이트하는 동시에 stop 신호를 반환받는다.
    def update_log_data(self, symbol: str, price: float, timestamp: int) -> bool:
        # container 데이터에 해당 symbol값이 없으면
        if not symbol in self.data_container.get_all_data_names():
            # stop 거절 신호를 반환한다. (아무일도 발생하지 않음.)
            return False
        # 데이터를 업데이트 한다.
        self.data_container.get_data(data_name=symbol).update_trade_data(
            current_price=price, current_timestamp=timestamp
        )
        # 종료 신호를 반환한다.
        self.update_data()
        return self.data_container.get_data(data_name=symbol).stop_signal

    # 필요한 값만 추출하여 리스트 형태로 반환한다.
    def __extract_valid_data(self, data: TradingLog):
        return [
            data.initial_value,
            data.current_value,
            data.gross_profit_loss,
        ]

    def remove_order_data(self, symbol: str):
        if not self.open_positions.get(symbol):
            raise ValueError(f"진행중인 거래 없음: {symbol}")

        open_position_data = self.open_positions[symbol].pop()

        if symbol in self.closed_positions.keys():
            self.closed_positions[symbol].append(open_position_data)
        elif not symbol in self.closed_positions.keys():
            self.closed_positions[symbol] = [open_position_data]

        self.trade_history.append(self.data_container.get_data(data_name=symbol))
        self.data_container.remove_data(data_name=symbol)
        self.update_data()

    def update_data(self):
        cloed_trade_data = []
        open_trade_data = []
        for _, closed_data in self.closed_positions.items():
            cloed_trade_data.append(closed_data)
        for _, open_data in self.open_positions.items():
            open_trade_data.append(open_data)

        closed_data_array = np.array(object=cloed_trade_data, dtype=float)
        if closed_data_array.ndim == 1:
            closed_data_array = closed_data_array.reshape(1, -1)

        open_data_array = np.array(object=open_trade_data, dtype=float)
        if open_data_array.ndim == 1:
            open_data_array = open_data_array.reshape(1, -1) 


        print(open_data_array)
        if open_data_array.size == 0:
            open_pnl = 0
        else:
            open_pnl = np.sum(closed_data_array[:, 2])
            
        if closed_data_array.size == 0:
            closed_pnl = 0
        else:
            closed_pnl = np.sum(closed_data_array[:, 2])


        print(open_pnl)
        print(closed_pnl)

        open_pnl = np.sum(open_data_array[:, 2])

        self.number_of_stocks = len(open_data_array)
        self.active_value = np.sum(open_data_array[:, 0])
        self.cash_balance = self.initial_balance - closed_pnl - self.active_value
        self.profit_loss = closed_pnl + open_pnl
        self.total_balance = self.profit_loss + self.active_value + self.cash_balance
        self.profit_loss_ratio = self.profit_loss / self.initial_balance
