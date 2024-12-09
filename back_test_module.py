import os
import utils
import Analysis
from typing import Dict, List, Union, Any, Optional
import time

# from Analysis import AnalysisManager


def update_data(kline_path: str, index_path: str):
    if not os.path.exists(kline_path):
        raise ValueError(f"{kline_path} path가 올바르지 않음.")
    if not os.path.exists(index_path):
        raise ValueError(f"{index_path} path가 올바르지 않음.")
    kline_data = utils._load_json(file_path=kline_path)
    index_data = utils._load_json(file_path=index_path)
    return (kline_data, index_data)


# 임시생성 함수
def signal(analy_data):
    if analy_data[2] and analy_data[4]:
        position = "LONG" if analy_data[0] == 1 else "SHORT"
        leverage = analy_data[3]
        return {"position": position, "leverage": leverage}
    else:
        return False


class DataManager:
    def __init__(self, kline_data, index_data):
        self.kline_data = kline_data
        self.index_data = index_data
        self.intervals = list(kline_data.keys())
        self.__validate_data()

    # 데이터의 유효성을 검사한다.
    def __validate_data(self):
        """
        1. 기능 : instance 선언시 입력되는 변수값의 유효성을 검사한다.
        2. 매개변수 : 해당없음.
        """
        if not isinstance(self.kline_data, dict) or not self.kline_data:
            raise ValueError(f"kline 데이터가 유효하지 않음.")
        if not isinstance(self.index_data, list) or not self.index_data:
            raise ValueError(f"index 데이터가 유효하지 않음.")
        if len(self.kline_data.keys()) != len(self.index_data[0]):
            raise ValueError(f"kline interval값과 index 데이터의 길이가 맞지 않음.")
        return True

    # 연산이 용이하도록 interval값과 index값을 이용하여 매핑값을 반환한다.
    def __map_intervals_to_indices(self, index_values: List[int]) -> Dict[str, int]:
        """
        1. 기능 : interval과 index데이터를 연산이 용이하도록 매핑한다.
        2. 매개변수
            1) index_values : 각 구간별 index 정보
        """
        mapped_intervals = {}
        for i, interval in enumerate(self.intervals):
            mapped_intervals[interval] = index_values[i]

        return mapped_intervals

    # 기간별 각 interval값을 raw데이터와 동일한 형태로 반환한다.
    def get_kline_data_by_range(
        self, end_index: int, step: int = 4320
    ) -> Dict[str, List[List[Union[int, str]]]]:
        """
        1. 기능 : 기간별 데이터를 추출한다.
        2. 매개변수
            1) start_index : index 0 ~ x까지 값을 입력
            2) step : 데이터 기간(min : 4320
                - interval max값의 minute변경 (3d * 1min * 60min/h * 24hr/d)
        """
        start_index = end_index - step
        if start_index < 0:
            start_index = 0
        start_indices = self.index_data[start_index]
        end_indices = self.index_data[end_index]

        start_mapped_intervals = self.__map_intervals_to_indices(
            index_values=start_indices
        )
        end_mapped_intervals = self.__map_intervals_to_indices(index_values=end_indices)

        result = {}
        for interval in self.intervals:
            interval_data = self.kline_data.get(interval)
            start_index_value = start_mapped_intervals.get(interval)
            end_index_value = end_mapped_intervals.get(interval)

            sliced_data = interval_data[start_index_value:end_index_value]
            result[interval] = sliced_data
        return result


