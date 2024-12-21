import os
import utils
import Analysis
import time
import numpy as np
import pickle
import asyncio
import DataProcess
from numpy.typing import NDArray
from TradingDataManager import SpotTrade, FuturesTrade
from typing import Dict, List, Union, Any, Optional, Tuple
import utils
import datetime
from BinanceTradeClient import FuturesOrder, SpotOrder
from MarketDataFetcher import FuturesMarket, SpotMarket
from dataclasses import dataclass, fields
import pandas as pd

import matplotlib.pyplot as plt
from matplotlib import style, ticker

"""
1. 목적
    >>> 대입결과 최상의 이익조건을 찾고 실제 SystemTrading에 반영한다.
    >>> Binanace kline Data를 활용하여 각종 시나리오를 대입해본다.
    
2. 기능
    CLASS
        1) DataManager : 과거 데이터를 수신하고 실제 SystemTrading시 적용할 Data와 동일하게 생성한다.
            >>> 특정기간동안 데이터 수신
            >>> 수신 데이터를 1개의 dict파일로 구성
            >>> interval별 매칭 idx 데이터 생성
            >>> 1분봉 기준 실시간 데이터 생성
            
        2) TradeSignalManager : 주문(매수 또는 매도) 신호를 발생하고 해당 내용을 기록 누적 저장한다.
            >>> Marging 세팅
            >>> Leverage 세팅
            >>> 
            
            
        3) TradeStopperManager : 매도 또는 Stoploss구간을 계산한다. TradeSignal과 별개로 동작하게 한다.
            >>> 시나리오 1. entryPrice <-> highPrice간 비율 유지 
            >>> 시나리오 2. closePrice 지정 (수익률 지정, 도달시 매도)
            >>> 시나리오 3. 보유기간 지정 (특정기간 보유 후 자동 매매)
            >>> 시나리오 4. Spot / Futures Market 괴리율 검토.
            >>> 시나리오 5. 
            
        4) ClientManager : 주문 설정관련된 정보를 관리하다.
            >>> 주문가능 수량 계산
            
            
        4) WalletManager : 가상의 지갑정보를 생성한다. 주문(매수 또는 매도)에 따른 계좌정보를 update한다.
            >>> 기초 데이터 설정
            >>> 거래 발생시 출금처리
            >>> 거래 발생시 입금처리
            >>> 현재가 기준 계좌 가치 update
            
        
        5) SpecialMethodManager : __메소드를 관리하는 class이며 간단한 유틸리티 함수도 포함한다.



        6) 폐기함수.
        
3. 코드 구성 방향
    parameter는 다 받는다. 기본값을 None으로 하고 None입력시 내부에 저징된 변수값을 대입할 수 있도록 조치하낟.
    동기식으로 생성한다.

    저장은 별도의 함수를 구성해라. 한가지 함수에 너무 많은 기능을 담지마라.
"""




############################################################
############################################################
##
##  거래 내역 발생시 해당내역을 저장 및 관리하다.
##  각 속성별 값들은 최종적 update method를 활용하여 업데이트한다.
##
############################################################
############################################################

@dataclass
class TradingLog:
    """
    거래 발생시 거래내역에 대한 자세한 정보를 정리한다. 각종 손익비용에 대한 정보를 기록하여 분석할 수 있는 데이터로 활용한다.
    """
    
    symbol: str
    start_timestamp: int  # 시작 시간
    entry_price: Union[float, int]  # 진입 가격
    position: int  # 포지션 (1: Long, -1: Short)
    quantity: Union[float, int]  # 수량
    leverage: int  # 레버리지
    fee_rate: float = 0.05  # 수수료율
    trade_scenario: Optional[str] = None # 적용 시나리오 값.
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
            raise ValueError(
                f"레버리지는 최소 1 이상이어야 합니다. 현재 값: {self.leverage}"
            )
        if self.end_time is None:
            self.end_time = self.start_timestamp
        self.__update_fees()
        self.__update_values()

    def __update_fees(self):
        adjusted_fee_rate = self.fee_rate / 100
        self.entry_fee = (
            self.entry_price * adjusted_fee_rate * self.quantity# * self.leverage
        )
        self.exit_fee = (
            self.current_price * adjusted_fee_rate * self.quantity# * self.leverage
        )
        total_fees = self.entry_fee + self.exit_fee
        self.break_even_price = self.entry_price + (total_fees / self.quantity)

    def __update_values(self):
        # self.initial_value = (self.entry_price * self.quantity) / self.leverage
        self.initial_value = (self.quantity / self.leverage) * self.entry_price
        self.current_value = (self.current_price * self.quantity) / self.leverage
        total_fees = self.entry_fee + self.exit_fee
        # self.profit_loss = self.current_value - self.initial_value - total_fees
        self.profit_loss = self.quantity * (self.current_price - self.entry_price) - total_fees

    def update_trade_data(self, current_price: Union[float, int], current_time: int):
        self.current_price = current_price
        self.end_time = current_time
        self.__update_fees()
        self.__update_values()

    def to_list(self):
        return list(self.__dict__.values())


