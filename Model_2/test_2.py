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
    "SANDUSDT",
    "ARKMUSDT",
    # "SOLUSDT",
    "DOGEUSDT",
]
# interval 지정.
# intervals = ["1m", "5m", "1h"]
intervals = ["1m", "3m", "5m", "1h"]

# 적용할 데이터의 기간 지정.
start_date = "2024-11-1"
end_date = "2024-11-28"


print(f"instance 로딩 완료 >> {datetime.now()}")
obj_process = DataProcess.TradeStopper(profit_ratio=0.02, risk_ratio=0.65)
obj_analy = Analysis.AnalysisManager(back_test=True)
obj_analy.intervals = intervals
obj_order = ProcessManager()
obj_con = DataProcess.OrderConstraint()
obj_data = DataManager(
    symbols=symbols, intervals=intervals, start_date=start_date, end_date=end_date
)

# k_path = os.path.join(os.path.dirname(os.getcwd()), "DataStore/closing_sync_data.pkl")
# with open(k_path, "rb") as file:
#     kline_data = pickle.load(file)
# kline_data = utils._load_json(file_path=k_path)
kline_data = asyncio.run(obj_data.generate_kline_interval_data(save=True))


kline_data = utils._convert_to_array(kline_data=kline_data)
kline_data = obj_data.generate_kline_closing_sync(kline_data=kline_data, save=True)

# kline_data = utils._load_json(file_path=)

symbol_map, interval_map, data_c = utils._convert_to_container(kline_data)
obj_data.get_indices_data(data_container=data_c, lookback_days=1)

obj_analysis = Analysis.AnalysisManager()


trade_data = []

# 초기 투자 자본
seed_money = 69492.7
# 가장 지갑 생성
obj_wallet = TradeOrderManager(initial_balance=seed_money)

# 래핑 데이터를 이용하여 반복문 실행한다.
for idx, d in enumerate(data_c.get_data("map_1m")):
    if idx < 10_000:
        continue
    for interval in intervals:
        maps_ = data_c.get_data(f"map_{interval}")[idx]
        # if interval == "5m":
        data = data_c.get_data(f"interval_{interval}")[maps_]
        obj_analysis.case_1_data_length(kline_data_lv3=data)
        obj_analysis.case_2_candle_length(kline_data_lv3=data)
        obj_analysis.case_3_continuous_trend_position(kline_data_lv3=data)
        # obj_analysis.case_4_process_neg_counts(kline_data_lv3=data, col=7)
        # obj_analysis.case_5_diff_neg_counts(kline_data_lv3=data, col1=1, col2=4)
        # obj_analysis.case_6_ocillator_volume(kline_data_lv3=data)#, col1=1, col2=4)
        obj_analysis.case_7_ocillator_value(kline_data_lv3=data)#, col1=1, col2=4)
        obj_analysis.case_8_sorted_indices(kline_data_lv3=data, col=4)
        # obj_analysis.case_9_rsi(kline_data_lv3=data, col=4)

        # 1분봉의 값 기준으로 현재가, timestamp가격을 반영한다.
    
        if interval == intervals[0]:
            price = data[-1][4]
            close_timestampe = data[-1][6]
            symbol = symbols[maps_[0]]
            obj_wallet.update_order_data(
                symbol=symbol, current_price=price, current_time=close_timestampe
            )
        utils._std_print(f"{idx:,.0f} / {obj_wallet.trade_analysis.profit_loss:,.2f}")

    scenario_1 = obj_analysis.scenario_2()
    obj_analysis.reset_cases()

    if scenario_1[0]:
        # print(True)
        # 주문 제약 사항 스펙
        constraint = obj_con.calc_fund(
            obj_wallet.trade_analysis.total_balance, rate=0.2, count_max=4
        )

        position = scenario_1[1]

        trade_balance = constraint.get("tradeValue")

        # 최대 보유 가능 종목수량
        trade_count = constraint.get("count")
        # 회당 지정 거래가능 대금 지정

        # 주문 신호 발생기
        status, qty, lv = asyncio.run(
            obj_order.calculate_order_values(
                symbol=symbol,
                leverage=10,
                balance=trade_balance,
                market_type="futures",
            )
        )
        
        # 주문 마진금액이 예수금보다 커야함.
        margin_ = (qty / lv) * price
        # 마진이 예수금을 초과여부 검사
        is_cash_margin = obj_wallet.trade_analysis.cash_balance > margin_
        # 최대 보유 항목 초과여부 검사
        is_trade_count = obj_wallet.trade_analysis.number_of_stocks < trade_count
        
        # 주문 신호 발생시
        if status and is_cash_margin and is_trade_count:
            # 포지션 종료를 위한 초기값 업데이트
            obj_process.initialize_trading_data(
                symbol=symbol,
                position="LONG" if position == 1 else "SHORT",
                entry_price=price,
            )
                
            # 지갑 정보 업데이트
            obj_wallet.add_order(
                symbol=symbol,
                start_timestamp=close_timestampe,
                entry_price=price,
                position=position,
                quantity=qty,
                leverage=lv,
            )

    # 포지션 종료 검사.
    # 현재가
    # current_price = data[0][4]
    # wallet 보유현황
    is_wallet = obj_process.trading_data.get(symbol)
    # print(is_wallet)

    # 만약 wallet에 해당 symbol이 없다면..손절 검사 실행
    if is_wallet is not None:
        # 매도 가격 도달 여부 (bool)
        is_stop = obj_process.get_trading_stop_signal(
            symbol=symbol, current_price=price
        )
        # 만약 매도 가격 도달시 (True)
        if is_stop and price > 0:
            # 지갑 금액 정보 업데이트

            # wallet에 보유정보 삭제 및 손익비용 연산 반환.
            obj_wallet.remove_order(symbol=symbol)
            # 매도 가격 도달시 종료하는 함수의 데이터 기록 제거.
            obj_process.remove_trading_data(symbol)

analyzer = ResultEvaluator(data=obj_wallet.trade_analysis)
analyzer.run_analysis()