class SignalRecorder:
    """
    가상 거래 내역을 기록하고 해당 내용을 공유한다.
    """

    def __init__(self):
        self.trade_history: List[Dict[str, Union[Any]]] = []

    def submit_trade_open_signal(
        self,
        position: bool,
        nested_kline_data: list[Union[str, int]],
        leverage: int,
        quantity: float,
        analysis_type: str = "anylisys_1",
    ):
        close_timestamp = nested_kline_data[6]
        close_price = nested_kline_data[4]
        trade_data = {
            "tradeStatus": True,
            "executionTimestamp": close_timestamp,
            # "executionDate": utils._convert_to_datetime(close_timestamp),
            "price": float(close_price),
            "position": position,
            "leverage": leverage,
            "quantity": quantity,
        }
        self.trade_history.append(trade_data)
        return trade_data

    def submit_trade_close_signal(
        self, nested_kline_data: list[Union[str, int]], stoploss_type: str = "stop_1"
    ):
        close_timestamp = nested_kline_data[6]
        close_price = nested_kline_data[4]
        quantity = self.trade_history[-1].get("quantity")
        leverage = self.trade_history[-1].get("leverage")
        last_position = self.trade_history[-1].get("position")
        position = "LONG" if last_position == "SHORT" else "SHORT"
        datetime = utils._convert_to_datetime(close_timestamp)
        trade_data = {
            "tradeStatus": False,
            "executionTimestamp": close_timestamp,
            # "executionDate": utils._convert_to_datetime(close_timestamp),
            "price": close_price,
            "position": position,
            "leverage": leverage,
            "quantity": quantity,
        }
        self.trade_history.append(trade_data)
        return trade_data

    def dump_to_json(self, file_path: str):
        utils._save_to_json(
            file_path=file_path, new_data=self.trade_history, overwrite=True
        )
        return

    def get_trade_history(self):
        return self.trade_history


class TradeStopper:
    def __init__(self, rist_ratio: float = 0.85, profit_ratio: float = 0.015):
        self.reference_price: Optional[float] = None

        self.risk_ratio = rist_ratio
        self.profit_ratio = profit_ratio
        self.target_price: Optional[float] = None

    def __clear_price_info(self):
        self.reference_price = None
        self.target_price = None

    def __trade_status(self, trade_history) -> bool:
        trade_data = trade_history[-1]
        return trade_data.get("tradeStatus")

    def __calculate_target_price(
        self, entry_price: float, reference_price: float, position: str
    ) -> float:
        position = position.upper()
        if position not in ["LONG", "BUY", "SELL", "SHORT"]:
            raise ValueError(f"유효하지 않은 포지션: {position}")
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
            raise ValueError(f"position입력오류 : {position}")

    def generate_close_signal_scenario1(
        self, nested_kline_data: list[Union[str, int]], trade_history: list
    ) -> bool:
        if not self.__trade_status(trade_history=trade_history):
            return False

        current_price = float(nested_kline_data[4])
        current_position = trade_history[-1].get("position")
        # Reference price 업데이트
        if not self.reference_price:
            self.reference_price = current_price

        if current_position in ["LONG", "BUY"]:
            self.reference_price = max(self.reference_price, current_price)
        elif current_position in ["SHORT", "SELL"]:
            self.reference_price = min(self.reference_price, current_price)

        # self.reference_price = reference_price

        # utils._std_print(self.reference_price)
        # Target price 계산
        self.target_price = self.__calculate_target_price(
            entry_price=current_price,
            reference_price=self.reference_price,
            position=current_position,
        )

        # 종료 조건
        if current_position in ["LONG", "BUY"] and current_price <= self.target_price:
            self.__clear_price_info()
            return True
        elif (
            current_position in ["SHORT", "SELL"] and current_price >= self.target_price
        ):
            self.__clear_price_info()
            return True

        return False


class Wallet:
    def __init__(self, initial_capital: float = 1_000, fee_ratio: float = 0.05):
        self.initial_capital: float = initial_capital
        self.fee_ratio: float = fee_ratio
        self.fee_value: float = 0
        self.free: float = initial_capital
        self.lock: float = 0
        self.total_balance: float = 0
        self.profit_to_loss_ratio: float = 0
        self.safety_ratio: float = 0.35
        self.available_value: float = initial_capital * (1 - self.safety_ratio)

    # 청산시 오류발생, 시스템 멈춤
    def __vaildate_balance(self):
        if self.free < 0:
            raise ValueError(f"{self.free} - 청산 발생")

    # 손익비율 계산
    def __cals_profit_to_loss_ratio(self):
        total_balance = self.lock + self.free
        cals_ratio = total_balance / self.initial_capital
        return round(cals_ratio, 3)

    # 안전 자산 외 자산
    def __cals_available_value(self):
        return self.total_balance * (1 - self.safety_ratio)

    # 잔고 총액 계산
    def __cals_total_balance(self):
        return self.free + self.lock

    # 출금 처리
    def withdrawal(self, USDT: float):
        self.__vaildate_balance()
        self.fee_value += self.fee_ratio * USDT
        value = USDT - self.fee_value
        self.free = self.free - USDT
        self.lock += value
        self.total_balance = self.__cals_total_balance()
        self.available_value = self.__cals_available_value()
        self.profit_to_loss_ratio = self.__cals_profit_to_loss_ratio()
        self.__vaildate_balance()

    # 입금 처리
    def deposit(self, USDT: float):
        value = (1 - self.fee_ratio) * USDT
        self.fee_value += self.fee_ratio * USDT
        self.lock = 0
        self.free += self.lock
        self.__cals_total_balance()
        self.__cals_available_value()
        self.__cals_profit_to_loss_ratio()

    # 실시간 wallet의 lock을 업데이트 한다.
    def realtime_wallet_update(self, curreutn_price: float, trade_history: dict):
        last_trade_history = trade_history[-1]
        leverage = last_trade_history.get("leverage")
        quantity = last_trade_history.get("quantity")
        return (current_price * quantity) / leverage

    # 계좌정보 반환
    def get_account_balance(self):
        return {
            "inital_money": self.initial_capital,
            "fee_ratio": self.fee_ratio,
            "fee_value": self.fee_value,
            "free": self.free,
            "lock": self.lock,
            "total_balance": self.total_balance,
            "profit_loss_ratio": self.profit_to_loss_ratio,
            "safety_ratio": self.safety_ratio,
        }


