from typing import Tuple, List
from functools import lru_cache


class FunctionGroup:
    # KLINE DATA에서 OpenTimestamp, CloseTimestamp값을 추출 및 반환한다.
    def _get_timestamps(self, kline_data: List) -> Tuple[int, int]:
        """
        1. 기능 : KLINE DATA값에서 OpenTimestamp, CloseTimestamp값을 추출 및 반환한다.
        2. 매개변수
            1) kline_data (List): KLINE DATA의 최하위 List값
        3. 오류발생시
            1) ValueError
                - Params kline_data 타입이 List가 아닐때
                - Rarams Kline_data의 길이가 12개가 아닐때
                - index값 타입이 int가 아닐때
        4. 반환값 (Tuple)
            1) open_timestamp : OpenTimestamp (마이크로 타임스템프)

        Returns:
            Tuple[int, int]: _description_
        """
        if not isinstance(kline_data, list) or len(kline_data) != 12:
            raise ValueError(f"Params 타입 오류 - {type(kline_data)}")
        oepn_timestamp = kline_data[0]
        close_timestamp = kline_data[6]
        if not isinstance(oepn_timestamp, int) or not isinstance(close_timestamp, int):
            raise ValueError(f"kline data 오류")
        return (oepn_timestamp, close_timestamp)


# class main(FunctionGroup):


# @lru_cache
# def calculate_stop_loss(entry_price: float, target_price: float, start_margin_ratio: float = 0.015, profit_take_ratio: float = 0.6):
#     """
#     Stop-loss 가격을 계산하는 함수.

#     Parameters:
#     - entry_price (float): 진입 가격.
#     - target_price (float): 목표 가격.
#     - start_margin_ratio (float): 시작 마진 비율, 기본값 0.015 (1.5%).
#     - profit_take_ratio (float): 목표 이익에서 취할 비율, 기본값 0.6 (60%).

#     Returns:
#     - float: 계산된 손절 가격 (stop-loss price).
#     """
#     adjusted_entry_price = entry_price - (entry_price * start_margin_ratio)
#     profit_threshold = (target_price - adjusted_entry_price) * profit_take_ratio
#     stop_loss_price = adjusted_entry_price + profit_threshold
#     return stop_loss_price
