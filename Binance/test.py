import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
import requests
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler

def fetch_binance_klinedata(symbol='BTCUSDT', interval='1h', limit=100):
    url = f'https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}'
    response = requests.get(url)
    data = response.json()
    data = np.array([[float(candle[1]), float(candle[2]), float(candle[3]), float(candle[4]), float(candle[5])] for candle in data])
    return data

def create_sequences(data, seq_length=10, future_target=10):
    sequences, labels = [], []
    for i in range(len(data) - seq_length - future_target):
        sequences.append(data[i:i+seq_length])
        labels.append(data[i+seq_length+future_target-1, 3])  # 예측값: 미래 close price
    return np.array(sequences), np.array(labels)

# 데이터 수집
data = fetch_binance_klinedata()
prices = data[:, 3].reshape(-1, 1)  # close price

# 데이터 정규화
scaler = MinMaxScaler()
prices_scaled = scaler.fit_transform(prices)

# 학습 데이터 생성
seq_length = 10
future_target = 10
X, y = create_sequences(prices_scaled, seq_length, future_target)

# 데이터셋 분할
split = int(len(X) * 0.8)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# LSTM 모델 구축
model = Sequential([
    LSTM(64, return_sequences=True, input_shape=(seq_length, 1)),
    Dropout(0.2),
    LSTM(64, return_sequences=False),
    Dropout(0.2),
    Dense(32),
    Dense(1)
])

# 모델 컴파일 및 학습
model.compile(optimizer='adam', loss='mean_squared_error')
model.fit(X_train, y_train, epochs=20, batch_size=16, validation_data=(X_test, y_test))

# 예측 수행
y_pred = model.predict(X_test)
y_pred_rescaled = scaler.inverse_transform(y_pred.reshape(-1, 1))
y_test_rescaled = scaler.inverse_transform(y_test.reshape(-1, 1))

# 수익률 계산 함수
def calculate_pnl(actual_prices, predicted_prices, stop_loss=0.015, take_profit=0.015):
    capital = 100  # 초기 자본 (예제)
    position = 0  # 현재 포지션 (1: long, -1: short, 0: 없음)
    profit = 0

    for i in range(len(actual_prices) - 1):
        actual = actual_prices[i]
        predicted = predicted_prices[i]
        next_actual = actual_prices[i + 1]

        if predicted > actual:  # 롱 포지션 진입
            entry_price = actual
            stop_price = entry_price * (1 - stop_loss)
            take_price = entry_price * (1 + take_profit)
            
            if next_actual >= take_price:  # 익절
                profit += take_profit * capital
            elif next_actual <= stop_price:  # 손절
                profit -= stop_loss * capital

        elif predicted < actual:  # 숏 포지션 진입
            entry_price = actual
            stop_price = entry_price * (1 + stop_loss)
            take_price = entry_price * (1 - take_profit)
            
            if next_actual <= take_price:  # 익절
                profit += take_profit * capital
            elif next_actual >= stop_price:  # 손절
                profit -= stop_loss * capital
    
    return profit

# 수익률 계산
pnl = calculate_pnl(y_test_rescaled.flatten(), y_pred_rescaled.flatten())
print(f"총 수익률: {pnl:.2f}%")

# 결과 시각화
start_index = seq_length + future_target  # 예측값을 앞으로 이동
plt.plot(range(len(y_test_rescaled)), y_test_rescaled, label='Actual Price')
plt.plot(range(start_index, start_index + len(y_pred_rescaled)), y_pred_rescaled, label='Predicted Price', linestyle='dashed')
plt.legend()
plt.show()
