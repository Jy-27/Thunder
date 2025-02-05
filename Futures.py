from typing import Union, Final, Tuple, List, Dict
import MarketDataFetcher
import TradeClient
import utils

### 전역 상수 선언
MAX_LEVERAGE = 125
MIN_LEVERAGE = 2
BUY_TYPE: Tuple[int, str] = (1, "BUY")
SELL_TYPE: Tuple[int, str] = (2, "SELL")
MARKETS: List = ["FUTURES", "SPOT"]
### 인스턴스 생성

# market
INS_MARKET_FUTURES = MarketDataFetcher.FuturesMarket()
INS_MARKET_SPOT = MarketDataFetcher.SpotMarket()
# INS_MARKET_MANAGER = MarketDataFetcher.MarketDataManager()

# client
INS_CLIENT_FUTURES = TradeClient.FuturesClient()
INS_CLIENT_SPOT = TradeClient.SpotClient()
# INS_CLIENT_MANAGER = TradeClient.BinanceClientManager()


### 함수 동작을 위한 내함수
def _validate_args_position(position: Union[int, str]) -> Union[int, str]:
    # position타입이 문자형인 경우
    if isinstance(position, str):
        # 대문자로 변환
        position = position.upper()
        # 각 타입의 index 1을 set으로 구성 및 포함여부 확인
        if position not in {BUY_TYPE[1], SELL_TYPE[1]}:
            raise ValueError(f"position 입력 오류: {position}")

    # position을 정수형으로 변환 (숫자이거나 문자열에서 변환된 경우)
    elif isinstance(position, int):
        # 각 타입의 index 0을 set으로 구성 및 포함여부 확인
        if position not in {BUY_TYPE[0], SELL_TYPE[0]}:
            raise ValueError(f"position 입력 오류: {position}")

    # args position 입력타입 오류시
    else:
        raise ValueError(f"position은 int 또는 str만 입력 가능: {type(position)}")
    return position


def _validate_args_leveragse(leverage: int) -> int:
    if not isinstance(leverage, int):
        raise ValueError(f"leverage 타입 입력 오류: {type(leverage)}")
    if MAX_LEVERAGE < leverage:
        raise ValueError(f"leverage는 {MAX_LEVERAGE}를 초과할 수 없음: {leverage}")
    if MIN_LEVERAGE > leverage:
        raise ValueError(f"leverage는 최소 {MIN_LEVERAGE} 이상이어야 함: {leverage}")
    return leverage


def _validate_args_direction_of_order(validate_position: Union[int, str]) -> int:
    """
    Binance Futures 계산에 쓰일 direction_of_order 값을 계산한다.
    Long position은 1, Short Position은 -1값을 반환한다.
    다만 args값은 검증된 값을 입력해야만 한다.

    Args:
        validate_position (Union[int, str]): position 값

    Returns:
        int: 1 or -1

    Notes:
        args에 들어갈 값이 올바르다면 문제 없으나, 그렇지 못할경우 오류가 발생한다.
        올바른 값은 전역 상수의 BUY_TYPE, SELL_TYPE를 따른다.

    Example:
        position = 1

        validate_position = _validate_args_position(position)
        direction_of_order = _validate_args_direction_of_order(validate_position)
    """
    if validate_position in BUY_TYPE:
        return 1
    else:
        return -1


def calculate_imr(leverage: int) -> float:  # 🚀
    """
    IMR(Initial Margin Ratio) 초기 증거금 비율을 계산한다.

    Args:
        leverage (int): 적용할 레버리지값

    Raises:
        ValueError: leverage가 int가 아닐경우
        ValueError: leverage가 MAX_LEVERAGE(125배)를 초과할 경우

    Returns:
        float: IMR값

    Example:
        leverage = 5
        imr = calculate_imr(leverage)
        print(imr)
    """
    leverage = _validate_args_leveragse(leverage)
    return 1 / leverage


