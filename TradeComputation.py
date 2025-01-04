from typing import List, Dict, Optional, Union, Final, Any
from functools import lru_cache
from dataclasses import dataclass, fields, field, asdict

# from BinanceTradeClient import SpotTrade, FuturesTrade
from MarketDataFetcher import FuturesMarket, SpotMarket
from TradeClient import FuturesOrder, SpotOrder
import time
import utils
import numpy as np
import os
import asyncio
import pickle
from copy import copy
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import style, ticker

import plotly.graph_objects as go
from plotly.subplots import make_subplots


##=--=####=---=###=--=####=---=###=--=##
# -=##=---==-*   M E  M O  *-==---=##=-#
##=--=####=---=###=--=####=---=###=--=##

# TickerDataManager.get_ticker_above_price에 적용될 dummy data 생성 함수 만들기
# fetch_ticker_price 대용
# TickerDataManager.get_tickers_above_value 적용될 dummy data 생성 함수 만들기
# fetch_24hr_ticker 대용
# TickerDataManager.get_tickers_above_change 적용될 dummy data 생성 함수 만들기
# fetch_24hr_ticker 대용

# 목표 // 백테스티 더미에티어를 반영하여 target_ticker가 적용되는지 여부를 확인한다.abs
# 타겟 티켓도 아닌데 발주 진행건으로 분류되는 것은 결과 데이터에 영향을 미친다.


