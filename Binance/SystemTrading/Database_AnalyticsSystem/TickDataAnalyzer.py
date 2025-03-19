import numpy as np
from typing import Dict

class TickDataAnalyzer:
    """틱 데이터를 기반으로 다양한 지표를 계산하는 클래스."""

    @staticmethod
    def tick_volatility(values:np.ndarray):
        """틱 변동성 (표준편차 기반) 계산"""
        return np.std(np.diff(values))

    @staticmethod
    def average_tick_change(values:np.ndarray):
        """각 틱의 가격 변화 평균 계산"""
        return np.mean(np.abs(np.diff(values)))

    @staticmethod
    def tick_spread(values:np.ndarray):
        """틱 가격의 스프레드 계산 (틱 최대값 - 틱 최소값)"""
        return max(values) - min(values)

    @staticmethod
    def tick_frequency(timestamps:np.ndarray):
        """틱당 체결 빈도 (초당 틱 발생횟수) 계산"""
        time_diff_sec = (timestamps[-1] - timestamps[0]) / 1000  # ms → sec 변환
        return len(timestamps) / time_diff_sec  # 초당 틱 발생 횟수 (TPS)

    @staticmethod
    def tick_direction_index(values:np.ndarray):
        """틱 방향 지수 (상승 틱 vs 하락 틱 비율) 계산"""
        up_ticks = np.sum(np.diff(values) > 0)
        down_ticks = np.sum(np.diff(values) < 0)
        return (up_ticks - down_ticks) / len(values)

    @staticmethod
    def tick_momentum(values:np.ndarray):
        """틱 모멘텀 (틱 가격 변화의 누적합) 계산"""
        return np.sum(np.diff(values))

    @staticmethod
    def trade_pressure(websocket_trade_message:Dict):
        """매수/매도 압력 계산"""
        score = {"buy":0, "sell":0}
        for message in websocket_trade_message:
            data = message["data"]
            value = float(data["p"]) * float(data["q"])
            if data["m"]:
                score["sell"] += value
            else:
                score["buy"] += value
        return score["buy"] / score["sell"]

    @staticmethod
    def tick_interval(timestamps):
        """평균 틱 간격 계산"""
        return np.mean(np.diff(timestamps))