# 초기 마진값 산출
def calculate_initial_margin(
    position_size: Union[float, int], entry_price: Union[float, int], imr: float
) -> float:  # 🚀
    """
    Binance Futures 거래시 초기 마진값을 계산한다. Spot 거래에서는 사용하지 않는다.

    Args:
        position_size (Union[float, int]): 진입 수량
        entry_price (Union[float, int]): 진입 가격
        imr (float): 초기 마진 비율
            >> IMR(Initial Margin Ratio) 초기 증거금 비율
            >> calculate_imr 함수로 계산가능.

    Return:
        float: 초기 마진값 (USDT 기준)

    Notes:
        fee는 반영이 안되어 있음.

    Example:
        leverage = 5
        position_size = 10
        entry_price = 4.5
        imr = calculate_imr(leverage)

        initial_margin = calculate_initial_margin(position_size, entry_price, imr)
    """
    return float(position_size * entry_price * imr)


# 손익금 산출
def calculate_net_pnl(
    position: Union[int, str],
    entry_price: Union[float, int],
    exit_price: Union[float, int],
    position_size: Union[float, int],
) -> float:  # 🚀
    """
    포지션(롱/숏)에 따른 손익(PnL)을 계산하는 함수이며 현물거래시 position은 항상 1이다.

    Args:
        position (Union[int, str]): 포지션 (1 또는 'BUY' / 2 또는 'SELL')
        entry_price (Union[float, int]): 진입 가격
        exit_price (Union[float, int]): 종료 가격
        position_size (Union[float, int]): 계약 수량 (Futures거래시 position_size를 의미함.)

    Returns:
        float: 손익 (PnL)

    Notes:
        사용 용도에 따라서 net_pnl과 unrealized_pnl사용에 활용할 수 있다.

    Raises:
        ValueError: position이 올바르지 않은 값일 경우 예외 발생

    Example:
        position = 1
        entry_price = 1.2
        exit_price = 1.3
        position_size = 10

        pnl = calculate_pnl(position, entry_price, exit_price, position_size)
    """
    validated_position = _validate_args_position(position=position)
    # PnL 계산 (롱 포지션인지, 숏 포지션인지 판별)
    if validated_position in {BUY_TYPE[0], BUY_TYPE[1]}:  # 롱(매수) 포지션
        return float((exit_price - entry_price) * position_size)
    else:  # 숏(매도) 포지션
        return float((entry_price - exit_price) * position_size)


# 미실현 손익금 산출
def calculate_unrealized_pnl(
    entry_price: float,
    mark_price: float,
    position_size: [float, int],
    direction_of_order: int,
) -> float:  # 🚀
    """
    미실현 손익(pnl)을 계산한다. direction_of_order가 항상 1이다.

    Args:
        entry_price (float): 진입가격
        mark_price (float): 현재가격(websocket 수신데이터의 close_price)
        position_size (float, int]): position_size(Futures 시장에서는 position_size라고 사용함)
        direction_of_order (float): _validate_args_direction_of_order(validate_position:Union[int, str]) -> int: 적용 1 또는 -1

    Returns:
        _type_: _description_

    Notes:
        calculate_net_pnl 함수의 결과값과 같다. 다만 매개변수 적용방법과 공식의 차이일 뿐이다. 매개변수만 준비된다면 net_pnl산출에 사용해도 무방하다.
    """
    return float(position_size * direction_of_order * (mark_price - entry_price))


# 수익률 산출 (PNL 기준)
def calculate_roi_by_pnl(initial_margin: calculate_initial_margin, pnl: float) -> float:
    """
    투자 수익률(ROI, Return on Inverstment) 계산 (공식 1)

    Args:
        initial_margin (float): 초기증거금 비율
            >> calculate_imr(leverage)를 이용하여 계산
        pnl (float): 손익금액
            >> calculate_pnl(position, entry_price, exit_price, position_size)를 이용하여 산출

    Resturn:
        float: 투자 수익률

    Notes:
        ROI 계산 공식중 하나를 적용

    Example:
        entry_price = 1.2
        position_size = 10
        initial_margin = calculate_pnl(position_size, entry_price)

        position = 1
        exit_price = 1.3
        pnl = calculate_pnl(position, entry_price, exit_price, position_size)

        roi = calculate_roi_by_pnl(initial_margin, pnl)
    """
    return pnl / initial_margin


