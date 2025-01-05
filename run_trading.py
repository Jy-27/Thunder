from SimulateTrading import *

# from RealTrading import *
import TradeComputation


if __name__ == "__main__":
    symbols = [
        # "btcusdt",
        "xrpusdt",
        "adausdt",
        # "linkusdt",
        # "sandusdt",
        # "bnbusdt",
        "dogeusdt",
        # "solusdt",
    ]  # 확인하고자 하는 심볼 정보
    # intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    ### 수신받을 데이터의 기간 ###
    start_date = "2024-11-1 09:00:00"  # 시작 시간
    end_date = "2025-1-5 08:59:59"  # 종료 시간
    safety_balance_ratio = 0.2  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.5  # 스톱 로스 비율
    is_download = False  # 기존 데이터로 할경우 False, 신규 다운로드 True
    adj_timer = True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    adj_rate = 0.0007
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 69690
    max_trade_number = 3
    start_step = 5_000
    leverage = 10
    init_stop_rate = 0.015
    adj_interval = "3m"
    is_order_break = True
    loss_chance = 1
    step_interval = "4h"

    ### Ticker Setting Option ###
    comparison = "above"  # above : 이상, below : 이하
    absolute = True  # True : 비율 절대값, False : 비율 실제값
    value = 35_000_000  # 거래대금 : 단위 USD
    target_percent = 0.03  # 변동 비율폭 : 음수 가능
    quote_type = "usdt"  # 쌍거래 거래화폐

    backtest_ins = BackTester(
        symbols=symbols,
        # intervals=intervals,
        start_date=start_date,
        end_date=end_date,
        safety_balance_ratio=safety_balance_ratio,
        stop_loss_rate=stop_loss_rate,
        is_download=is_download,
        adj_timer=adj_timer,
        adj_rate=adj_rate,
        is_use_scale_stop=use_scale_stop,
        seed_money=seed_money,
        max_trade_number=max_trade_number,
        start_step=start_step,
        max_leverage=leverage,
        init_stop_rate=init_stop_rate,
        adj_interval=adj_interval,
        is_order_break=is_order_break,
        loss_chance=loss_chance,
        step_interval=step_interval,
        comparison=comparison,
        absolute=True,
        value=value,
        percent=target_percent,
        quote_type=quote_type,
    )

    asyncio.run(backtest_ins.run())
    analyze_statistics = TradeComputation.ResultEvaluator(backtest_ins.portfolio_ins)
    analyze_statistics.run_analysis()
