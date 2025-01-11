from SimulateTrading import *
from LiveTrading import *
# from RealTrading import *
import TradeComputation


if __name__ == "__main__":
    symbols = ["cgptusdt", "suiusdt", "aixbtusdt"]  # 확인하고자 하는 심볼 정보
    # intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    ### 수신받을 데이터의 기간 ###
    start_date = "2025-1-1 09:00:00"  # 시작 시간
    end_date = "2025-1-11 08:59:59"  # 종료 시간
    safety_balance_ratio = 0.4  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.65  # 스톱 로스 비율
    is_download = True  # 기존 데이터로 할경우 False, 신규 다운로드 True
    is_dynamic_adjustment = (
        True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    )
    dynamic_adjustment_rate = 0.0007  # 시간 흐름에 따른 시작가 변동율
    dynamic_adjustment_interval = "3m"  # 변동율 반영 스텝
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 350  # 시작금액
    leverage = 15  # 레버리지
    init_stop_rate = 0.035  # 시작 손절가
    is_order_break = True  # 반복 손실 발생시 주문 거절여부
    allowed_loss_streak = 2  # 반복 손실 발생 유예횟수
    loss_recovery_interval = "4h"  # 반복 손실 시간 범위
    max_held_symbols = 4  # 동시 거래 가능 수량
    is_profit_preservation = True  # 수익보존여부
    ### Ticker Setting Option ###
    comparison = "above"  # above : 이상, below : 이하
    absolute = True  # True : 비율 절대값, False : 비율 실제값
    value = 5_000_000  # 거래대금 : 단위 USD
    target_percent = 0.035  # 변동 비율폭 : 음수 가능
    quote_type = "usdt"  # 쌍거래 거래화폐

    TEST_MODE = False

    ins_backtest = BackTesterManager(
        symbols=symbols,
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
        seed_money=seed_money
    )
    
    if TEST_MODE:
        asyncio.run(ins_backtest.run())
        analyze_statistics = TradeComputation.ResultEvaluator(ins_backtest.ins_portfolio)
        analyze_statistics.run_analysis()
    elif not TEST_MODE:
        asyncio.run(ins_livetrading.run())