class TradeAnalysis:
    """
    거래발생시 해당내용을 가상 wallet에 저장하여 각종 손익비용을 분석한다. 분석한 데이터를 토대로 테스트종료시 결과를 계산할 베이스 데이터가 된다.
    """
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

    # 거래 종료시 positions 정보를 self.close_positios에 저장 또는 추가한다.
    def add_closed_position(self, trade_order_data: list):
        """
        1. 기능 : 거래 포지션 종료시 해당 내역을 self.closed_positions에 추가 저장한다.
        2. 매개변수
            1) trade_order_data : class TradingLog data
        """
        
        # symbol값을 index값으로 찾는다.
        # trade_order_data는 Class TradingLog 데이터를 적용한다
        symbol = trade_order_data[0]
        # self.closed_positions에 symbol값이 없을 경우 신규 값으로 기록 한다.
        if symbol not in self.closed_positions:
            # index [1:]은 Class TradingLog 의 등록된 속성값중 symbol값 제외 모든 데이터를 포함한다.
            self.closed_positions[symbol] = [trade_order_data[1:]]
        # self.closed_positions에 symbol값이 있을 경우 기존 값에 추가 기록 한다.
        else:
            # index [1:]은 Class TradingLog 의 등록된 속성값중 symbol값 제외 모든 데이터를 포함한다.
            self.closed_positions[symbol].append(trade_order_data[1:])
        # positions이 종료 됐으므로 self.open_postion에서 해당 symbol값을 제거한다.
        del self.open_positions[symbol]
        # wallet 정보를 업데이트해서 각 속성값들을 업데이트(계산) 한다.
        self.update_wallet()
        # self.closed_positions값을 반환한다.
        # 필수 기능 아님.
        return self.closed_positions

    # 거래 발생시 positions 정보를 self.open_positios에 저장 한다.
    def add_open_position(self, trade_order_data: list):
        """'
        1. 기능 : 거래 포지션 종료시 해당 내역을 self.open_positions에 저장한다.
        2. 매개변수
            1) trade_order_data : class TradingLog data
        """
        # symbol값을 index값으로 찾는다.
        # trade_order_data는 Class TradingLog 데이터를 적용한다
        symbol = trade_order_data[0]
        # index [1:]은 Class TradingLog 의 등록된 속성값중 symbol값 제외 모든 데이터를 포함한다.
        self.open_positions[symbol] = trade_order_data[1:]
        # wallet 정보를 업데이트해서 각 속성값들을 업데이트(계산) 한다.
        self.update_wallet()
        # self.open_positions값을 반환한다.
        # 필수 기능 아님.
        return self.open_positions

    # 속성값에 저장된 값을 업데이트(계산)하여 재 반영한다.
    def update_wallet(self):
        """
        1. 기능 : 본 class에 저장된 속성값들을 업데이트해서 현재 가상 계좌의 가치를 재평가한다.
        2. 매개변수 : 해당없음.
        """
        
        # 모든 거래정보를 저장할 변수를 초기화 한다.
        all_trades_data = []
        # 현재 진행중인 거래정보를 저장할 변수를 초기화 한다.
        open_trades_data = []

        # 종료된 포지션 거래가 존재시
        if self.closed_positions:
            # 종료된 포지션 정보의 value값을 찾아서
            for _, trades_close in self.closed_positions.items():
                # all_trade_data에 extend로 추가한다. 
                # closed_positions은 2차원 list형태로 저장되므로 append가 아닌 extend를 이용한다.
                all_trades_data.extend(trades_close)

        # 진행중인 포지션 거래가 존재시
        if self.open_positions:
            # 진행중인 포지션 정보의 value값을 찾아서
            for _, trades_open in self.open_positions.items():
                # all_trade_data에 append로 추가한다.
                # closed_positions과 달리 open_position은 불타기/물타기를 지원하지 않으므로 1차원 데이터로 저장된다.
                all_trades_data.append(trades_open)
                # 진행중인 포지션 정보의 value값을 별도로 추가한다.
                open_trades_data.append(trades_open)

        # 현재 진행중인 포지션의 갯수(길이)를 확인한다.
        open_position_length = len(self.open_positions)
        # 현재 진행중인 포지션이 없다면,
        if open_position_length == 0:
            # 거래중인 포지션은 없음.
            self.number_of_stocks = 0
        # 현재 진행중인 포지션이 있다면,
        elif open_position_length > 0:
            # 거래중인 포지션의 갯수를 저장한다.
            self.number_of_stocks = open_position_length

        # 종료된 거래와 현재 진행된 거래가 없을경우
        if not self.closed_positions and not self.open_positions:
            # 진행중인 거래대금 없음 적용
            self.active_value = 0
            # 예수금과 평가 금액을 동일하게 설정.
            self.cash_balance = self.total_balance
            # 본 함수 종료
            return

        # 위 조건 통과시(종료된 거래와 현재 진행된 거래가 있을 경우)
        # 전체 거래내역(거래중) 정보를 np.ndarray화 한다.
        all_trades_data_array = np.array(all_trades_data)
        # 거래중 정보를 np.ndarray화 한다.
        open_trades_data_array = np.array(open_trades_data)

        # 행의 길이가 1이하면 연산이 불가하므로 변환 별도의 작업을 해야한다.
        # 행 길이 정보를 확인하여 길이가 1이라면,
        if all_trades_data_array.ndim == 1:
            # 2차원 배열로 변환 (행 기준)
            all_trades_data_array = all_trades_data_array.reshape(1, -1)
        
        # 행 길이 정보를 확인하여 길이가 1이라면,
        if open_trades_data_array.ndim == 1:
            # 2차원 배열로 변환 (행 기준)
            open_trades_data_array = open_trades_data_array.reshape(1, -1)

        # 수수료와 관련된 비용
        # entry_fee : index 13
        # exit_fee : index 14
        # initial_value : index 8
        # open or close position 추가시 index 0값을 제외하고 저장하므로 index 0은 start_timestamp가 적용됨.
        
        # 수수료 관련 비용
        # entry_fee[13] + exit_fee[14]
        sunk_cost = np.sum(all_trades_data_array[:, [13, 14]])
        # 진입과 관련된 비용
        entry_cost = np.sum(all_trades_data_array[:, 8])
        
        # 진입비용 + 수수료 전체
        total_cost = sunk_cost + entry_cost
        # 현재 평가 가치
        recovered_value = np.sum(all_trades_data_array[:, 9])


        ##################################################################################
        # 아래 함수가 필요할까? 그냥 self.active_value = entry_cost로 하는게 나을수도.
        ##################################################################################
        
        # 거래중인 자산 업데이트
        if open_trades_data_array.size > 0:
            # 거래중인 자산금액 == 진입 관련 비용
            self.active_value = entry_cost#np.sum(open_trades_data_array[:, 8])
        else:
            # 거래중인 자산 없을경우 0
            self.active_value = 0

        self.cash_balance = self.initial_balance - self.active_value
        self.profit_loss = np.sum(all_trades_data_array[:, 10])
        self.profit_loss_ratio = round(
            (self.profit_loss / self.initial_balance) * 100, 3
        )
        self.total_balance = self.cash_balance + self.active_value + self.profit_loss

        if self.cash_balance < 0:
            raise ValueError(f"주문 오류 : 진입금액이 예수금을 초과함.")

        # 계좌 가치가 0 미만이면 청산신호 발생 및 프로그램 중단.
        if self.total_balance < 0:
            raise ValueError(f"청산발생 : 계좌잔액 없음.")


