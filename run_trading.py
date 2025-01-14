from SimulateTrading import *
from LiveTrading import *

# from RealTrading import *
import TradeComputation


if __name__ == "__main__":
    symbols = ["agldusdt", "xrpusdt", "dogeusdt", "suiusdt", "btcusdt", "ethusdt"]  # 확인하고자 하는 심볼 정보
    market = "futures"
    # intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    ### 수신받을 데이터의 기간 ###
    kline_period = 1
    start_date = "2024-11-1 09:00:00"  # 시작 시간
    end_date = "2025-1-14 08:59:59"  # 종료 시간
    safety_balance_ratio = 0.2  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.75  # 스톱 로스 비율
    is_download = False  # 기존 데이터로 할경우 False, 신규 다운로드 True
    is_dynamic_adjustment = (
        True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    )
    dynamic_adjustment_rate = 0.0007  # 시간 흐름에 따른 시작가 변동율
    dynamic_adjustment_interval = "3m"  # 변동율 반영 스텝
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 250  # 시작금액
    leverage = 10  # 레버리지
    init_stop_rate = 0.025  # 시작 손절가
    is_order_break = True  # 반복 손실 발생시 주문 거절여부
    allowed_loss_streak = 2  # 반복 손실 발생 유예횟수
    loss_recovery_interval = "4h"  # 반복 손실 시간 범위
    max_held_symbols = 4  # 동시 거래 가능 수량
    is_profit_preservation = True  # 수익보존여부
    ### Ticker Setting Option ###
    comparison = "above"  # above : 이상, below : 이하
    absolute = False  # True : 비율 절대값, False : 비율 실제값
    value = 350_000_000  # 거래대금 : 단위 USD
    target_percent = 0.035  # 변동 비율폭 : 음수 가능
    quote_type = "usdt"  # 쌍거래 거래화폐

    ### 테스트 여부 확인 ###
    while True:
        user_input = input("TEST MODE ? (y/n): ").strip().lower()

        if user_input == "y":
            TEST_MODE = True
            break
        elif user_input == "n":
            TEST_MODE = False
            break
        else:
            print("잘못된 입력입니다. 'y' 또는 'n'을 입력하세요.")

    ins_backtest = BackTesterManager(
        symbols=symbols,
        market=market,
        kline_period = kline_period,
        max_held_symbols=max_held_symbols,
        start_date=start_date,
        end_date=end_date,
        safe_asset_ratio=safety_balance_ratio,
        stop_loss_rate=stop_loss_rate,
        is_download=is_download,
        is_dynamic_adjustment=is_dynamic_adjustment,
        dynamic_adjustment_rate=dynamic_adjustment_rate,
        is_use_scale_stop=use_scale_stop,
        seed_money=seed_money,
        requested_leverage=leverage,
        init_stop_rate=init_stop_rate,
        dynamic_adjustment_interval=dynamic_adjustment_interval,
        is_order_break=is_order_break,
        allowed_loss_streak=allowed_loss_streak,
        loss_recovery_interval=loss_recovery_interval,
        comparison=comparison,
        absolute=absolute,
        value=value,
        percent=target_percent,
        quote_type=quote_type,
        is_profit_preservation=is_profit_preservation,
    )

    ins_livetrading = LiveTradingManager(
        seed_money=seed_money,
        market=market,
        kline_period=kline_period,
        safe_asset_ratio = safety_balance_ratio,
        max_held_symbols=max_held_symbols,
        use_scale_stop=use_scale_stop,
        init_stop_rate=init_stop_rate,
        stop_loss_rate=stop_loss_rate,
        symbols_comparison_mode=comparison,
        symbols_use_absolute_value=absolute,
        symbols_transaction_volume=value,
        symbols_price_change_threshold=target_percent,
        requested_leverage=leverage,
    )

    if TEST_MODE:
        asyncio.run(ins_backtest.run())
        analyze_statistics = TradeComputation.ResultEvaluator(
            ins_backtest.ins_portfolio
        )
        analyze_statistics.run_analysis()
    elif not TEST_MODE:
        asyncio.run(ins_livetrading.run())
