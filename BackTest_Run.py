from BackTest_binance import *
import DataProcess


if __name__ == "__main__":
    symbols = [
        "btcusdt",
        "xrpusdt",
        "adausdt",
        "linkusdt",
        "sandusdt",
        "bnbusdt",
        "dogeusdt",
        "solusdt",
    ]  # 확인하고자 하는 심볼 정보
    # intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    start_date = "2024-11-1 00:00:00"  # 시작 시간
    end_date = "2024-12-28 23:59:59"  # 종료 시간
    safety_balance_ratio = 0.02  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.35  # 스톱 로스 비율
    is_download = True  # 기존 데이터로 할경우 False, 신규 다운로드 True
    adj_timer = True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    adj_rate = 0.0007
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 69690
    max_trade_number = 3
    start_step = 5_000
    leverage = 125
    init_stop_rate = 0.015
    adj_interval = "3m"
    is_order_break = True
    loss_chance = 1
    step_interval = "4h"

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
    )

    asyncio.run(backtest_ins.run())
    analyze_statistics = DataProcess.ResultEvaluator(backtest_ins.trade_analysis_ins)
    analyze_statistics.run_analysis()