def trade_log_attr_maps():
    # DataProcess.TradingLog의 속성 가져오기
    trading_log_vars = vars(TradingLog)

    # __match_args__가 존재하는지 확인
    if "__match_args__" not in trading_log_vars:
        return {}  # 존재하지 않으면 빈 딕셔너리 반환

    attr_ = trading_log_vars["__match_args__"]

    # 속성 이름과 인덱스 매핑
    return {attr: idx for idx, attr in enumerate(attr_)}


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
    adj_timer: bool = False  # interval 시간 간격마다 adj_start_price 변동 적용여부
    adj_rate: Optional[float] = (
        0.0007  # scale_stop_ratio option, 시계흐름에 따른 시작가 변화적용율
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
    net_profit_loss_rate: Optional[float] = None  # 수수료 제외 손익률
    gross_profit_loss: Optional[float] = None  # 수수료를 포함한 손익
    gross_profit_loss_rate: Optional[float] = None  # 수수료 포함 손익률
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
        if not self.adj_timer:
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

        if self.position == 1:
            # 수수료를 제외한 손익금
            self.net_profit_loss = (
                self.current_price - self.entry_price
            ) * self.quantity

        elif self.position == 2:
            # 수수료를 제외한 손익금
            self.net_profit_loss = (
                self.entry_price - self.current_price
            ) * self.quantity

        # 수수료 제외 손익률
        self.net_profit_loss_rate = self.net_profit_loss / self.initial_value
        # 수수료를 포함한 손익금(총 수수료 반영)
        self.gross_profit_loss = self.net_profit_loss - total_fees
        # 수수료 포함 손익률
        self.gross_profit_loss_rate = self.gross_profit_loss / self.initial_value
        # 손익분기 가격
        self.break_even_price = self.entry_price + (total_fees / self.quantity)

        # # 포지션이 Long일때
        # if self.position == 1:
        #     # 손익 계산 및 속성 반영
        #     self.profit_loss = (
        #         self.quantity * (self.current_price - self.entry_price) - total_fees
        #     )
        # # 포지션이 Short일때
        # elif self.position == 2:
        #     # 손익 계산 및 속성 반영
        #     self.profit_loss = (
        #         self.quantity * (self.entry_price - self.current_price) - total_fees
        #     )

    # Stoploss가격을 계산한다. 포지션 종료의 기준이 가격이 된다.
    def __calculate_stop_price(self):
        # scale stop 미사용시 손절율을 최종가에 반영한다.
        if not self.adj_timer:
            # 시작 손절율을 0로 만든다. 시작 손절율은 self.stop_rate로 대체한다.
            self.init_stop_rate = 0
            # 시작 가격은 진입가로 대처한다.
            self.adj_start_price = self.entry_price
            # 포지션이 롱이면,
            dynamic_rate = 0
            if self.position == 1:
                # high price를 반영하여 stop_price를 계산한다.
                self.stop_price = self.high_price * (1 - self.stop_rate)
            # 포지션이 숏이면,
            elif self.position == 2:
                # low price를 반영하여 stop_price를 계산한다.
                self.stop_price = self.low_price * (1 + self.stop_rate)
            # 발생할 수 없으나, 만일을 위해
            else:
                raise ValueError(f"position입력 오류: {self.position}")
            return
        # adj_timer가 적용된다면,
        elif self.adj_timer:
            # 종료시간과 시작시간의 차이를 구하고
            time_diff = self.last_timestamp - self.start_timestamp
            # 현재 설정된(self.adj_interval)값을 조회한다.
            target_ms_seconds = utils._get_interval_ms_seconds(self.adj_interval)
            # 만일 adj_interval을 잘못입력시 오류발생시킨다.
            if target_ms_seconds is None:
                # 이미 검증을 했지만, 혹시 모를 재검증.
                raise ValueError(f"interval값이 유효하지 않음: {self.adj_interval}")
            # 시간차와 래핑값을 나누어 step값을 구하고 비율을 곱하여 반영할 비율을 계산한다.
            dynamic_rate = int(time_diff / target_ms_seconds) * self.adj_rate


        # 시작 손절 비율을 계산한다. adj_timer 설정에 따라 start_rate가 달라진다.
        # dynamic_rate값이 음수로 바뀔경우 start_rate는 증가된다. 맞나??
        start_rate = self.init_stop_rate - dynamic_rate

        # 포지션이 롱이면,
        if self.position == 1:
            # 손절 반영 시작값은 시작가 기준
            self.adj_start_price = self.entry_price * (1 - start_rate)
            self.stop_price = self.adj_start_price + (
                (self.high_price - self.adj_start_price) * (1 - self.stop_rate)
            )
        elif self.position == 2:
            self.adj_start_price = self.entry_price * (1 + start_rate)
            self.stop_price = self.adj_start_price + (
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
        if self.test_mode and current_timestamp is None:
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


# 전체 자산 관리와 거래 기록 관리
class PortfolioManager:
    """
    전체 자산 관리와 거래기록을 관리한다.
    """

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
        self.trade_count: int = 0  # 총 체결 횟수
        # self.trading_log_attr_maps:Dict[str, int] = utils._info_trade_log_attr_maps()

    def validate_open_position(self, symbol: str):
        if symbol in self.open_positions:
            return True
        else:
            return False

    # TradingLog 클라스를 컨테이너 데이터에 저장한다.
    def add_log_data(self, log_data: TradingLog):
        # symbol정보를 조회한다.
        symbol = log_data.symbol
        # container name은 symbol로 정하고 데이터는 TradingLog를 넣는다.
        self.data_container.set_data(data_name=symbol, data=log_data)
        trade_data = self.__extract_valid_data(data=log_data)
        self.trade_count += 1
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
        # 컨테이너에서 데이터를 불러온다.
        log_data = self.data_container.get_data(data_name=symbol)
        trade_data = self.__extract_valid_data(data=log_data)
        # print(trade_data)
        self.open_positions[symbol] = trade_data
        # print(self.open_positions[symbol])
        # 종료 신호를 반환한다.
        self.update_data()
        return self.data_container.get_data(data_name=symbol).stop_signal

    # 필요한 값만 추출하여 리스트 형태로 반환한다.
    def __extract_valid_data(self, data: TradingLog):
        return [
            data.start_timestamp,  # 0 시작 타임스템프
            data.last_timestamp,  # 1  종료 타임스템프
            data.position,  # 2    포지션 (1:long, 2:short)
            data.leverage,  # 3    레버리지
            data.quantity,  # 4    수량
            data.entry_price,  # 5 진입가격
            data.high_price,  # 6  최고가격
            data.low_price,  # 7   최저가격
            data.current_price,  # 8   현재가격 또는 마지막 가격
            data.stop_price,  # 9  stoploss 가격
            data.initial_value,  # 10  초기 진입 평가 금액
            data.current_value,  # 11  현재 평가 금액
            data.net_profit_loss,  # 12    수수료 제외 PnL
            data.gross_profit_loss,  # 13  수수료 포함 PnL
            data.entry_fee,  # 14  진입 수수료
            data.exit_fee,  # 15   종료 수수료
            data.trade_scenario,  # 16  시나리오 종류
        ]

    def remove_order_data(self, symbol: str):
        if not self.open_positions.get(symbol):
            raise ValueError(f"진행중인 거래 없음: {symbol}")

        open_position_data = self.open_positions[symbol].copy()
        del self.open_positions[symbol]

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
            for nest_closed_data in closed_data:
                cloed_trade_data.append(nest_closed_data)
        for _, open_data in self.open_positions.items():
            open_trade_data.append(open_data)

        closed_data_array = np.array(object=cloed_trade_data, dtype=float)
        if closed_data_array.ndim == 1:
            closed_data_array = closed_data_array.reshape(1, -1)

        open_data_array = np.array(object=open_trade_data, dtype=float)
        if open_data_array.ndim == 1:
            open_data_array = open_data_array.reshape(1, -1)

        if open_data_array.size == 0:
            open_pnl = 0
            active_value = 0
        else:
            open_pnl = np.sum(open_data_array[:, 13])
            active_value = np.sum(open_data_array[:, 10])

        if closed_data_array.size == 0:
            closed_pnl = 0
        else:
            # print(closed_data_array)
            closed_pnl = np.sum(closed_data_array[:, 13])

        # open_pnl = np.sum(open_data_array[:, 2])

        self.number_of_stocks = len(self.open_positions.keys())
        self.active_value = active_value
        self.cash_balance = self.initial_balance + closed_pnl - self.active_value
        self.profit_loss = closed_pnl + open_pnl
        self.total_balance = self.profit_loss + self.initial_balance
        # self.profit_loss_ratio = self.profit_loss / self.initial_balance
        self.profit_loss_ratio = (
            self.total_balance - self.initial_balance
        ) / self.initial_balance


##=---=####=---=####=---=####=---=####=---=####=---=##
# =-=##=---=###=----=###=----=###=----=###=----=###=-=#
##=---=####=---=####=---=####=---=####=---=####=---=##
# -=###=----=#=- BACK TEST METHOD ZONE -=##=----=###=-#
##=---=####=---=####=---=####=---=####=---=####=---=##
# =-=##=---=###=----=###=----=###=----=###=----=###=-=#
##=---=####=---=####=---=####=---=####=---=####=---=##


class BacktestDataFactory:
    """
    백테스트에 사용될 데이터를 수집 및 가공 편집한다. kline_data를 수집 후 np.array처리하며, index를 위한 데이터도 생성한다.
    """

    FUTURES = "FUTURES"
    SPOT = "SPOT"

    def __init__(
        self,
        symbols: Union[str, List],
        intervals: Union[list[str], str],
        start_date: str,
        end_date: str,
    ):
        # str타입을 list타입으로 변형한다.
        self.symbols = [symbols] if isinstance(symbols, str) else symbols
        self.intervals = [intervals] if isinstance(intervals, str) else intervals

        # KlineData 다운로드할 기간. str(YY-MM-DD HH:mm:dd)
        self.start_date: str = start_date
        self.end_date: str = end_date

        # 가상 신호발생시 quantity 계산을 위한 호출
        # self.ins_trade_spot = SpotTrade()
        # self.ins_trade_futures = FuturesTrade()

        # kline 데이터 수신을 위한 호출
        self.ins_market_spot = SpotMarket()
        self.ins_market_futures = FuturesMarket()

        self.storeage = "DataStore"
        self.kline_closing_sync_data = "closing_sync_data.pkl"
        self.indices_file = "indices_data.json"
        self.kline_data_file = "kline_data.json"
        self.parent_directory = os.path.dirname(os.getcwd())

    # def create_dummy_signal(self, signal_type:str):

    # 장기간 kline data수집을 위한 date간격을 생성하여 timestamp형태로 반환한다.
    def __generate_timestamp_ranges(
        self, interval: str, start_date: str, end_date: str
    ) -> List[List[int]]:
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date

        # 시작 및 종료 날짜 문자열 처리
        # 시간 정보는 반드시 00:00:00 > 23:59:59로 세팅해야 한다. 그렇지 않을경우 수신에 문제 발생.
        start_date = start_date  # + " 00:00:00"
        end_date = end_date  # + " 23:59:59"

        # interval에 따른 밀리초 단위 스텝 가져오기
        interval_step = utils._get_interval_ms_seconds(interval)

        # Limit 값은 1,000이나 유연한 대처를 위해 999 적용
        MAX_LIMIT = 1_000

        # 시작 타임스탬프
        start_timestamp = utils._convert_to_timestamp_ms(date=start_date)
        # interval 및 MAX_LIMIT 적용으로 계산된 최대 종료 타임스탬프

        if interval_step is not None:
            max_possible_end_timestamp = (
                start_timestamp + (interval_step * MAX_LIMIT) - 1
            )
        else:
            raise ValueError(f"interval step값 없음 - {interval_step}")
        # 지정된 종료 타임스탬프
        end_timestamp = utils._convert_to_timestamp_ms(date=end_date)

        # 최대 종료 타임스탬프가 지정된 종료 타임스탬프를 초과하지 않을 경우
        if max_possible_end_timestamp >= end_timestamp:
            return [[start_timestamp, end_timestamp]]
        else:
            # 초기 데이터 설정
            initial_range = [start_timestamp, max_possible_end_timestamp]
            timestamp_ranges = [initial_range]

            # 반복문으로 추가 데이터 생성
            while True:
                # 다음 시작 및 종료 타임스탬프 계산
                next_start_timestamp = timestamp_ranges[-1][1] + 1
                next_end_timestamp = (
                    next_start_timestamp + (interval_step * MAX_LIMIT) - 1
                )

                # 다음 종료 타임스탬프가 지정된 종료 타임스탬프를 초과할 경우
                if next_end_timestamp >= end_timestamp:
                    final_range = [next_start_timestamp, end_timestamp]
                    timestamp_ranges.append(final_range)
                    return timestamp_ranges

                # 그렇지 않을 경우 범위 추가 후 반복
                else:
                    new_range = [next_start_timestamp, next_end_timestamp]
                    timestamp_ranges.append(new_range)
                    continue

    # 각 symbol별 interval별 지정된 기간동안의 kline_data를 수신 후 dict타입으로 묶어 반환한다.
    async def generate_kline_interval_data(
        self,
        symbols: Union[str, list, None] = None,
        intervals: Union[str, list, None] = None,
        start_date: Union[str, None] = None,
        end_date: Union[str, None] = None,
        save: bool = False,
    ):
        """
        1. 기능 : 장기간 kline data를 수집한다.
        2. 매개변수
            1) symbols : 쌍거래 심볼 리스트
            2) intervals : interval 리스트
            3) start_date : 시작 날짜 (년-월-일 만 넣을것.)
            4) end_date : 종료 날짜 (년-월-일 만 넣을것.)
            5) save : 저장여부
        3. 추가설명
            self.__generate_timestamp_ranges가 함수내에 호출됨.
        """

        # 기본값 설정
        if symbols is None:
            symbols = self.symbols
        if intervals is None:
            intervals = self.intervals
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date

        # API 호출 제한 설정
        MAX_API_CALLS_PER_MINUTE = 1150
        API_LIMIT_RESET_TIME = 60  # 초 단위

        api_call_count = 0
        # start_time = datetime.datetime.now()
        aggregated_results: Dict[str, Dict[str, List[int]]] = {}

        for symbol in symbols:
            aggregated_results[symbol] = {}

            for interval in intervals:
                aggregated_results[symbol][interval] = {}
                timestamp_ranges = self.__generate_timestamp_ranges(
                    interval=interval, start_date=start_date, end_date=end_date
                )

                collected_data = []
                for timestamps in timestamp_ranges:
                    # 타임스탬프를 문자열로 변환
                    start_timestamp_str = utils._convert_to_datetime(timestamps[0])
                    end_timestamp_str = utils._convert_to_datetime(timestamps[1])

                    # Kline 데이터 수집
                    kline_data = await self.ins_market_futures.fetch_klines_date(
                        symbol=symbol,
                        interval=interval,
                        start_date=start_timestamp_str,
                        end_date=end_timestamp_str,
                    )                   
                    collected_data.extend(kline_data)

                # API 호출 간 간격 조정
                await asyncio.sleep(0.2)
                aggregated_results[symbol][interval] = collected_data

        if save:
            path = os.path.join(
                self.parent_directory, self.storeage, self.kline_data_file
            )
            utils._save_to_json(
                file_path=path, new_data=aggregated_results, overwrite=True
            )
        return aggregated_results

    # 생성한 closing_sync_data를 interval index데이터를 구성한다.(전체)
    def __generate_full_indices(self, closing_sync_data):
        # symbols를 획득
        symbols = list(closing_sync_data.keys())
        # Intervals를 획득
        intervals = list(closing_sync_data[symbols[0]])
        # 기본 데이터를 지정
        base_data = closing_sync_data[symbols[0]]
        # 마지막 index값 조회
        max_index = len(base_data[intervals[0]])
        
        # 인덱스 데이터를 저장할 자료를 초기화
        indices_data = {}
        # interval 루프
        for interval in intervals:
            # interval별 miute를 활용하여 step으로 지정
            interval_step = utils._get_interval_minutes(interval)
            # arange를 통해서 interval의 기준 index 지정.
            indices_data[interval] = np.arange(start=0, stop=max_index, step=interval_step)
        # 결과 반환.
        return indices_data

    # 1분봉 종가 가격을 각 interval에 반영한 테스트용 더미 데이터를 생성한다.
    def generate_kline_closing_sync(self, kline_data: Dict, save: bool = False) -> Dict[str, Dict[str, np.ndarray]]:
        """
        1. 기능 : 백테스트시 데이터의 흐름을 구현하기 위하여 1분봉의 누적데이터를 반영 및 1분봉의 길이와 맞춘다.
        2. 매개변수
            1) kline_data : kline_data 를 numpy.array화 하여 적용
            2) save : 생성된 데이터 저장여부.

        3. 처음부터 인터별간 데이터의 길이는 다르지만, open_timestamp와 end_timestamp가 일치한다. kline_data수신기에는 이상이 없다.
            dummy_data가 불필요하다는 소리....해당 함수를 완전 재구성해야한다. 그동안 잘못된 데이터로 백테스를 수행하였다. 데이터의 신뢰성을
            먼저 확보해야만 한다.
        """

        # 심볼 및 interval 값을 리스트로 변환
        symbols_list = list(kline_data.keys())
        intervals_list = list(kline_data[symbols_list[0]].keys())
        closing_sync_data = {}

        kline_array = utils._convert_to_array(kline_data)

        ### np.ndarray로 구성된 dict자료형태를 Loop 순환 ###
        for symbol, symbol_data in kline_array.items():
            closing_sync_data[symbol] = {}

            ### base data 생성(각 symbol별 첫번째 interval값 기준 ###
            base_data = symbol_data[
                self.intervals[0]
            ]  # 첫번재 index데이터값 기준으로 생성함.

            ### interval Loop 대입 ###
            for interval in self.intervals:
                ### interval 첫번재 index값은 continue처리한다.(base_data값은 위에 선언 했으므로)
                if interval == self.intervals[0]:
                    closing_sync_data[symbol][interval] = base_data
                    continue

                timestamp_range = utils._get_interval_ms_seconds(interval) - 1
                ### 목표 interval 데이터값을 조회한다.###
                interval_data = kline_array[symbol][interval]

                ### 데이터를 저장할 임시 변수를 초기화 한다. ###
                temp_data = []

                ### base data를 활용하여 index를 구현하고, index별 데이터를 순환한다.###
                for index, data in enumerate(base_data):
                    open_timestamp = data[0]  # 시작 타임스템프
                    open_price = data[1]  # 시작 가격
                    high_price = data[2]  # 최고 가격
                    low_price = data[3]  # 최저 가격
                    close_price = data[4]  # 마지막 가격
                    volume = data[5]  # 거래량(단위 : coin)
                    close_timestamp = data[6]  # 종료 타임스템프
                    volume_total_usdt = data[7]  # 거래량(단위 : usdt)
                    trades_count = data[8]  # 총 거래횟수
                    taker_asset_volume = data[9]  # 시장가 주문 거래량(단위 : coin)
                    taker_quote_volume = data[10]  # 시장가 주문 거래량(단위 : usdt)

                    ### base_data가 적용되는 interval_data의 index값을 확보한다.
                    condition = np.where(
                        (interval_data[:, 0] <= open_timestamp)
                        & (interval_data[:, 6] >= close_timestamp)
                    )

                    ### interval 전체 데이터에서 해당 interval 데이터만 추출한다. ###
                    ### 용도는 start_timestap / end_timestamp추출 및 new_data에 적용을 위함. ###
                    target_data = interval_data[condition]

                    target_open_timestamp = target_data[0, 0]  # 단일값이 확실할 경우
                    target_close_timestamp = target_data[0, 6]  # 단일값이 확실할 경우

                    new_data_condition = np.where(
                        (base_data[:, 0] >= target_open_timestamp)
                        & (base_data[:, 6] <= close_timestamp)
                    )  # close_timestamp는 현재 data종료 시간 기준으로 해야한다.

                    new_base_data = base_data[new_data_condition]

                    timestamp_diff = new_base_data[-1, 6] - new_base_data[0, 0]
                    if timestamp_range == timestamp_diff:
                        new_data = target_data[0]
                    else:
                        new_data = [
                            target_open_timestamp,
                            new_base_data[0, 1],
                            np.max(new_base_data[:, 2]),
                            np.min(new_base_data[:, 3]),
                            new_base_data[-1, 4],
                            np.sum(new_base_data[:, 5]),
                            target_close_timestamp,
                            np.sum(new_base_data[:, 7]),
                            np.sum(new_base_data[:, 8]),
                            np.sum(new_base_data[:, 9]),
                            np.sum(new_base_data[:, 10]),
                            0,
                        ]
                    temp_data.append(new_data)
                closing_sync_data[symbol][interval] = np.array(temp_data, float)
        if save:
            path = os.path.join(
                self.parent_directory, self.storeage, self.kline_closing_sync_data
            )
            with open(file=path, mode="wb") as file:
                pickle.dump(closing_sync_data, file)
        return closing_sync_data

    # generate_kline_closing_sync index 자료를 생성한다.
    def get_indices_data(
        self, closing_sync_data:Dict[str, Dict[str, np.ndarray]] , lookback_days: int = 2) -> utils.DataContainer:
        """
        1. 기능 : generate_kline_clsing_sync 데이터의 index를 생성한다.
        2. 매개변수
            1) data_container : utils모듈에서 사용중인 container data
            2) lookback_days : index 데이터를 생성한 기간을 정한다.
        3. 추가설명
            data_container는 utils에서 호출한 instance를 사용한다. params에 적용하면 해당 변수는 전체 적용된다.
            백테스를 위한 자료이며, 실제 알고리즘 트레이딩시에는 필요 없다. 데이터의 흐름을 구현하기 위하여 만든 함수다.
        """
        # 하루의 총 분
        
        symbols = list(closing_sync_data.keys())
        intervals = list(closing_sync_data[symbols[0]])
        
        date_range = lookback_days
        timestamp_step = utils._get_interval_minutes('1d') * date_range

        indices_data = self.__generate_full_indices(closing_sync_data)
        base_indices = indices_data[intervals[0]]

        container_data = utils.DataContainer()

        for interval in intervals:
            select_indices = []
            for current_idx in base_indices:
                reference_data = indices_data[interval]
                start_idx = current_idx - timestamp_step
                if start_idx < 0:
                    start_idx
                condition = np.where((reference_data[:]>=start_idx)&
                                    (reference_data[:]<=current_idx))
                indices = indices_data[interval][condition]
                if current_idx > condition[0][-1]:
                    indices = np.append(indices, current_idx)
                select_indices.append(indices)
            container_data.set_data(data_name=f'interval_{interval}', data=select_indices)

        return container_data

        # original code
        # for interval in intervals:
        #     indices_data = []
        # # 데이터에서 각 인덱스 처리
        #     for current_index, data_point in enumerate(data_container.get_data(data_name=f'interval_{interval}')[0]):
        #         for series_index in range(len(data_container.get_data(data_name=f'interval_{interval}'))):
        #             # 시작 인덱스 계산 (interval에 따른 간격으로 조정)
        #             start_index = current_index - minutes_in_a_day * lookback_days
        #             start_index = (start_index // interval_to_minutes) * interval_to_minutes
        #             if start_index < 0:
        #                 start_index = 0

        #             # np.arange 생성
        #             interval_range = np.arange(start_index, current_index, interval_to_minutes)

        #             # current_index가 마지막 인덱스보다 크면 추가
        #             if current_index not in interval_range:
        #                 interval_range = np.append(interval_range, current_index)

        #             # (series_index, interval_range) 추가
        #             indices_data.append((series_index, interval_range))
        #     data_container.set_data(data_name=f'map_{interval}', data=indices_data)
        # return indices_data

    # Data Manager 함수를 일괄 실행 및 정리한다.
    async def data_manager_run(self, save: bool = False):
        kline_data = await self.generate_kline_interval_data(save=save)
        kline_data_array = utils._convert_to_array(kline_data=kline_data)
        closing_sync = self.generate_kline_closing_sync(
            kline_data=kline_data_array, save=True
        )
        data_container = utils._convert_to_container(kline_data=closing_sync)
        indices_data = self.get_indices_data(
            data_container=data_container, lookback_days=2, save=True
        )
        return kline_data_array, closing_sync, indices_data


class BacktestProcessor:
    """
    각종 연산이 필요한 함수들의 집함한다.
    """

    def __init__(self, max_leverage: int):
        self.ins_trade_futures_client = FuturesOrder()
        self.ins_trade_spot_client = SpotOrder()
        # self.ins_trade_stopper = DataProcess.TradeStopper()
        self.market_type = ["FUTURES", "SPOT"]
        self.max_leverage = max_leverage
        self.MIN_LEVERAGE = 5

    # 주문이 필요한 Qty, leverage를 계산한다.
    async def calculate_order_values(
        self,
        symbol: str,
        leverage: int,
        balance: float,
        market_type: str = "futures",
    ):
        """
        1. 기능 : 조건 신호 발생시 가상의 구매신호를 발생한다.
        2. 매개변수
        """
        market = market_type.upper()
        if market not in self.market_type:
            raise ValueError(f"market type 입력 오류 - {market}")

        if market == self.market_type[0]:
            ins_obj = self.ins_trade_futures_client
        else:
            ins_obj = self.ins_trade_spot_client

        # position stopper 초기값 설정
        # self.ins_trade_stopper(symbol=symbol, position=position, entry_price=entry_price)

        # print(date)
        # leverage 값을 최소 5 ~ 최대 30까지 설정.
        target_leverage = min(max(leverage, self.MIN_LEVERAGE), self.max_leverage)

        # 현재가 기준 최소 주문 가능량 계산
        get_min_trade_qty = await ins_obj.get_min_trade_quantity(symbol=symbol)
        # 조건에 부합하는 최대 주문 가능량 계산
        get_max_trade_qty = await ins_obj.get_max_trade_quantity(
            symbol=symbol, leverage=target_leverage, balance=balance
        )

        if get_max_trade_qty < get_min_trade_qty:
            return (False, get_max_trade_qty, target_leverage)

        return (True, get_max_trade_qty, target_leverage)


class OrderConstraint:
    """주문시 제약사항을 생성한다."""

    def __init__(
        self,
        increase_type: str,
        chance: int,
        step_interval: str,
        safety_ratio: float = 0.2,
        position_limit: int = 3,
    ):
        self.increase_type = increase_type
        self.safety_ratio = safety_ratio
        self.position_limit = position_limit

        self.chance: int = chance
        self.step_interval: str = step_interval

        self.total_balance: Optional[float] = None
        self.closed_trade_data: Optional[List[Any]] = None

        self.__verify_config()

    # def __init__ (self):
    #     self.target_count_min = 1
    #     self.target_count_max = 10

    #     self.account_amp_min = 10
    #     self.account_step = 5

    #     self.safety_account_ratio = 0.32

    def __verify_config(self):
        increase_types = ["stepwise", "proportional"]
        if not self.increase_type in increase_types or not isinstance(
            self.increase_type, str
        ):
            raise ValueError(f"increase_type 유효하지 않음:{self.increase_type}")

        if self.safety_ratio >= 1 or not isinstance(self.safety_ratio, float):
            raise ValueError(f"sefty ratio가 유효하지 않음:{self.safety_ratio}")

        if not isinstance(self.position_limit, int):
            raise ValueError(f"position_limit이 유효하지 않음:{self.position_limit}")

    def update_trading_data(
        self, closed_position: PortfolioManager, total_balance: PortfolioManager
    ):
        self.total_balance = total_balance
        self.closed_trade_data = closed_position

    # 반복적인 실패 Scenario주문을 방지하고자 실패 시나리오일 경우 주문 거절 신호를 발생한다.
    def validate_failed_scenario(
        self,
        symbol: str,
        scenario: int,
        closed_positions: PortfolioManager,
        current_timestamp: Optional[int] = None,
    ):
        """
        1. 기능: 반복적인 실패 Scenario주문을 방지하고자 실패 시나리오일 경우 주문 거절 신호를 발생한다.
        2. 매개변수:
            1) symbol : 쌍거래 symbol
            2) scenario : 적용될 시나리오
            3) closed_position : PortfolioManager의 속성값
            6) current_timestamp : 현재 시간, None일 경우 현재 시간을 생성
        """

        # 거래 종료 이력을 확인하고 없으면 True를 반환한다.
        if symbol not in closed_positions:
            return True

        # 거래 종료 데이터 np.array화
        data_array = np.array(closed_positions[symbol], float)

        # 현재 타임스탬프 설정
        if current_timestamp is None:
            current_timestamp = int(time.time() * 1_000)

        # interval별 밀리초 계산
        ms_seconds = utils._get_interval_ms_seconds(self.step_interval)
        target_timestamp = current_timestamp - ms_seconds

        # print(utils._convert_to_datetime(target_timestamp))
        # print(data_array[0][1])
        # 조건 필터링
        mask = (
            (data_array[:, 1] >= target_timestamp)  # last_timestamp > target_timestamp
            & (data_array[:, 16] == scenario)  # trade_scenario == scenario
            & (data_array[:, 13] < 0)  # gross_profit_loss < 0
        )
        filtered_count = np.sum(mask)  # 조건을 만족하는 데이터 개수

        # 허용된 chance보다 크면 이면 False 반환
        return filtered_count < self.chance

    # 보유가능한 항목과, 안전금액, 거래가능금액을 계산한다.
    def calc_fund(self, funds: float) -> dict:
        """
        총 자금과 안전 비율을 기반으로 보유 가능량과 다음 기준 금액 계산.

        Args:
            funds (float): 사용 가능한 총 자금.
            ratio (float): 안전 비율. 기본값은 0.35.

        Returns:
            dict: 계산 결과를 담은 딕셔너리.
        """
        # 자금이 10 미만일 경우 초기값 반환

        init_safety_value = round(10 * self.safety_ratio, 3)
        init_usable_value = 10 - init_safety_value
        init_trade_value = min(6, init_usable_value)

        if funds < 10:
            return {
                "count": 1,  # 보유 가능량
                "targetValue": 10,  # 다음 기준 금액
                "safetyValue": init_safety_value,  # 안전 금액
                "usableValue": init_usable_value,  # 유효 금액
                "tradeValue": init_trade_value,  # 회당 거래대금
            }

        steps = [2, 3]  # 증가 단계
        target = 5  # 초기 목표 금액
        count = 0  # 보유 가능량
        last_valid_target = 0  # 초과 이전의 유효한 목표 금액

        # 증가율 순환
        for step in steps:
            while target <= funds:
                last_valid_target = target  # 초과 전 단계 값 저장
                target *= step
                count += 1
                if target > funds:
                    break

        # count최대값을 지정한다. 너무 높면 회당 주문금액이 낮아진다.
        count = min(count, self.position_limit)

        count = 4
        
        # 안전 금액 및 유효 금액 계산
        safety_value = last_valid_target * self.safety_ratio
        usable_value = last_valid_target - safety_value
        trade_value = usable_value / count if count > 0 else 0

        # 결과 반환
        return {
            "count": count,  # 보유 가능량
            "targetValue": last_valid_target,  # 다음 기준 금액
            "safetyValue": safety_value,  # 안전 금액
            "usableValue": usable_value,  # 유효 금액
            "tradeValue": trade_value,  # 회당 거래대금
        }

    # # 거래가능횟수를 제한한다. 필요한가?
    # def get_transaction_capacity(self)

    # # 현재 보유금액에 다른 계산식을 만든다.
    # def calc_holding_limit(self)

    # # 회당 주문금액 계산
    # def calc_max_trade_amount(self)

    # total_balance_ =
    # available_balance_ =


class ResultEvaluator:
    def __init__(self, trade_analysis_ins):
        """
        초기화 메서드
        :param trade_analysis_ins: trade_analysis_ins 객체
        """
        self.trade_analysis_ins = trade_analysis_ins
        self.closed_positions = (
            trade_analysis_ins.closed_positions or {}
        )  # 청산된 포지션 초기화
        self.initial_balance = trade_analysis_ins.initial_balance
        self.total_balance = trade_analysis_ins.total_balance
        self.profit_loss = trade_analysis_ins.profit_loss
        self.profit_loss_ratio = trade_analysis_ins.profit_loss_ratio
        self.df = None  # 초기 데이터프레임 설정 (None)
        self.summary = None  # 요약 데이터 초기화

    def create_dataframe(self):
        """
        closed_positions를 DataFrame으로 변환
        :return: pandas DataFrame
        """
        if not self.closed_positions:
            print("Info: No data in closed_positions. Returning an empty DataFrame.")
            return pd.DataFrame(
                columns=[
                    "Symbol",
                    "Scenario",
                    "Position",
                    "Start Timestamp",
                    "End Timestamp",
                    "Leverage",
                    "Quantity",
                    "Entry Price",
                    "Exit Price",
                    "Net Profit/Loss",
                    "Gross Profit/Loss",
                    "Entry Fee",
                    "Exit Fee",
                    "Total Fee",
                ]
            )

        # 데이터 기록 생성
        records = []
        for symbol, trades in self.closed_positions.items():
            for trade in trades:
                records.append(
                    {
                        "Symbol": symbol,
                        "Scenario": trade[16],  # 시나리오 종류
                        "Position": "Long" if trade[2] == 1 else "Short",
                        "Start Timestamp": trade[0],
                        "End Timestamp": trade[1],
                        "Leverage": trade[3],
                        "Quantity": trade[4],
                        "Entry Price": trade[5],
                        "Exit Price": trade[8],
                        "Net Profit/Loss": trade[12],
                        "Gross Profit/Loss": trade[13],
                        "Entry Fee": trade[14],
                        "Exit Fee": trade[15],
                        "Total Fee": trade[14] + trade[15],  # 총 수수료 계산
                    }
                )

        return pd.DataFrame(records)

    def analyze_profit_loss(self):
        """
        거래 데이터를 분석하여 요약 통계를 생성
        :return: None
        """
        if self.df is None or self.df.empty:
            print("Warning: No data available to analyze.")
            self.summary = pd.DataFrame()  # 빈 요약 데이터프레임 생성
            return

        # 그룹별 요약 통계 계산
        summary = self.df.groupby(["Scenario", "Position", "Symbol"]).agg(
            Total_Profits=("Gross Profit/Loss", lambda x: x[x > 0].sum()),
            Total_Losses=("Gross Profit/Loss", lambda x: abs(x[x < 0].sum())),
            Max_Profit=("Gross Profit/Loss", "max"),
            Min_Loss=("Gross Profit/Loss", "min"),
            Gross_PnL=("Gross Profit/Loss", "sum"),
            Avg_PnL=("Gross Profit/Loss", "mean"),
            Trades=("Gross Profit/Loss", "count"),
            Total_Fees=("Total Fee", "sum"),
        )

        self.summary = summary

    def plot_profit_loss(self):
        """
        동일한 막대 그래프로 구성된 시각화.
        행: 각 시나리오, 열: Long, Short, Total
        최하단 행: Long_Total, Short_Total, Total
        """
        if self.summary is None or self.summary.empty:
            print("Warning: No data available for plotting.")
            return

        summary_reset = self.summary.reset_index()
        scenarios = summary_reset["Scenario"].unique()
        positions = ["Long", "Short", "Total"]

        # 총 행 수: 시나리오 수 + 1 (최하단 합계 행)
        total_rows = len(scenarios) + 1
        total_cols = len(positions)

        # Subplots 생성
        fig = make_subplots(
            rows=total_rows,
            cols=total_cols,
            subplot_titles=[
                f"{scenario}_{position}"
                for scenario in scenarios
                for position in positions
            ]
            + [f"Combined_{position}" for position in positions],
            vertical_spacing=0.1,
        )

        # X축의 기본 심볼 목록
        all_symbols = summary_reset["Symbol"].unique()
        if len(all_symbols) == 0:  # 심볼이 없으면 기본값 추가
            all_symbols = [f"Symbol_{i}" for i in range(5)]

        # 시나리오별 데이터 추가
        for row, scenario in enumerate(scenarios, start=1):
            for col, position in enumerate(positions, start=1):
                data = summary_reset[
                    (summary_reset["Scenario"] == scenario)
                    & (summary_reset["Position"] == position)
                ]

                # 데이터가 없으면 기본값 생성
                if data.empty:
                    data = pd.DataFrame(
                        {
                            "Symbol": all_symbols,
                            "Gross_PnL": [0] * len(all_symbols),
                        }
                    )

                fig.add_trace(
                    go.Bar(
                        x=data["Symbol"],
                        y=data["Gross_PnL"],
                        name=f"{scenario}_{position}",
                        marker=dict(
                            color=[
                                "#2ca02c" if v > 0 else "#d62728"
                                for v in data["Gross_PnL"]
                            ],
                            line=dict(color="black", width=2),  # 검정 테두리 추가
                        ),
                        text=[
                            f"{v:.2f}" for v in data["Gross_PnL"]
                        ],  # 소수점 2자리 표현
                        textposition="auto",
                    ),
                    row=row,
                    col=col,
                )

        # 합계 데이터 추가
        for col, position in enumerate(positions, start=1):
            total_data = (
                summary_reset[summary_reset["Position"] == position]
                .groupby("Symbol")
                .sum()
                .reset_index()
            )

            # 데이터가 없으면 기본값 생성
            if total_data.empty:
                total_data = pd.DataFrame(
                    {
                        "Symbol": all_symbols,
                        "Gross_PnL": [0] * len(all_symbols),
                    }
                )

            fig.add_trace(
                go.Bar(
                    x=total_data["Symbol"],
                    y=total_data["Gross_PnL"],
                    name=f"Combined_{position}",
                    marker=dict(
                        color=[
                            "#1f77b4" if v > 0 else "#ff7f0e"
                            for v in total_data["Gross_PnL"]
                        ],
                        line=dict(color="black", width=2),  # 검정 테두리 추가
                    ),
                    text=[
                        f"{v:.2f}" for v in total_data["Gross_PnL"]
                    ],  # 소수점 2자리 표현
                    textposition="auto",
                ),
                row=total_rows,
                col=col,
            )

        # 레이아웃 업데이트
        fig.update_layout(
            height=300 * total_rows,
            width=1800,  # 넓이를 2배로 확대
            title="📊 Scenario-Based Profit/Loss Analysis",
            title_font_size=20,
            template="plotly_white",
            showlegend=False,
            xaxis=dict(showgrid=True),  # X축 그리드 활성화
            yaxis=dict(showgrid=True),  # Y축 그리드 활성화
        )

        # 그래프 출력
        fig.show()

    def print_summary(self):
        """
        주요 잔고 정보를 출력
        :return: None
        """
        print(f"Initial Balance: {self.initial_balance:,.2f}")
        print(f"Total Balance: {self.total_balance:,.2f}")
        print(f"Gross Profit/Loss: {self.profit_loss:,.2f}")
        print(f"Profit/Loss Ratio: {self.profit_loss_ratio*100:.2f} %\n")

    def run_analysis(self):
        """
        전체 분석 실행
        :return: None
        """
        if self.df is None:  # 데이터프레임이 생성되지 않았다면 생성
            self.df = self.create_dataframe()

        self.analyze_profit_loss()
        self.print_summary()
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        pd.set_option("display.float_format", "{:,.2f}".format)
        print(self.summary)
        self.plot_profit_loss()
