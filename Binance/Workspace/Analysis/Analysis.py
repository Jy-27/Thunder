### 초기설정

import asyncio
import numpy as np
from pprint import pprint
from typing import Dict, List, Final, Optional
from copy import copy


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
from Workspace.DataStorage.NodeStorage import SubStorage

class MA:
    """
    이동평균값을 계산하는 클래스
    """

    @staticmethod
    def sma(values: np.ndarray, period: int) -> np.ndarray:
        """
        단순 이동평균(SMA)을 계산하는 함수

        Args:
            data (np.ndarray): 가격 데이터 (OHLC 포함)
            period (int): 이동평균 기간

        Returns:
            np.ndarray: SMA 값 (길이 유지)
        """
        sma_values = np.convolve(prices, np.ones(period) / values, mode="valid")
        
        # 원래 길이를 유지하도록 NaN 추가
        return np.concatenate((np.full(period - 1, np.nan), sma_values))

    @staticmethod
    def ema(values: np.ndarray, period: int) -> np.ndarray:
        """
        지수 이동평균(EMA)을 계산하는 함수

        Args:
            data (np.ndarray): 가격 데이터 (OHLC 포함)
            period (int): 이동평균 기간

        Returns:
            np.ndarray: EMA 값 (길이 유지)
        """
        ema = np.full_like(values, np.nan, dtype=float)  # 초기 NaN 값 설정
        multiplier = 2 / (period + 1)

        # 첫 번째 EMA 값을 SMA로 설정
        ema[period - 1] = np.mean(prices[:period])

        # EMA 계산
        for i in range(period, len(prices)):
            ema[i] = (prices[i] - ema[i - 1]) * multiplier + ema[i - 1]

        return ema

    @staticmethod
    def wma(values: np.ndarray, period: int) -> np.ndarray:
        """
        가중 이동평균(WMA)을 계산하는 함수

        Args:
            data (np.ndarray): 가격 데이터 (OHLC 포함)
            period (int): 이동평균 기간

        Returns:
            np.ndarray: WMA 값 (길이 유지)
        """
        weights = np.arange(1, period + 1)
        wma_values = np.convolve(values, weights / weights.sum(), mode="valid")

        # 원래 길이를 유지하도록 NaN 추가
        return np.concatenate((np.full(period - 1, np.nan), wma_values))

class MACD:
    """
    MACD 지표를 계산하는 클래스 (EMA를 비공개 메서드로 변경)
    """

    @staticmethod
    def __ema(values: np.ndarray, window: int) -> np.ndarray:
        """(비공개) EMA 계산 함수 - MACD 내부에서만 사용"""
        if len(values) < window:
            return np.full_like(values, np.nan, dtype=np.float64)  # 데이터 부족 시 NaN 반환

        alpha = 2 / (window + 1)
        ema_values = np.full_like(values, np.nan, dtype=np.float64)  # NaN으로 초기화
        ema_values[window - 1] = np.nanmean(values[:window])  # 첫 EMA는 SMA로 초기화

        for i in range(window, len(values)):
            ema_values[i] = alpha * values[i] + (1 - alpha) * ema_values[i - 1]

        return ema_values

    @staticmethod
    def line(values: np.ndarray, short_window: int = 12, long_window: int = 26) -> np.ndarray:
        """MACD Line 계산"""
        short_ema = MACD.__ema(values, short_window)
        long_ema = MACD.__ema(values, long_window)
        return short_ema - long_ema

    @staticmethod
    def signal_line(values: np.ndarray, short_window: int = 12, long_window: int = 26, signal_window: int = 9) -> np.ndarray:
        """Signal Line 계산"""
        macd_line = MACD.line(values, short_window, long_window)
        
        # 데이터 길이 확인 후 NaN 방지
        if np.isnan(macd_line).all():
            return np.full_like(macd_line, np.nan)

        valid_macd = macd_line[~np.isnan(macd_line)]  # NaN이 아닌 값만 필터링
        signal = MACD.__ema(valid_macd, signal_window)

        # 결과값 길이 맞추기
        result = np.full_like(macd_line, np.nan)
        result[-len(signal):] = signal  # 뒤쪽에 채우기

        return result

    @staticmethod
    def histogram(values: np.ndarray, short_window: int = 12, long_window: int = 26, signal_window: int = 9) -> np.ndarray:
        """MACD Histogram 계산"""
        macd_line = MACD.line(values, short_window, long_window)
        signal_line = MACD.signal_line(values, short_window, long_window, signal_window)
        return macd_line - signal_line

