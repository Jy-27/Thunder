import json
import pandas as pd

# JSON 파일에서 '5m' 데이터를 로드하고 전처리하는 함수
def load_and_preprocess_5m_data(file_path):
    """
    JSON 파일에서 '5m' 데이터를 로드하고 백테스트에 맞게 전처리합니다.
    
    :param file_path: JSON 파일 경로
    :return: 5분봉 데이터가 포함된 데이터프레임
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
        
    df = pd.DataFrame(data["5m"], columns=[
        "open_time", "open", "high", "low", "close", "volume", 
        "close_time", "quote_asset_volume", "num_trades", 
        "taker_buy_base_asset_volume", "taker_buy_quote_asset_volume", "ignore"
    ])
    
    # 데이터 타입을 float으로 변환
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["volume"] = df["volume"].astype(float)
    
    # 시간 인덱스로 설정
    df["open_time"] = pd.to_datetime(df["open_time"], unit='ms')
    df.set_index("open_time", inplace=True)
    
    # 시간 기준 정렬
    df.sort_index(inplace=True)
    
    return df

# 백테스트 함수: 3회 연속 상승 시 매수 진입 후 일정 보유 기간 후 청산
def backtest_long_strategy(df, hold_period=10):
    """
    3회 연속 상승 시 매수하고 보유 기간 후 청산하는 백테스트 전략.
    
    :param df: 5분봉 데이터프레임
    :param hold_period: 매수 후 보유할 캔들 수 (기본: 10)
    :return: 백테스트 결과 딕셔너리
    """
    initial_cash = 100000  # 초기 자금
    cash = initial_cash
    position = 0  # 보유 자산 수량
    trades = []  # 거래 내역 저장

    # 연속 상승 감지 열 추가
    df['is_up'] = df['close'] > df['close'].shift(1)
    df['up_streak'] = df['is_up'].rolling(window=3).apply(lambda x: x.all(), raw=True)

    for i in range(len(df) - hold_period):
        # 3회 연속 상승 시 매수 진입
        if df['up_streak'].iloc[i] == 1 and position == 0:
            buy_price = df['close'].iloc[i]
            position = cash / buy_price
            cash = 0
            trades.append({'type': 'buy', 'price': buy_price, 'time': df.index[i]})

            # 보유 기간 동안 포지션 청산
            sell_price = df['close'].iloc[i + hold_period]
            cash = position * sell_price
            position = 0
            trades.append({'type': 'sell', 'price': sell_price, 'time': df.index[i + hold_period]})

    # 최종 수익률 계산
    final_balance = cash if position == 0 else cash + position * df['close'].iloc[-1]
    profit = final_balance - initial_cash
    profit_pct = (profit / initial_cash) * 100

    results = {
        "initial_cash": initial_cash,
        "final_balance": final_balance,
        "profit": profit,
        "profit_pct": profit_pct,
        "trades": trades
    }
    
    return results

# 전체 실행
if __name__ == "__main__":
    # JSON 파일 경로 지정
    file_path = '/Users/nnn/Desktop/DataStore/KlineData/btcusdt.json'
    
    # 5분봉 데이터 로드 및 전처리
    df_5m = load_and_preprocess_5m_data(file_path)
    
    # 백테스트 실행
    results = backtest_long_strategy(df_5m, hold_period=10)

    # 백테스트 결과 출력
    print("Initial Cash:", results["initial_cash"])
    print("Final Balance:", results["final_balance"])
    print("Total Profit:", results["profit"])
    print("Total Profit (%):", results["profit_pct"])
    print("Trades:")
    for trade in results["trades"]:
        print(trade)
