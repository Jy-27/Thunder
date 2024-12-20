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
    "NOTUSDT",
    "SANDUSDT",
    "ARKMUSDT",
    "SOLUSDT",
    "DOGEUSDT",
]
# interval 지정.
# intervals = ["1m", "5m", "1h"]
intervals = ["1m", "3m", "5m", "1h"]

# 적용할 데이터의 기간 지정.
start_date = "2024-11-20 00:00:00"
end_date = "2024-11-29 23:59:59"

print(f"instance 로딩 완료 >> {datetime.now()}")
obj_process = DataProcess.TradeStopper()
obj_analy = Analysis.AnalysisManager(back_test=True)
obj_analy.intervals = intervals
obj_order = OrderManager()
obj_con = DataProcess.OrderConstraint()
obj_data = DataManager(
    symbols=symbols, intervals=intervals, start_date=start_date, end_date=end_date
)

print(f"데이터 다운로드 시작 >> {datetime.now()}")
range_length_data, kline_data, indices_data, closing_sync_data = asyncio.run(
    obj_data.read_data_run(download_if_missing=True)
)  # (download_if_missing=get_futures_kilne_datarue))
print(f"데이터 다운로드(로딩) 완료 >> {datetime.now()}")

kline_data = obj_data.convert_kline_data_array(kline_data=kline_data)


trade_data = []

# 손익비용 저장할 변수
pnl_data = defaultdict(float)
pnl_count = defaultdict(int)

# 초기 투자 자본
seed_money = 1000

# 가장 지갑 생성
obj_wallet = WalletManager(initial_fund=seed_money)

n = 0
# 데이터 간격 지정.
minutes = 288

