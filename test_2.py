from BinanceBackTest import *
import asyncio
import nest_asyncio
import os
import utils
from pprint import pprint
import Analysis
import DataProcess
from collections import defaultdict
from datetime import datetime

nest_asyncio.apply()

print(f"작업시작 >> {datetime.now()}")

# symbols 지정
symbols = [
    "BTCUSDT",
    "XRPUSDT",
    "ADAUSDT",
    # "NOTUSDT",
    # "SANDUSDT",
    # "ARKMUSDT",
    # "SOLUSDT",
    "DOGEUSDT",
]
# interval 지정.
# intervals = ["1m", "5m", "1h"]
intervals = ["1m", "3m", "5m", "1h"]

# 적용할 데이터의 기간 지정.
start_date = "2024-11-1"
end_date = "2024-12-7"


print(f"instance 로딩 완료 >> {datetime.now()}")
obj_process = DataProcess.TradeStopper()
obj_analy = Analysis.AnalysisManager(back_test=True)
obj_analy.intervals = intervals
obj_order = OrderManager()
obj_con = DataProcess.OrderConstraint()
obj_data = DataManager(symbols=symbols,
                       intervals=intervals,
                       start_date=start_date,
                       end_date=end_date)

# path = os.path.join(os.path.dirname(os.getcwd()), 'DataStore/kline_data.json')
# data = utils._load_json(file_path=path)
kline_data = asyncio.run(obj_data.generate_kline_interval_data(save=True))

kline_data = utils._convert_to_array(kline_data=kline_data)
kline_data = obj_data.generate_kline_closing_sync(kline_data=kline_data, save=True)
symbol_map, interval_map, data_c = utils._convert_to_container(kline_data)
obj_data.get_indices_data(data_container=data_c, lookback_days=1)

obj_analysis = Analysis.AnalysisManager()



trade_data = []

#손익비용 저장할 변수
pnl_data = defaultdict(float)
pnl_count = defaultdict(int)

#초기 투자 자본
seed_money = 1000

# 가장 지갑 생성
obj_wallet = WalletManager(initial_fund=seed_money)

# 래핑 데이터를 이용하여 반복문 실행한다.
for idx, d in enumerate(data_c.get_data('map_1m')):
    for interval in intervals:
        maps_ = data_c.get_data(f'map_{interval}')[idx]
        # if interval == "5m":
        data = data_c.get_data(f'interval_{interval}')[maps_]
        obj_analysis.case_1_data_length(kline_data_lv3=data)
        obj_analysis.case_2_candle_length(kline_data_lv3=data)
        obj_analysis.case_3_continuous_trend_position(kline_data_lv3=data)
        obj_analysis.case_4_process_neg_counts(kline_data_lv3=data, col=7)
        obj_analysis.case_5_diff_neg_counts(kline_data_lv3=data, col1=1, col2=4)

        # 1분봉의 값 기준으로 현재가, timestamp가격을 반영한다.
        if interval == intervals[0]:
            price = data[-1][4]
            close_timestampe = data[-1][6]
            symbol = symbols[maps_[0]]
        utils._std_print(f'{idx} / {len(data_c.get_data('map_1m'))}')
    
    scenario_1 =obj_analysis.scenario_1()
    obj_analysis.reset_cases()
    
    if scenario_1[0]:
        
        # 주문 제약 사항 스펙
        constraint = obj_con.calc_fund(
            obj_wallet.balance_info["total_assets"], rate=0.2
        )
        
        position = scenario_1[1]
        
        trade_balance = constraint.get("tradeValue")
    

        # 최대 보유 가능 종목수량
        trade_count = constraint.get("count")
        # 회당 지정 거래가능 대금 지정

        #주문 신호 발생기
        status, order_signal_open = asyncio.run(
            obj_order.generate_order_open_signal(
                symbol=symbol,
                position=position,
                # position=reset_position,
                leverage=int(scenario_1[2] / 60),
                balance=trade_balance,
                entry_price=price,
                open_timestamp=close_timestampe,
            )
        )
        #주문 신호 발생시
        if (
            status
            and trade_count
            > obj_wallet.balance_info["locked_funds"]["number_of_stocks"]
        ):
            # 포지션 종료를 위한 초기값 업데이트
            obj_process.initialize_trading_data(
                symbol=symbol,
                position=order_signal_open["position"],
                entry_price=order_signal_open["entryPrice"],
            )
            # 지갑 정보 업데이트
            obj_wallet.add_funds(order_signal=order_signal_open)
            
            #DEBUG CODE
            print(obj_wallet.balance_info)
            
            trade_data.append(order_signal_open)
            trade_data.append(obj_wallet.balance_info)
        
    # 포지션 종료 검사.
    # 현재가
    # current_price = data[0][4]
    # wallet 보유현황
    is_wallet = obj_process.trading_data.get(symbol)
    # print(is_wallet)
    obj_wallet.get_wallet_status(symbol=symbol, current_price=price)
    
    
    
    # 만약 wallet에 해당 symbol이 없다면..손절 검사 실행
    if is_wallet is not None:
        # 매도 가격 도달 여부 (bool)
        is_stop = obj_process.get_trading_stop_signal(
            symbol=symbol, current_price=price
        )
        # 만약 매도 가격 도달시 (True)
        if is_stop and price >0:
            # 지갑 금액 정보 업데이트
            
            # 종료 신호 생성
            value = obj_order.generate_order_close_signal(
                symbol=symbol,
                current_price=price,
                wallet_data=obj_wallet.account_balances,
            )
            
            # wallet에 보유정보 삭제 및 손익비용 연산 반환.
            _, pnl_value = obj_wallet.remove_funds(symbol=symbol)
            # 매도 가격 도달시 종료하는 함수의 데이터 기록 제거.
            obj_process.remove_trading_data(symbol)
            # 계좌정보 별도 저장.
            trade_data.append(obj_wallet.account_balances.get(symbol))
            trade_data.append(obj_wallet.balance_info)

            # if pnl_value < 0:
                # pprint(obj_wallet.balance_info)
                
            if not pnl_data.get(symbol):
                pnl_data[symbol] = float(pnl_value)
                pnl_count[symbol] = 0
            else:
                pnl_data[symbol] += float(pnl_value)
                pnl_count[symbol] += 1
    # break
#실시간 변동이 보고싶다면 이곳에.
# utils._std_print(f'{i} / {range_length_data}')
# utils._std_print(round(obj_wallet.get_wallet_status(symbol=symbol, current_price=price)['total_assets'],3))

# utils._std_print(obj_wallet.balance_info['total_assets'])
print(f"분석 종료 {datetime.now()}")

print("\n")
print("==>> wallet info")
pprint(obj_wallet.balance_info)
utils._save_to_json(
    file_path=f"{os.path.dirname(os.getcwd())}/DataStore/balance_info.json",
    new_data=obj_wallet.balance_info,
)

print("\n")
print("==>> balance info")
pprint(obj_wallet.account_balances)
utils._save_to_json(
    file_path=f"{os.path.dirname(os.getcwd())}/DataStore/account_balances.json",
    new_data=obj_wallet.account_balances,
)

print("\n")
print("==>> PNL info")

for idx, data in enumerate(trade_data):
    print(f"No. {idx}")
    pprint(data)
utils._save_to_json(
    file_path=f"{os.path.dirname(os.getcwd())}/DataStore/trade_data.json",
    new_data=trade_data,
)