# 수익률 산출 (가격 기준)
def calculate_roi_by_price(
    entry_price: float, exit_price: float, position: Union[int, str], imr: float
) -> float:
    """
    투자 수익률(ROI, Return on Inverstment) 계산 (공식 2)

    Args:
        entry_price (float): 진입 가격
        exit_price (float): 종료 가격
        position (Union[int, str]): 포지션
        imr (float): 초기 마진값

    Returns:
        float: 투자 수익률

    Notes:
        ROI 계산 공식중 하나를 적용

    Example:
        entry_price = 1.2
        exit_price = 1.3
        position = 1
        leverage = 5

        imr = calculate_imr(leverage)

        roi = calculate_roi_by_price(entry_price, exit_price, position, imr)
    """
    # 부포 변환
    sign_flip = -1
    # Agrs 검증
    validated_position = _validate_args_position(position=position)

    side = _validate_args_direction_of_order(validated_position) * sign_flip
    return side * ((1 - (exit_price / entry_price)) / imr)


# 손익률 기준 목표금액 산출
def calculate_target_price(
    entry_price: float, target_roi: float, leverage: int, position: Union[float, str]
) -> float:
    """
    수익률을 반영하여 목표 단가를 산출한다.

    Args:
        entry_price (float): 진입가
        target_roi (float): 목표 수익률
        leverage (int): 레버리지
        position (Union[float, str]): 포지션

    Returns:
        float: 목표 단가

    Notes:
        목표 수익률에 다른 포지션 종료 단가를 계산한다.

    Example:
        entry_price = 1.2
        target_roi = 0.5  (50%)
        leverage = 5
        position = 1

        target_price = calculate_target_price(entry_price, target_roi, leverage, position)
    """

    validated_leverage = _validate_args_leveragse(leverage)
    validated_position = _validate_args_position(position)
    if validated_position in BUY_TYPE:
        return entry_price * ((target_roi / validated_leverage) + 1)
    else:
        return entry_price * (1 - (target_roi / leverage))


# 가용 마진금액
def calculate_available_margin(
    net_collateral: float, open_order_losses: float, initial_margins: float
) -> float:
    """
    사용가능한 예수금을 계산한다.

    Args:
        net_collateral (float): ∑순 담보 (총 자산에서 부채를 제외한 값)
        open_order_losses (float): ∑미체결 주문으로 인해 발생한 잠재적 손실
        initial_margins (float): ∑현재 오픈된 포지션을 유지하는데 필요한 초기 마진

    Returns:
        float: 사용 가능 마진(예수금)

    Notes:
        총 예수금 계산한다. 토탈 금액에서 현재 보유중인 초기마진금액, 미체결 주문의 차이를 구한다.
        바이낸스 공식을 대입한 함수이며, 아직 테스트 단계다.

    Example:
        open_order_losses = 미체결 주문 합계
        net_collateral = 순 담보
        initial_margins = 현재 진행중인 포지션의 마진값 합

        available_margin = calculate_available_margin(net_collateral, open_order_losses, initial_margins)
    """
    return max(0, net_collateral - open_order_losses - initial_margins)


# TradeClient instance 선택
def get_instance_client_by_market(market: str):
    """'
    TradeClient의 market별 instance 획득한다.
    본 파일의 내용은 Futures이므로 사용가능성이 없다고 봐도 무방하다.

    Args:
        market (str): MARKETS 중 선택

    Returns:
        TradeClient.(market)

    Notes:
        본 파일은 Futures전용이므로 사용 계획이 없음.

    Example:
        market = 'futures'
        ins_client = get_instance_client_by_market(market)
    """
    market = market.upper()
    if market not in MARKETS:
        raise ValueError(f"market 오입력: {market}")
    return {MARKETS[0]: INS_CLIENT_FUTURES, MARKETS[1]: INS_MARKET_SPOT}.get(market)


# API availableBalance 조회 및 반환
def extract_available_balance(account_data: INS_CLIENT_FUTURES.fetch_account_balance) -> float:
    """
    Futures 계좌의 예수금을 조회한다.
    """
    result = account_data["availableBalance"]
    return float(result)