class RSI:
    """ 
    다양한 형태의 RSI(Relative Strength Index) 계산 클래스 
    - 기본 RSI (Wilder 방식)
    - 스토캐스틱 RSI
    - 다이버전스 RSI
    - Cutler's RSI (SMA 기반)
    - EMA 적용 부드러운 RSI
    - RSI 밴드
    """

    @staticmethod
    def wilder(values: np.ndarray, window: int = 14) -> np.ndarray:
        """
        📌 기본 RSI (Wilder 방식)
        - RSI는 가격의 상승 및 하락 강도를 비교하는 지표.
        - Wilder 방식의 지수 이동평균(EMA)을 사용하여 RSI를 계산.
        
        ✅ 공식:
            1. 가격 변화량(Δ) 계산: delta = 현재 가격 - 이전 가격
            2. 상승(gain)과 하락(loss) 분리
            3. 평균 상승(AVG_Gain) 및 평균 하락(AVG_Loss) 계산 (Wilder 방식 적용)
            4. 상대 강도(Relative Strength, RS) 계산: RS = AVG_Gain / AVG_Loss
            5. RSI 계산: RSI = 100 - (100 / (1 + RS))
        """
        if len(values) < window:
            return np.full_like(values, np.nan, dtype=np.float64)

        # 가격 변화량 계산
        delta = np.diff(values, prepend=values[0])

        # 상승(gain)과 하락(loss) 분리
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        # 초기 평균 상승 및 하락 값 계산 (첫 window 구간은 단순 평균 사용)
        avg_gain = np.full_like(values, np.nan, dtype=np.float64)
        avg_loss = np.full_like(values, np.nan, dtype=np.float64)
        avg_gain[window - 1] = np.mean(gain[:window])
        avg_loss[window - 1] = np.mean(loss[:window])

        # Wilder 방식의 지수 이동평균(EMA) 적용
        for i in range(window, len(values)):
            avg_gain[i] = (avg_gain[i - 1] * (window - 1) + gain[i]) / window
            avg_loss[i] = (avg_loss[i - 1] * (window - 1) + loss[i]) / window

        # 상대 강도(Relative Strength) 및 RSI 계산
        rs = np.where(avg_loss == 0, 0, avg_gain / avg_loss)
        rsi = 100 - (100 / (1 + rs))

        return rsi

    @staticmethod
    def stochastic(values: np.ndarray, window: int = 14) -> np.ndarray:
        """
        📌 스토캐스틱 RSI
        - RSI 값을 스토캐스틱 방식으로 변환하여 과매수/과매도 신호를 더욱 강조.

        ✅ 공식:
            Stoch RSI = (RSI - 최소 RSI) / (최대 RSI - 최소 RSI)

        ✅ 오류 방지 개선 사항:
            1. `rsi` 값이 NaN이면 `np.nan_to_num()`을 사용하여 안전한 기본값 설정.
            2. `np.nanmin()`과 `np.nanmax()`에서 NaN 값이 모두 포함될 경우 기본값(`rsi[i]`) 사용.
            3. `max_rsi - min_rsi == 0`인 경우 `1`로 설정하여 나눗셈 오류 방지.
        """
        rsi = RSI.wilder(values, window)
        rsi = np.nan_to_num(rsi, nan=50.0)  # NaN 값을 기본값 50으로 대체 (중립적인 값)

        # 최솟값 및 최댓값 계산 (NaN 방지 코드 포함)
        min_rsi = np.full_like(rsi, np.nan)
        max_rsi = np.full_like(rsi, np.nan)

        for i in range(len(rsi)):
            valid_rsi = rsi[max(0, i - window + 1):i + 1]
            valid_rsi = valid_rsi[~np.isnan(valid_rsi)]  # NaN 제거

            if len(valid_rsi) > 0:
                min_rsi[i] = np.nanmin(valid_rsi)
                max_rsi[i] = np.nanmax(valid_rsi)
            else:
                min_rsi[i] = rsi[i]  # NaN 방지: 현재 RSI 값 사용
                max_rsi[i] = rsi[i]

        # ⚠️ 나눗셈 오류 방지 (max_rsi - min_rsi == 0인 경우 1로 처리)
        range_rsi = np.where((max_rsi - min_rsi) == 0, 1, max_rsi - min_rsi)

        return (rsi - min_rsi) / range_rsi

    @staticmethod
    def divergence(values: np.ndarray, window: int = 14) -> np.ndarray:
        """
        📌 다이버전스 감지
        - 가격과 RSI 간의 불일치를 감지하여 추세 반전을 예측하는 기법.
        
        ✅ 특징:
            - 강세 다이버전스: 가격 하락 & RSI 상승 (매수 신호)
            - 약세 다이버전스: 가격 상승 & RSI 하락 (매도 신호)
        """
        rsi = RSI.wilder(values, window)
        return np.where(np.diff(values, prepend=values[0]) > 0, -1, 1)

    @staticmethod
    def cutlers(values: np.ndarray, window: int = 14) -> np.ndarray:
        """
        📌 Cutler’s RSI (SMA 기반)
        - 기존 RSI는 EMA 기반이지만, Cutler’s RSI는 단순 이동평균(SMA)을 사용.
        
        ✅ 공식:
            Cutler's RSI = 100 - (100 / (1 + RS))
            RS = SMA(Avg Gain) / SMA(Avg Loss)
        """
        delta = np.diff(values, prepend=values[0])
        gain = np.where(delta > 0, delta, 0)
        loss = np.where(delta < 0, -delta, 0)

        avg_gain = np.convolve(gain, np.ones(window)/window, mode='valid')
        avg_loss = np.convolve(loss, np.ones(window)/window, mode='valid')

        rs = np.where(avg_loss == 0, 0, avg_gain / avg_loss)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def ema_smooth(values: np.ndarray, window: int = 14, smoothing: int = 3) -> np.ndarray:
        """
        📌 EMA 적용 부드러운 RSI
        - 기본 RSI의 변동성을 줄이기 위해 추가적인 EMA를 적용하여 부드러운 RSI 생성.
        
        ✅ 공식:
            EMA_RSI = α * RSI + (1 - α) * EMA_RSI_이전값
            α = 2 / (smoothing + 1)
        """
        rsi = RSI.wilder(values, window)
        ema_rsi = np.full_like(rsi, np.nan)
        
        alpha = 2 / (smoothing + 1)
        ema_rsi[window - 1] = rsi[window - 1]

        for i in range(window, len(rsi)):
            ema_rsi[i] = alpha * rsi[i] + (1 - alpha) * ema_rsi[i - 1]

        return ema_rsi

    @staticmethod
    def bands(values: np.ndarray, window: int = 14, std_factor: float = 1.5) -> tuple:
        """
        📌 RSI 밴드 (볼린저 밴드와 유사)
        - RSI 변동성을 반영한 상한 및 하한 밴드를 생성하여 신뢰도 높은 매매 신호를 제공.
        
        ✅ 공식:
            상한 밴드 = RSI + (RSI 표준편차 * std_factor)
            하한 밴드 = RSI - (RSI 표준편차 * std_factor)
        """
        rsi = RSI.wilder(values, window)

        # ⚠️ NaN 데이터 및 데이터 부족 문제 방지
        rsi_std = np.full_like(rsi, np.nan)

        for i in range(len(rsi)):
            valid_data = rsi[max(0, i - window + 1):i + 1]
            valid_data = valid_data[~np.isnan(valid_data)]  # NaN 값 제거
            
            if len(valid_data) > 1:  # 표준편차를 계산할 충분한 데이터가 있는 경우
                rsi_std[i] = np.nanstd(valid_data, ddof=0)  # 자유도 0 설정
            else:
                rsi_std[i] = 0  # 데이터가 부족하면 표준편차를 0으로 설정

        # 상한 및 하한 밴드 계산
        upper_band = rsi + (rsi_std * std_factor)
        lower_band = rsi - (rsi_std * std_factor)

        return rsi, upper_band, lower_band