class TradeOrderManager:
    """
    주문관련 기능을 수행한다. TradeAnalysis, TradingLog 두 class를 운용한다.
    """
    def __init__(self, initial_balance: float = 1_000):
        self.active_orders: List[TradingLog] = []
        self.order_index_map = {}
        self.active_symbols: List[str] = []
        self.trade_analysis = TradeAnalysis(initial_balance=initial_balance)

    def __refresh_order_map(self):
        self.order_index_map = {
            order.symbol: idx for idx, order in enumerate(self.active_orders)
        }
        self.active_symbols = list(self.order_index_map.keys())

    def add_order(self, **kwargs):
        if kwargs.get("symbol") in self.order_index_map:
            return

        valid_keys = {field.name for field in fields(TradingLog)}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        order = TradingLog(**filtered_kwargs)

        self.active_orders.append(order)
        self.__refresh_order_map()

        order_signal = order.to_list()
        self.trade_analysis.add_open_position(order_signal)
        return order

    def remove_order(self, symbol: str):
        idx = self.order_index_map.get(symbol)
        order_signal = self.active_orders[idx].to_list()
        self.trade_analysis.add_closed_position(order_signal)
        del self.active_orders[idx]
        self.__refresh_order_map()

    def update_order_data(
        self, symbol: str, current_price: Union[float, int], current_time: int
    ):
        idx = self.order_index_map.get(symbol)
        if idx is None:
            return
        self.active_orders[idx].update_trade_data(
            current_price=current_price, current_time=current_time
        )
        trade_order_data = self.active_orders[idx].to_list()
        self.trade_analysis.add_open_position(trade_order_data)

    def get_order(self, symbol: str):
        idx = self.order_index_map.get(symbol)
        return self.active_orders[idx]