# API totalWalletBalance 조회 및 반환
def extract_total_wallet_balance(account_data: INS_CLIENT_FUTURES.fetch_account_balance) -> float:
    result = account_data["totalWalletBalance"]
    return float(result)


# API 최대 레버리지값 조회 및 반환
def extract_max_leverage(brackets_data: INS_CLIENT_FUTURES.fetch_leverage_brackets) -> int:
    leverage = brackets_data[0]["brackets"][0]['initialLeverage']
    return int(leverage)


def extract_exchange_symbols_info(symbol: str, exchange_data: INS_MARKET_FUTURES.fetch_exchange_info) -> dict:  # 🚀
    """
    exchange 데이터의 "symbols" 정보를 추출한다.

    Args:
        symbol (str): 분류하고 싶은 symbol정보
        exchange_data (dict): MarketDataFetcher.FuturesMarket().fetch_exchange_info() 반환값

    Returns:
        {'tickSize': 0.0001,
         'minPrice': 0.0143,
         'maxPrice': 100000.0,
         'minQty': 0.1,
         'maxQty': 10000000.0,
         'stepSize': 0.1,
         'marketMaxQty': 2000000.0,
         'limitOrders': 200.0,
         'limitAlgoOrders': 10.0,
         'notional': 5.0,
         'multiplierUp': 1.05,
         'multiplierDown': 0.95,
         'multiplierDecimal': 4.0}

    Notes:
        반환값별 설명
            'tickSize' : 가격의 최소 단위 (1틱당 가격)
            'minPrice' : 주문 가능한 최저 가격
            'maxPrice' : 주문 가능한 최고 가격
            'minQty' : 주문 가능한 최소 수량
            'maxQty' : 주문 가능한 최대 수량
            'stepSize' : 주문 가능한 최소 단위
            'marketMinQty' : 시장가 주문 최소 주문 가능 수량
            'marketMaxQty' : 시장가 주문 최대 주문 가능 수량
            'limitOrders' :  동시에 열 수 있는 주문 개수
            'limitAlgoOrders' : 알고리즘 주문(조건부 주문 내역)
            'notional' : 명복가치, 계약가치
            'multiplierUp' : 주문 가능한 최저 비율
            'multiplierDown' : 주문 가능한 최고 비율
            'multiplierDecimal' : 가격제한 정밀도(소수점)

        minPrice or multiplierDown // multiplierUp or maxPrice는 이중적 보안장치로 AND 조건임.
    
    Example:
        symbol = 'BTCUSDT'
        exchange_data = MarketDataFetcher.FuturesMarket().fetch_exchange_info()
        symbol_info = extract_exchange_symbols_info('BTCUSDT', exchange_data)
    
    """
    symbols_data = exchange_data["symbols"]
    symbol_info = next(item for item in symbols_data if item["symbol"] == symbol)
    filters_data = symbol_info["filters"]

    return {
        "tickSize": float(filters_data[0]["tickSize"]),  # 가격의 최소 단위 (1틱당 가격)
        "minPrice": float(filters_data[0]["minPrice"]),  # 주문 가능한 최저 가격 (range)
        "maxPrice": float(filters_data[0]["maxPrice"]),  # 주문 가능한 최고 가격 (range)
        "minQty": float(filters_data[1]["minQty"]),  # 주문 가능한 최소 수량
        "maxQty": float(filters_data[1]["maxQty"]),  # 주문 가능한 최대 수량
        "stepSize": float(filters_data[1]["stepSize"]),  # 주문 가능한 최소 단위
        "marketMinQty": float(
            filters_data[2]["minQty"]
        ),  # 시장가 주문 최소 주문 가능 수량
        "marketMaxQty": float(
            filters_data[2]["maxQty"]
        ),  # 시장가 주문 최대 주문 가능 수량
        "limitOrders": float(filters_data[3]["limit"]),  # 동시에 열 수 있는 주문 개수
        "limitAlgoOrders": float(
            filters_data[4]["limit"]
        ),  # 알고리즘 주문(조건부 주문 내역)
        "notional": float(filters_data[5]["notional"]),  # 명복가치, 계약가치
        "multiplierUp": float(filters_data[6]["multiplierUp"]),  # 주문 가능한 최저 비율
        "multiplierDown": float(
            filters_data[6]["multiplierDown"]
        ),  # 주문 가능한 최고 비율
        "multiplierDecimal": float(filters_data[6]["multiplierDecimal"]),
    }  # 가격제한 정밀도(소수점)