print(f"분석 시작 {datetime.now()}")
for i in range(10, range_length_data, 1):
    # 해당 index값을 closing_sync_data index값으로 업데이트
    kline_data = obj_data.sync_kline_data(
        idx=i,
        kline_data=kline_data,
        idx_mapping=indices_data,
        sync_data=closing_sync_data,
    )
    # 필요한 범위만 추출해서 반환.
    target_data = obj_data.get_kline_interval_data_by_range(
        end_idx=i, kline_data=kline_data, idx_data=indices_data
    )
    for symbol in symbols:

        # 시나리오 1 검사.
        case_1 = obj_analy.scenario_1(symbol=symbol, convert_data=target_data)
        # 주문 제약 사항 스펙
        constraint = obj_con.calc_fund(
            obj_wallet.balance_info["total_assets"], rate=0.2
        )

        # 최대 보유 가능 종목수량
        trade_count = constraint.get("count")
        # 회당 지정 거래가능 대금 지정
        trade_balance = constraint.get("tradeValue")

        if (
            case_1[1] > 0
            and case_1[2] > 2
            and case_1[3] > 1
            # and case_1[4]
            and not obj_wallet.account_balances.get(symbol)
        ):
            # debug code
            # reset_position = 2 if case_1[1]==1 else 1

            # 주문 신호 발생기
            status, order_signal_open = asyncio.run(
                obj_order.generate_order_open_signal(
                    symbol=symbol,
                    position=case_1[1],
                    # position=reset_position,
                    leverage=int(case_1[4] / 60),
                    balance=trade_balance,
                    entry_price=target_data.get(symbol).get("1m")[-1][4],
                    open_timestamp=target_data.get(symbol).get("1m")[-1][6],
                )
            )
            # 주문 신호 발생시
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
                trade_data.append(order_signal_open)
                trade_data.append(obj_wallet.balance_info)

        # 포지션 종료 검사.
        # 현재가
        current_price = float(target_data[symbol]["1m"][-1][4])
        # wallet 보유현황
        is_wallet = obj_process.trading_data.get(symbol)
        # print(is_wallet)
        obj_wallet.get_wallet_status(symbol=symbol, current_price=current_price)

        # 만약 wallet에 해당 symbol이 없다면..
        if is_wallet is not None:
            # 매도 가격 도달 여부 (bool)
            is_stop = obj_process.get_trading_stop_signal(
                symbol=symbol, current_price=current_price
            )
            # 만약 매도 가격 도달시 (True)
            if is_stop:
                # 지갑 금액 정보 업데이트

                # 종료 신호 생성
                value = obj_order.generate_order_close_signal(
                    symbol=symbol,
                    current_price=current_price,
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
    # 실시간 변동이 보고싶다면 이곳에.
    utils._std_print(f"{i} / {range_length_data}")
    # utils._std_print(round(obj_wallet.get_wallet_status(symbol=symbol, current_price=current_price)['total_assets'],3))

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


# import numpy as np
# from typing import Tuple
# from multiprocessing import Pool, Manager, cpu_count
# import asyncio
# import nest_asyncio
# from datetime import datetime
# import os
# import utils
# from pprint import pprint
# import Analysis
# import DataProcess
# from BinanceBackTest import *

# nest_asyncio.apply()

# def process_symbol(args):
#     """
#     각 종목에 대한 트레이딩 시나리오 처리 함수
#     """
#     symbol, data, obj_analy, obj_con, obj_order, obj_wallet, obj_process = args

#     results = []
#     pnl_data = {}
#     pnl_count = {}

#     # 시나리오 1 검사.
#     case_1 = obj_analy.scenario_1(symbol=symbol, convert_data=data)

#     # 주문 제약 사항 스펙
#     constraint = obj_con.calc_fund(obj_wallet.balance_info['total_assets'], rate=0.2)
#     trade_count = constraint.get('count')
#     trade_balance = constraint.get('tradeValue')

#     # 시나리오 1 조건
#     if case_1[1] > 0 and case_1[2] >= 3 and case_1[3] >= 3 and case_1[-1] and not obj_wallet.account_balances.get(symbol):
#         status, order_signal_open = asyncio.run(obj_order.generate_order_open_signal(
#             symbol=symbol,
#             position=case_1[1],
#             leverage=int(case_1[4] / 60),
#             balance=trade_balance,
#             entry_price=data.get(symbol).get('1m')[-1][4],
#             open_timestamp=data.get(symbol).get('1m')[-1][6]
#         ))
#         if status and trade_count > obj_wallet.balance_info['locked_funds']['number_of_stocks']:
#             # 포지션 종료를 위한 초기값 업데이트
#             obj_process.initialize_trading_data(symbol=symbol,
#                                                  position=order_signal_open['position'],
#                                                  entry_price=order_signal_open['entryPrice'])
#             # 지갑 정보 업데이트
#             obj_wallet.add_funds(order_signal=order_signal_open)
#             results.append(order_signal_open)
#             results.append(obj_wallet.balance_info)

#     # 포지션 종료 검사
#     current_price = float(data[symbol]['1m'][-1][4])
#     is_wallet = obj_process.trading_data.get(symbol)
#     if is_wallet is not None:
#         is_stop = obj_process.get_trading_stop_signal(symbol=symbol, current_price=current_price)
#         if is_stop:
#             value = obj_order.generate_order_close_signal(
#                 symbol=symbol,
#                 current_price=current_price,
#                 wallet_data=obj_wallet.account_balances
#             )
#             _, pnl_value = obj_wallet.remove_funds(symbol=symbol)
#             obj_process.remove_trading_data(symbol)
#             results.append(obj_wallet.account_balances.get(symbol))
#             results.append(obj_wallet.balance_info)

#             if not pnl_data.get(symbol):
#                 pnl_data[symbol] = float(pnl_value)
#                 pnl_count[symbol] = 0
#             else:
#                 pnl_data[symbol] += float(pnl_value)
#                 pnl_count[symbol] += 1

#     return results, pnl_data, pnl_count

# from datetime import datetime
# async def main():
#     """
#     멀티프로세싱 및 비동기 처리를 결합한 메인 함수
#     """
#     print(f"작업시작 >> {datetime.now()}")

#     # symbols 지정
#     symbols = [
#         "BTCUSDT", "XRPUSDT", "ADAUSDT", "NOTUSDT", "SANDUSDT", "ARKMUSDT", "SOLUSDT", "DOGEUSDT"
#     ]
#     intervals = ["1m", "3m", "5m", "1h"]
#     start_date = "2024-11-1 00:00:00"
#     end_date = "2024-11-29 23:59:59"

#     # 인스턴스 로딩
#     obj_process = DataProcess.TradeStopper()
#     obj_analy = Analysis.AnalysisManager(back_test=True)
#     obj_analy.intervals = intervals
#     obj_order = OrderManager()
#     obj_con = DataProcess.OrderConstraint()
#     obj_data = DataManager(
#         symbols=symbols, intervals=intervals, start_date=start_date, end_date=end_date
#     )

#     # print(f"데이터 다운로드 시작 >> {datetime.now()}")
#     range_length_data, kline_data, indices_data, closing_sync_data = await obj_data.read_data_run(download_if_missing=True)
#     print(f"데이터 다운로드(로딩) 완료 >> {datetime.now()}")

#     kline_data = obj_data.convert_kline_data_array(kline_data=kline_data)

#     # Wallet 초기화
#     seed_money = 1000
#     obj_wallet = WalletManager(initial_fund=seed_money)

#     # 멀티프로세싱 설정
#     pool = Pool(processes=cpu_count())
#     tasks = []

#     # 분석 시작
#     for i in range(10, range_length_data, 1):
#         # kline_data = obj_data.sync_kline_data(idx=i, kline_data=kline_data, idx_mapping=indices_data, sync_data=closing_sync_data)
#         # target_data = obj_data.get_kline_interval_data_by_range(end_idx=i, kline_data=kline_data, idx_data=indices_data)
#         target_data =
#         # 멀티프로세싱을 위한 인자 준비
#         args_list = [(symbol, target_data, obj_analy, obj_con, obj_order, obj_wallet, obj_process) for symbol in symbols]

#         # 멀티프로세싱을 통해 분석 수행
#         results = pool.map(process_symbol, args_list)

#         # 결과 병합 및 출력
#         for result, pnl_data, pnl_count in results:
#             for item in result:
#                 pprint(item)
#         utils._std_print(f'{i} / {range_length_data}')

#     pool.close()
#     pool.join()

#     print(f"분석 종료 {datetime.now()}")

#     # 최종 지갑 정보 및 PNL 출력
#     print("\n==>> 최종 지갑 정보")
#     pprint(obj_wallet.balance_info)
#     utils._save_to_json(file_path=f"{os.path.dirname(os.getcwd())}/DataStore/balance_info.json", new_data=obj_wallet.balance_info)

#     print("\n==>> 최종 계좌 잔액")
#     pprint(obj_wallet.account_balances)
#     utils._save_to_json(file_path=f"{os.path.dirname(os.getcwd())}/DataStore/account_balances.json", new_data=obj_wallet.account_balances)

#     print("\n==>> PNL 정보")
#     trade_data = []
#     for idx, data in enumerate(results):
#         print(f"No. {idx}")
#         pprint(data)
#     utils._save_to_json(file_path=f"{os.path.dirname(os.getcwd())}/DataStore/trade_data.json", new_data=trade_data)


# if __name__ == "__main__":
#     asyncio.run(main())