class BollingerBands:
    """
    📌 볼린저 밴드 및 변형된 지표 모음
    - 기본 볼린저 밴드 (Standard Bollinger Bands)
    - 볼린저 밴드 %B (%B Indicator)
    - 볼린저 밴드 너비 (BBW, Bollinger Band Width)
    - 확장형 볼린저 밴드 (Wide Bollinger Bands)
    - 축소형 볼린저 밴드 (Narrow Bollinger Bands)
    - 볼린저 밴드 스퀴즈 (Bollinger Squeeze)
    - Keltner Channel (켈트너 채널)
    - Donchian Channel (돈치안 채널)
    """

    @staticmethod
    def standard(values: np.ndarray, window: int = 20, std_factor: float = 2) -> tuple:
        """
        📌 기본 볼린저 밴드 (Standard Bollinger Bands)
        - 중심선(SMA), 상한선(Upper Band), 하한선(Lower Band) 계산

        ✅ 공식:
            중심선 = SMA(단순 이동평균)
            상한선 = SMA + (표준편차 × std_factor)
            하한선 = SMA - (표준편차 × std_factor)
        """
        if len(values) < window:
            return np.full(len(values), np.nan), np.full(len(values), np.nan), np.full(len(values), np.nan)

        sma = np.convolve(values, np.ones(window) / window, mode="valid")
        std_dev = np.array([np.nanstd(values[max(0, i - window + 1):i + 1]) for i in range(len(values))])

        upper_band = sma + (std_factor * std_dev)
        lower_band = sma - (std_factor * std_dev)

        return np.concatenate((np.full(window - 1, np.nan), sma)), upper_band, lower_band

    @staticmethod
    def percent_b(values: np.ndarray, window: int = 20) -> np.ndarray:
        """
        📌 볼린저 밴드 %B (%B Indicator)
        - 가격이 볼린저 밴드 내에서 어디에 위치하는지 계산

        ✅ 공식:
            %B = (현재 가격 - 하한선) / (상한선 - 하한선)
        """
        sma, upper_band, lower_band = BollingerBands.standard(values, window)
        percent_b = (values - lower_band) / (upper_band - lower_band)
        return percent_b

    @staticmethod
    def bandwidth(values: np.ndarray, window: int = 20) -> np.ndarray:
        """
        📌 볼린저 밴드 너비 (BBW, Bollinger Band Width)
        - 볼린저 밴드의 폭을 측정하여 변동성 분석

        ✅ 공식:
            BBW = (상한선 - 하한선) / 중심선
        """
        sma, upper_band, lower_band = BollingerBands.standard(values, window)
        bbw = (upper_band - lower_band) / sma
        return bbw

    @staticmethod
    def wide(values: np.ndarray, window: int = 20, std_factor: float = 3) -> tuple:
        """
        📌 확장형 볼린저 밴드 (Wide Bollinger Bands)
        - 표준편차 값을 더 크게 설정하여 넓은 밴드를 형성
        """
        return BollingerBands.standard(values, window, std_factor)

    @staticmethod
    def narrow(values: np.ndarray, window: int = 20, std_factor: float = 1) -> tuple:
        """
        📌 축소형 볼린저 밴드 (Narrow Bollinger Bands)
        - 표준편차 값을 더 작게 설정하여 좁은 밴드를 형성
        """
        return BollingerBands.standard(values, window, std_factor)

    @staticmethod
    def squeeze(values: np.ndarray, window: int = 20, threshold: float = 0.05) -> np.ndarray:
        """
        📌 볼린저 밴드 스퀴즈 (Bollinger Squeeze)
        - BBW(볼린저 밴드 너비)가 특정 임계값 이하로 떨어질 때 신호 발생

        ✅ 활용:
            - BBW가 특정 값 이하일 경우, 추후 변동성 폭발 가능성
        """
        bbw = BollingerBands.bandwidth(values, window)
        squeeze_signal = bbw < threshold  # BBW가 특정 값 이하이면 True 반환
        return squeeze_signal.astype(float)  # 1(스퀴즈 발생) 또는 0(스퀴즈 없음) 반환

    @staticmethod
    def keltner_channel(values: np.ndarray, window: int = 20, atr_factor: float = 2) -> tuple:
        """
        📌 Keltner Channel (켈트너 채널)
        - 볼린저 밴드와 유사하지만, 표준편차 대신 ATR(Average True Range)을 사용하여 변동성을 측정

        ✅ 공식:
            중심선 = EMA(지수 이동평균)
            상한선 = 중심선 + (ATR × atr_factor)
            하한선 = 중심선 - (ATR × atr_factor)
        """
        if len(values) < window:
            return np.full(len(values), np.nan), np.full(len(values), np.nan), np.full(len(values), np.nan)

        ema = np.convolve(values, np.ones(window) / window, mode="valid")
        atr = np.array([np.nanstd(values[max(0, i - window + 1):i + 1]) for i in range(len(values))])

        upper_band = ema + (atr_factor * atr)
        lower_band = ema - (atr_factor * atr)

        return np.concatenate((np.full(window - 1, np.nan), ema)), upper_band, lower_band

    @staticmethod
    def donchian_channel(values: np.ndarray, window: int = 20) -> tuple:
        """
        📌 Donchian Channel (돈치안 채널)
        - 최근 N일 동안의 최고가와 최저가를 기반으로 채널을 형성

        ✅ 공식:
            상한선 = 최근 N일 동안의 최고가
            하한선 = 최근 N일 동안의 최저가
        """
        if len(values) < window:
            return np.full(len(values), np.nan), np.full(len(values), np.nan)

        upper_band = np.array([np.nanmax(values[max(0, i - window + 1):i + 1]) for i in range(len(values))])
        lower_band = np.array([np.nanmin(values[max(0, i - window + 1):i + 1]) for i in range(len(values))])

        return upper_band, lower_band