# 최소 Position Size 산출
def calculate_min_position_size(
    mark_price: float, min_qty: float, step_size: float, notional: float
):
    """
    최소 진입 가능한 position size를 산출한다.

    Args:
        mark_price (float): 현재가
        min_qty (float): extract_exchange_symbols_info()['minQty']
        step_size (float): extract_exchange_symbols_info()['stepSize']
        notional (float): extract_exchange_symbols_info()['notional']

    Returns:
        float: min position size
    """
    required_size = notional / mark_price
    min_size = utils._round_up(value=required_size, step=step_size)
    return max(min_size, min_qty)


# 최대 Position Size 산출
def calculate_max_position_size(
    mark_price: float, leverage: int, step_size: float, balance: float
):
    """
    최대 진입 가능한 position size를 산출한다.

    Args:
        mark_price (float): 현재가
        max_qty (float): extract_exchange_symbols_info()['maxQty']
        step_size (float): extract_exchange_symbols_info()['stepSize']
        notional (float): extract_exchange_symbols_info()['notional']

    Returns:
        float: max position size
    """
    required_size = (balance * leverage) / mark_price
    max_size = utils._round_down(value=required_size, step=step_size)
    return max_size


# 지정 symbol값에 대한 포지션 정보를 반환한다.
def extract_position(symbol:str, account_data: INS_CLIENT_FUTURES.fetch_account_balance) -> Dict:
    """
    지정한 symbol값의 포지션 정보값을 반환한다.

    Args:
        symbol (str): symbol값
        account_data (Dict): TradeClient.FuturesClient.fetch_account_balance() 수신값

    Returns:
        {'symbol': 'SOLUSDT',
         'initialMargin': '0',
         'maintMargin': '0',
         'unrealizedProfit': '0.00000000',
         'positionInitialMargin': '0',
         'openOrderInitialMargin': '0',
         'leverage': '75',
         'isolated': False,
         'entryPrice': '0.0',
         'breakEvenPrice': '0.0',
         'maxNotional': '100000',
         'positionSide': 'BOTH',
         'positionAmt': '0',
         'notional': '0',
         'isolatedWallet': '0',
         'updateTime': 0,
         'bidNotional': '0',
         'askNotional': '0'}
    """
    position_data = next(data for data in account_data['positions'] if data['symbol'] == symbol)
    return position_data

# 보유중인 포지션 정보 전체를 반환한다.
def extract_open_positions(account_data: INS_CLIENT_FUTURES.fetch_account_balance) -> Dict:  # 🚀
    """
    보유중인 포지션 전체 정보값을 반환한다.

    Args:
        account_data (dict): TradeClient.FuturesClient.fetch_account_balance() 수신값

    Resturn:
        {'XRPUSDT': {'initialMargin': 2.23689411,
                     'maintMargin': 0.02236894,
                     'unrealizedProfit': -0.70481176,
                     'positionInitialMargin': 2.23689411,
                     'openOrderInitialMargin': 0,
                     'leverage': 2,
                     'isolated': True,
                     'entryPrice': 2.877,
                     'breakEvenPrice': 2.8784385,
                     'maxNotional': 50000000,
                     'positionSide': 'BOTH',
                     'positionAmt': 1.8,
                     'notional': 4.47378823,
                     'isolatedWallet': 2.59310914,
                     'updateTime': 1738713600499,
                     'bidNotional': 0,
                     'askNotional': 0}},
         'ADAUSDT': {'initialMargin': 2.23689411,
                     'maintMargin': 0.02236894,
                     'unrealizedProfit': -0.70481176,
                     'positionInitialMargin': 2.23689411,
                     'openOrderInitialMargin': 0,
                     'leverage': 2,
                     'isolated': True,
                     'entryPrice': 2.877,
                     'breakEvenPrice': 2.8784385,
                     'maxNotional': 50000000,
                     'positionSide': 'BOTH',
                     'positionAmt': 1.8,
                     'notional': 4.47378823,
                     'isolatedWallet': 2.59310914,
                     'updateTime': 1738713600499,
                     'bidNotional': 0,
                     'askNotional': 0}}

    Notes:
        None

    Example:
        ins_client_futures = TradeClient.FuturesClient()
        account_data = asyncio.run(ins_client_futures.fetch_account_balance())

        open_positions = extract_open_positions(account_data)
    """
    positions_data = account_data["positions"]
    result = {}
    for position in positions_data:
        """
        여기서 조건문을 0보다 크게 하면 안된다. short position의 경우 음수로 표기되기 때문이다.
        """
        if float(position["positionAmt"]) != 0:
            symbol = position["symbol"]
            result[symbol] = {}
            for key, value in position.items():
                result[symbol][key] = value
    return result



