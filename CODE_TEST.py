from decimal import Decimal, getcontext

def calculate_liquidation_price(entry_price, size, leverage, maint_margin_percent, fee_rate, liquidation_fee, position_type="long"):
    """
    Binance 격리 마진(Isolated Margin) 청산 가격 계산기.
    :param entry_price: 진입 가격 (Decimal, USDT)
    :param size: 포지션 크기 (Decimal, 계약 수)
    :param leverage: 레버리지 (Decimal)
    :param maint_margin_percent: 유지 증거금 비율 (Decimal, 예: 0.025)
    :param fee_rate: 거래 수수료율 (Decimal, 예: 0.0005)
    :param liquidation_fee: 청산 수수료 비율 (Decimal, 예: 0.015)
    :param position_type: 포지션 타입 ("long" 또는 "short")
    :return: 청산 가격 (Decimal)
    """
    # 포지션 명목 가치
    position_value = entry_price * size

    # 초기 증거금
    initial_margin = position_value / leverage

    # 유지 증거금
    maintenance_margin = position_value * maint_margin_percent

    # 총 수수료 (진입 + 청산)
    total_fee = 2 * (position_value * fee_rate)

    # 청산 수수료
    liquidation_fee_value = position_value * liquidation_fee

    # 사용 가능한 증거금
    available_margin = initial_margin - maintenance_margin - total_fee - liquidation_fee_value

    # 청산 가격 계산
    if position_type == "long":
        liquidation_price = entry_price * (1 - available_margin / position_value)
    elif position_type == "short":
        liquidation_price = entry_price * (1 + available_margin / position_value)
    else:
        raise ValueError("position_type은 'long' 또는 'short'여야 합니다.")

    return liquidation_price

# 소수점 정밀도 설정
getcontext().prec = 8

# 입력 데이터
entry_price = Decimal('0.008845')
size = Decimal('566')
leverage = Decimal('7')
maint_margin_percent = Decimal('0.025')
fee_rate = Decimal('0.0005')
liquidation_fee = Decimal('0.015')

# 롱 포지션 청산 가격 계산
liq_price_long = calculate_liquidation_price(
    entry_price, size, leverage, maint_margin_percent, fee_rate, liquidation_fee, position_type="long"
)
print(f"롱 포지션 청산 가격: {liq_price_long}")

# 숏 포지션 청산 가격 계산
liq_price_short = calculate_liquidation_price(
    entry_price, size, leverage, maint_margin_percent, fee_rate, liquidation_fee, position_type="short"
)
print(f"숏 포지션 청산 가격: {liq_price_short}")
