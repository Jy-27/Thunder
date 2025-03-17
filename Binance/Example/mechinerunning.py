import asyncio
import pandas as pd
import nest_asyncio
import json
import numpy as np
import matplotlib.pyplot as plt
from ccxt.pro import binance
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout

nest_asyncio.apply()

class BinanceDataCollector:
    """ 바이낸스 Depth(Orderbook), Trade, Kline 데이터를 실시간으로 수집하는 클래스 """
    def __init__(self, symbol="BTC/USDT", timeframe="1m"):
        self.exchange = binance()
        self.symbol = symbol
        self.timeframe = timeframe
        self.depth_data = pd.DataFrame()
        self.trade_data = pd.DataFrame()
        self.ohlcv_data = pd.DataFrame()

    async def fetch_depth(self):
        """ Orderbook 데이터를 수신하여 저장 """
        while True:
            orderbook = await self.exchange.watch_order_book(self.symbol)
            bids = orderbook['bids'][:5]  # 상위 5개 매수 호가
            asks = orderbook['asks'][:5]  # 상위 5개 매도 호가
            spread = asks[0][0] - bids[0][0]
            df = pd.DataFrame([{
                "timestamp": pd.Timestamp.now(),
                "bid1": bids[0][0], "ask1": asks[0][0],
                "spread": spread
            }])
            self.depth_data = pd.concat([self.depth_data, df]).tail(1000)
            await asyncio.sleep(0.1)  # 100ms 마다 갱신

    async def fetch_trade(self):
        """ Trade 데이터를 수신하여 저장 """
        while True:
            trades = await self.exchange.watch_trades(self.symbol)
            df = pd.DataFrame([{
                "timestamp": pd.Timestamp.now(),
                "price": trade["price"],
                "amount": trade["amount"]
            } for trade in trades])
            self.trade_data = pd.concat([self.trade_data, df]).tail(1000)
            await asyncio.sleep(0.1)

    async def fetch_kline(self):
        """ Kline 데이터를 수신하여 저장 """
        while True:
            ohlcv = await self.exchange.watch_ohlcv(self.symbol, self.timeframe)
            df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            self.ohlcv_data = df.tail(1000)
            await asyncio.sleep(1)

    async def run(self):
        """ 비동기 데이터 수집 실행 """
        await asyncio.gather(
            self.fetch_depth(),
            self.fetch_trade(),
            self.fetch_kline()
        )

# 데이터 수집 시작
collector = BinanceDataCollector()
asyncio.run(collector.run())

# 데이터 저장 (테스트용)
collector.ohlcv_data.to_csv("ohlcv_data.csv", index=False)
collector.depth_data.to_csv("depth_data.csv", index=False)
collector.trade_data.to_csv("trade_data.csv", index=False)

# 데이터 로드
ohlcv_data = pd.read_csv("ohlcv_data.csv")
depth_data = pd.read_csv("depth_data.csv")
trade_data = pd.read_csv("trade_data.csv")

# 데이터 정규화
scaler = MinMaxScaler()
ohlcv_data[["open", "high", "low", "close", "volume"]] = scaler.fit_transform(
    ohlcv_data[["open", "high", "low", "close", "volume"]]
)
depth_data[["spread"]] = scaler.fit_transform(depth_data[["spread"]])
trade_data["price_mean"] = trade_data["price"].rolling(window=10).mean()
trade_data["amount_mean"] = trade_data["amount"].rolling(window=10).mean()

# LSTM 입력 데이터 생성
def create_sequences(data, seq_length=60):
    sequences, labels = [], []
    for i in range(len(data) - seq_length):
        sequences.append(data[i:i + seq_length])
        labels.append(data[i + seq_length, 3])  # 종가(close) 예측
    return np.array(sequences), np.array(labels)

seq_length = 60
data_values = ohlcv_data[["open", "high", "low", "close", "volume"]].values
X, y = create_sequences(data_values, seq_length)

# LSTM 모델 생성
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(seq_length, 5)),
    Dropout(0.2),
    LSTM(50),
    Dropout(0.2),
    Dense(1)
])

model.compile(optimizer="adam", loss="mse")

# 모델 학습
model.fit(X, y, epochs=10, batch_size=32)

# 예측 수행
predictions = model.predict(X)

# 예측 결과 시각화
plt.figure(figsize=(10, 5))
plt.plot(y, label="Actual Price")
plt.plot(predictions, label="Predicted Price", linestyle="dashed")
plt.legend()
plt.show()