if __name__ == "__main__":
    from pprint import pprint
    import asyncio
    import shutil
    terminal_width = shutil.get_terminal_size().columns
    text = "*-=-=-  EXAMPLE  -=-=-*"
    print(' ')
    print(text.center(terminal_width))
    print(' ')
    ins_client = TradeClient.FuturesClient()
    ins_market = MarketDataFetcher.FuturesMarket()
    account_balance = asyncio.run(ins_client.fetch_account_balance())

    symbol = 'XRPUSDT'
    position_size = 1.8
    entry_price = 2.877
    mark_price = float(asyncio.run(ins_market.fetch_symbol_price(symbol))['price'])
    leverage = 2
    imr = calculate_imr(leverage)
    position = _validate_args_position(1)
    direction_of_order = _validate_args_direction_of_order(position)
    print(f'1. IMR: {imr}')
    init_margnin = calculate_initial_margin(position_size=position_size, entry_price=entry_price, imr=imr)
    print(f'2. initial_marging: {init_margnin:,.2f} USDT')
    net_pnl = calculate_net_pnl(position=position, entry_price=entry_price, exit_price=mark_price, position_size=position_size)
    print(f'3. net_pnl: {net_pnl:,.2f} USDT')
    unrealized_pnl = calculate_unrealized_pnl(entry_price=entry_price, mark_price=mark_price, position_size=position_size, direction_of_order=direction_of_order)
    print(f'4. unrealized_pnl: {unrealized_pnl:,.2f} USDT')
    roi_price = calculate_roi_by_price(entry_price=entry_price, exit_price=mark_price, position=position, imr=imr)
    print(f'5. ROI(Price): {roi_price:,.2f} %')
    roi_pnl = calculate_roi_by_pnl(initial_margin=init_margnin, pnl=net_pnl)
    print(f'6. ROI(PNL): {roi_pnl:,.2f} USDT')
    ava_balance = extract_available_balance(account_balance)
    print(f'7. available_balance: {ava_balance:,.2f} USDT')
    total_balance = extract_total_wallet_balance(account_balance)
    print(f'8. total_balance: {total_balance:,.2f}')

    brackets_data = asyncio.run(ins_client.fetch_leverage_brackets(symbol))
    max_leverage = extract_max_leverage(brackets_data)
    print(f'9. MAX_leverage: {max_leverage}')
    exchange_info = asyncio.run(ins_market.fetch_exchange_info())
    symbols_info = extract_exchange_symbols_info(symbol, exchange_info)
    print(f'10. symbols_info:')
    pprint(symbols_info)

    step_size = symbols_info['stepSize']
    notionla = symbols_info['notional']
    min_qty = symbols_info['minQty']
    min_position_size = calculate_min_position_size(mark_price, min_qty, step_size, notionla)
    print(f'11. min_position_size: {min_position_size}')
    max_position_size = calculate_max_position_size(mark_price, leverage, step_size, ava_balance)
    print(f'12. max_position_size: {max_position_size}')
    position_info = extract_position(symbol, account_balance)
    print(f'13. position_info:')
    pprint(position_info)
    open_positions = extract_open_positions(account_balance)
    print(f'14. open_positions:')
    pprint(open_positions)