if __name__ == "__main__":
    directory = "/Users/cjupit/Documents/GitHub/DataStore"
    kline = os.path.join(directory, "ADAUSDT.json")
    index = os.path.join(directory, "BTCUSDT_index.json")
    path_trade_history = "/Users/cjupit/Desktop/trade_history.json"
    # index = "/Users/nnn/GitHub/DataStore/BTCUSDT_index.json"

    # analysis_ins = Analysis.AnalysisManager()

    kline_data, index_data = update_data(kline_path=kline, index_path=index)

    data_obj = DataManager(kline_data=kline_data, index_data=index_data)
    signal_obj = SignalRecorder()
    stopper_obj = TradeStopper()
    wallet_obj = Wallet()
    analy_obj = Analysis.AnalysisManager()

    for i in range(len(index_data) - 1):
        get_data = data_obj.get_kline_data_by_range(end_index=i)
        # print('DEBUG 1=========')
        if not get_data.get("3d"):
            continue
        # print('DEBUG 2')

        # 데이터 분석 tool
        analy_data = analy_obj.case2_conditions(ticker_data=get_data)
        open_signal = signal(analy_data=analy_data)

        # utils._std_print(analy_data)
        # 1분봉 마지막 데이터 (최신데이터 대체적용)
        nested_kline_data = get_data.get("1m")[-1]
        current_price = float(nested_kline_data[4])  # 이상 무
        # 시나리오 true면

        trade_history = signal_obj.get_trade_history()
        if trade_history and trade_history[-1].get("tradeStatus"):
            wallet_obj.realtime_wallet_update(
                curreutn_price=nested_kline_data[4], trade_history=trade_history
            )

        if isinstance(open_signal, dict):
            trade_history = signal_obj.get_trade_history()
            if trade_history and trade_history[-1]["tradeStatus"]:
                continue
            position = open_signal.get("position")
            leverage = open_signal.get("leverage")

            quantity = (leverage * wallet_obj.available_value) / current_price
            signal_obj.submit_trade_open_signal(
                position=position,
                nested_kline_data=nested_kline_data,
                leverage=leverage,
                quantity=quantity,
            )
            wallet_obj.withdrawal(USDT=wallet_obj.available_value)
            # signal_obj.dump_to_json(file_path=path_trade_history)

        trade_history = signal_obj.get_trade_history()

        if trade_history:
            close_signal = stopper_obj.generate_close_signal_scenario1(
                nested_kline_data=nested_kline_data, trade_history=trade_history
            )
            # print(close_signal)
            if close_signal:
                signal_obj.submit_trade_close_signal(
                    nested_kline_data=nested_kline_data
                )
                last_trade_history = signal_obj.get_trade_history()[-1]

                leverage = last_trade_history.get("leverage")
                quantity = last_trade_history.get("quantity")

                selling_amt = (quantity * current_price) / leverage
                wallet_obj.deposit(selling_amt)
                # signal_obj.dump_to_json(file_path=path_trade_history)

        accout_balace = wallet_obj.get_account_balance()
        utils._std_print(accout_balace)