class DataManager:
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
        self.ins_trade_spot = SpotTrade()
        self.ins_trade_futures = FuturesTrade()

        # kline 데이터 수신을 위한 호출
        self.ins_market_spot = SpotMarket()
        self.ins_market_futures = FuturesMarket()

        self.storeage = "DataStore"
        self.kline_closing_sync_data = "closing_sync_data.pkl"
        self.indices_file = "indices_data.json"
        self.kline_data_file = "kline_data.json"
        self.parent_directory = os.path.dirname(os.getcwd())

    # 장기간 kline data수집을 위한 date간격을 생성하여 timestamp형태로 반환한다.
    def __generate_timestamp_ranges(
        self, interval: str, start_date: str, end_date: str
    ) -> List[List[int]]:
        if start_date is None:
            start_date = self.start_date
        if end_date is None:
            end_date = self.end_date

        interval_to_milliseconds = {
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
        }

        # 시작 및 종료 날짜 문자열 처리
        # 시간 정보는 반드시 00:00:00 > 23:59:59로 세팅해야 한다. 그렇지 않을경우 수신에 문제 발생.
        start_date = start_date + " 00:00:00"
        end_date = end_date + " 23:59:59"

        # interval에 따른 밀리초 단위 스텝 가져오기
        interval_step = interval_to_milliseconds.get(interval)

        # Limit 값은 1,000이나 유연한 대처를 위해 999 적용
        MAX_LIMIT = 1_000

        # 시작 타임스탬프
        start_timestamp = utils._convert_to_timestamp_ms(date=start_date)
        # interval 및 MAX_LIMIT 적용으로 계산된 최대 종료 타임스탬프
        max_possible_end_timestamp = start_timestamp + (interval_step * MAX_LIMIT) - 1
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
        start_time = datetime.datetime.now()
        aggregated_results = {}

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

    # 1분봉 종가 가격을 각 interval에 반영한 테스트용 더미 데이터를 생성한다.
    def generate_kline_closing_sync(self, kline_data: Dict, save: bool = False):
        """
        1. 기능 : 백테스트시 데이터의 흐름을 구현하기 위하여 1분봉의 누적데이터를 반영 및 1분봉의 길이와 맞춘다.
        2. 매개변수
            1) kline_data : kline_data 를 numpy.array화 하여 적용
            2) save : 생성된 데이터 저장여부.


        """
        # 심볼 및 interval 값을 리스트로 변환
        symbols_list = list(kline_data.keys())
        intervals_list = list(kline_data[symbols_list[0]].keys())

        # np.arange시 전체 shift처리위하여 dummy data를 추가함.
        dummy_data = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        # 최종 반환 데이터를 초기화
        output_data = {}

        for symbol, kline_data_symbol in kline_data.items():
            # 최종 반환 데이터에 심볼별 키 초기화
            output_data[symbol] = {}

            # 가장 작은 단위 interval 데이터를 기준으로 기준 데이터를 생성
            reference_data = kline_data[symbol][intervals_list[0]]

            for interval, kline_data_interval in kline_data_symbol.items():
                if interval == intervals_list[0]:
                    # np.arange길이 맞추기 위해 dummy data 삽입
                    new_row = np.insert(
                        reference_data, 0, dummy_data, axis=0
                    )  # reference_data.insert(0, dummy_data)
                    output_data[symbol][interval] = new_row
                    continue

                combined_data = []
                output_data[symbol][interval] = {}

                for idx, reference_entry in enumerate(reference_data):
                    target_open_timestamp = reference_entry[0]
                    target_close_timestamp = reference_entry[6]

                    # 기준 조건에 맞는 데이터 검색
                    condition = np.where(
                        (kline_data_interval[:, 0] <= target_open_timestamp)
                        & (kline_data_interval[:, 6] >= target_close_timestamp)
                    )[0]

                    if len(condition) != 1:
                        print(f"{symbol} - {interval} - {condition}")

                    reference_open_timestamp = kline_data_interval[condition, 0][0]
                    reference_close_timestamp = kline_data_interval[condition, 6][0]

                    if len(combined_data) == 0 or not np.array_equal(
                        combined_data[-1][0], reference_open_timestamp
                    ):
                        new_entry = [
                            reference_open_timestamp,
                            reference_entry[1],
                            reference_entry[2],
                            reference_entry[3],
                            reference_entry[4],
                            reference_entry[5],
                            reference_close_timestamp,
                            reference_entry[7],
                            reference_entry[8],
                            reference_entry[9],
                            reference_entry[10],
                            0,
                        ]
                    elif np.array_equal(reference_data[6], reference_close_timestamp):
                        new_entry = kline_data_interval
                    else:
                        previous_entry = combined_data[-1]
                        new_entry = [
                            reference_open_timestamp,
                            previous_entry[1],
                            max(previous_entry[2], reference_entry[2]),
                            min(previous_entry[3], reference_entry[3]),
                            reference_entry[4],
                            previous_entry[5] + reference_entry[5],
                            reference_close_timestamp,
                            previous_entry[7] + reference_entry[7],
                            previous_entry[8] + reference_entry[8],
                            previous_entry[9] + reference_entry[9],
                            previous_entry[10] + reference_entry[10],
                            0,
                        ]
                    combined_data.append(new_entry)

                combined_data.insert(0, dummy_data)
                output_data[symbol][interval] = np.array(
                    object=combined_data, dtype=float
                )
        if save:
            path = os.path.join(
                self.parent_directory, self.storeage, self.kline_closing_sync_data
            )
            with open(file=path, mode="wb") as file:
                pickle.dump(output_data, file)
        return output_data

    # generate_kline_closing_sync index 자료를 생성한다.
    def get_indices_data(
        self, data_container, lookback_days: int = 2, save: bool = False
    ):
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
        minutes_in_a_day = 1440

        # interval에 따른 간격(분) 정의
        interval_to_minutes = {
            "1m": 1,
            "3m": 3,
            "5m": 5,
            "15m": 15,
            "30m": 30,
            "1h": 60,
            "2h": 120,
            "4h": 240,
            "6h": 360,
            "8h": 480,
            "12h": 720,
            "1d": 1440,
        }

        indices_data = []

        data_container_name = data_container.get_all_data_names()
        intervals = [interval.split("_")[1] for interval in data_container_name]

        for interval in intervals:
            indices_data = []
            # 데이터에서 각 인덱스 처리
            for current_index, data_point in enumerate(
                data_container.get_data(data_name=f"interval_{interval}")[0]
            ):
                for series_index in range(
                    len(data_container.get_data(data_name=f"interval_{interval}"))
                ):
                    # 시작 인덱스 계산 (interval에 따른 간격으로 조정)
                    start_index = current_index - minutes_in_a_day * lookback_days
                    start_index = (
                        start_index // interval_to_minutes.get(interval)
                    ) * interval_to_minutes.get(interval)
                    if start_index < 0:
                        start_index = 0

                    # np.arange 생성
                    interval_range = np.arange(
                        start_index, current_index, interval_to_minutes.get(interval)
                    )

                    # current_index가 마지막 인덱스보다 크면 추가
                    if current_index not in interval_range:
                        interval_range = np.append(interval_range, current_index)

                    # (series_index, interval_range) 추가
                    indices_data.append((series_index, interval_range))
            data_container.set_data(data_name=f"map_{interval}", data=indices_data)

        if save:
            path = os.path.join(self.parent_directory, self.storeage, self.indices_file)
            utils._save_to_json(
                file_path=indices_data, new_data=indices_data, overwrite=True
            )
        return indices_data

        # original code
        # for interval in intervals:
        #     indices_data = []
        # # 데이터에서 각 인덱스 처리
        #     for current_index, data_point in enumerate(data_container.get_data(data_name=f'interval_{interval}')[0]):
        #         for series_index in range(len(data_container.get_data(data_name=f'interval_{interval}'))):
        #             # 시작 인덱스 계산 (interval에 따른 간격으로 조정)
        #             start_index = current_index - minutes_in_a_day * lookback_days
        #             start_index = (start_index // interval_to_minutes.get(interval)) * interval_to_minutes.get(interval)
        #             if start_index < 0:
        #                 start_index = 0

        #             # np.arange 생성
        #             interval_range = np.arange(start_index, current_index, interval_to_minutes.get(interval))

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


class ProcessManager:
    """
    각종 연산이 필요한 함수들의 집함한다. 
    """

    def __init__(self):
        self.ins_trade_futures_client = FuturesOrder()
        self.ins_trade_spot_client = SpotOrder()
        self.ins_trade_stopper = DataProcess.TradeStopper()
        self.market_type = ["FUTURES", "SPOT"]
        self.MAX_LEVERAGE = 30
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
        target_leverage = min(max(leverage, self.MIN_LEVERAGE), self.MAX_LEVERAGE)

        # 현재가 기준 최소 주문 가능량 계산
        get_min_trade_qty = await ins_obj.get_min_trade_quantity(symbol=symbol)
        # 조건에 부합하는 최대 주문 가능량 계산
        get_max_trade_qty = await ins_obj.get_max_trade_quantity(
            symbol=symbol, leverage=target_leverage, balance=balance
        )

        if get_max_trade_qty < get_min_trade_qty:
            print("기본 주문 수량 > 최대 주문 수량")
            return (False, get_max_trade_qty, target_leverage)

        return (True, get_max_trade_qty, target_leverage)



class ResultEvaluator:
    def __init__(self, data):
        # with open(file_path, 'r') as file:
        #     data = json.load(file)

        self.closed_positions = data.closed_positions
        self.initial_balance = data.initial_balance
        self.total_balance = data.total_balance
        self.profit_loss = data.profit_loss
        self.profit_loss_ratio = data.profit_loss_ratio
        self.df = self.create_dataframe()
        self.summary = None

    def create_dataframe(self):
        if not self.closed_positions:
            # 빈 딕셔너리일 경우 0으로 채운 기본 데이터프레임 반환
            return pd.DataFrame([{
                "Symbol": None,
                "Close Time": None,
                "Profit/Loss": 0.0,
                "Entry Price": 0.0,
                "Exit Price": 0.0,
                "Volume": 0.0,
                "Entry Fee": 0.0,
                "Exit Fee": 0.0,
                "Total Fee": 0.0
            }])

        # 데이터가 있을 경우 데이터프레임 생성
        records = []
        for symbol, trades in self.closed_positions.items():
            for trade in trades:
                records.append(
                    {
                        "Symbol": symbol,
                        "Close Time": trade[6],
                        "Profit/Loss": trade[9],
                        "Entry Price": trade[1],
                        "Exit Price": trade[10],
                        "Volume": trade[2],
                        "Entry Fee": trade[-2],
                        "Exit Fee": trade[-1],
                        "Total Fee": trade[-2] + trade[-1],
                    }
                )
        return pd.DataFrame(records)

    def analyze_profit_loss(self):
        summary = self.df.groupby("Symbol").agg(
            Total_Profits=("Profit/Loss", lambda x: x[x > 0].sum()),
            Total_Losses=("Profit/Loss", lambda x: abs(x[x < 0].sum())),
            Max_Profit=(
                "Profit/Loss",
                lambda x: x[x > 0].max() if not x[x > 0].empty else 0,
            ),
            Min_Profit=(
                "Profit/Loss",
                lambda x: x[x > 0].min() if not x[x > 0].empty else 0,
            ),
            Max_Loss=(
                "Profit/Loss",
                lambda x: x[x < 0].min() if not x[x < 0].empty else 0,
            ),
            Min_Loss=(
                "Profit/Loss",
                lambda x: x[x < 0].max() if not x[x < 0].empty else 0,
            ),
            Net_PnL=("Profit/Loss", "sum"),
            Avg_PnL=("Profit/Loss", "mean"),
            Trades=("Profit/Loss", "count"),
            Total_Entry_Fees=("Entry Fee", "sum"),
            Total_Exit_Fees=("Exit Fee", "sum"),
            Total_Fees=("Total Fee", "sum"),
        )
        summary.loc["Total"] = summary.sum(numeric_only=True)
        summary.loc["Total", "Trades"] = self.df[
            "Symbol"
        ].count()  # 합계 행의 거래 횟수 수동 조정
        # 컬럼 순서 조정: Total_Fees를 가장 마지막으로 이동
        column_order = [
            "Total_Profits",
            "Total_Losses",
            "Max_Profit",
            "Min_Profit",
            "Max_Loss",
            "Min_Loss",
            "Net_PnL",
            "Avg_PnL",
            "Trades",
            "Total_Entry_Fees",
            "Total_Exit_Fees",
            "Total_Fees",
        ]
        self.summary = summary[column_order].fillna(0)

    def plot_profit_loss(self):
        if self.summary is None:
            raise ValueError(
                "Summary has not been calculated. Run analyze_profit_loss first."
            )

        style.use("ggplot")  # 세련된 스타일 적용
        plt.figure(figsize=(12, 6), facecolor="white")  # 배경 흰색
        sorted_summary = self.summary.drop("Total", errors="ignore").sort_values(
            "Net_PnL"
        )
        bar_width = 0.6  # 스틱 두께 조정

        # 순손익 바
        plt.bar(
            sorted_summary.index,
            sorted_summary["Net_PnL"],
            color="#1f77b4",
            edgecolor="black",
            linewidth=1.5,
            label="Net PnL",
            width=bar_width,
        )

        # 수익과 손실 바 겹쳐 그리기
        plt.bar(
            sorted_summary.index,
            sorted_summary["Total_Profits"],
            color="#2ca02c",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
            label="Total Profits",
            width=bar_width,
        )
        plt.bar(
            sorted_summary.index,
            -sorted_summary["Total_Losses"],
            color="#d62728",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
            label="Total Losses",
            width=bar_width,
        )

        # 텍스트 크기 조정
        plt.title("Profit/Loss Breakdown by Symbol", fontsize=14)
        plt.ylabel("Profit/Loss (with commas)", fontsize=12)
        plt.xlabel("Symbol", fontsize=12)
        plt.xticks(rotation=45, fontsize=10)

        # 천 단위 쉼표 추가
        ax = plt.gca()
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

        plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.show()

    def print_summary(self):
        print(f"Initial Balance: {self.initial_balance:,.2f}")
        print(f"Total Balance: {self.total_balance:,.2f}")
        print(f"Net Profit/Loss: {self.profit_loss:,.2f}")
        print(f"Profit/Loss Ratio: {self.profit_loss_ratio:.2f}%")
        print()

    def run_analysis(self):
        self.analyze_profit_loss()
        self.print_summary()
        # 데이터프레임 전체 출력 설정
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        pd.set_option("display.float_format", "{:,.2f}".format)
        print(self.summary)
        self.plot_profit_loss()
