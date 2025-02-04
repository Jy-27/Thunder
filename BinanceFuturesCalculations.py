from typing import Union, Final, Tuple, List, Dict
import MarketDataFetcher
import TradeClient
import utils

### 전역 상수 선언
MAX_LEVERAGE = 125
MIN_LEVERAGE = 2
BUY_TYPE: Tuple[int, str] = (1, "BUY")
SELL_TYPE: Tuple[int, str] = (2, "SELL")
MARKETS: List = ['FUTURES', 'SPOT']
### 인스턴스 생성

# market
INS_MARKET_FUTURES = MarketDataFetcher.FuturesMarket()
INS_MARKET_SPOT = MarketDataFetcher.SpotMarket()
# INS_MARKET_MANAGER = MarketDataFetcher.MarketDataManager()

# client
INS_CLIENT_FUTURES = TradeClient.FuturesClient()
INS_CLIENT_SPOT = TradeClient.SpotClient()
# INS_CLIENT_MANAGER = TradeClient.BinanceClientManager()


### 비공개 함수
def __validate_args_position(position: Union[int, str]) -> Union[int, str]:
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

def __validate_args_leveragse(leverage: int) -> int:
    if not isinstance(leverage, int):
        raise ValueError(f"leverage 타입 입력 오류: {type(leverage)}")
    if MAX_LEVERAGE < leverage:
        raise ValueError(f"leverage는 {MAX_LEVERAGE}를 초과할 수 없음: {leverage}")
    if MIN_LEVERAGE > leverage:
        raise ValueError(f"leverage는 최소 {MIN_LEVERAGE} 이상이어야 함: {leverage}")
    return leverage

def __validate_args_direction_of_order(validate_position: Union[int, str]) -> int:
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

        validate_position = __validate_args_position(position)
        direction_of_order = __validate_args_direction_of_order(validate_position)
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
    leverage = __validate_args_leveragse(leverage)
    return 1 / leverage


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
    return position_size * entry_price * imr


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
    validated_position = __validate_args_position(position=position)
    # PnL 계산 (롱 포지션인지, 숏 포지션인지 판별)
    if validated_position in {BUY_TYPE[0], BUY_TYPE[1]}:  # 롱(매수) 포지션
        return (exit_price - entry_price) * position_size
    else:  # 숏(매도) 포지션
        return (entry_price - exit_price) * position_size


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
        direction_of_order (float): __validate_args_direction_of_order(validate_position:Union[int, str]) -> int: 적용 1 또는 -1

    Returns:
        _type_: _description_

    Notes:
        calculate_net_pnl 함수의 결과값과 같다. 다만 매개변수 적용방법과 공식의 차이일 뿐이다. 매개변수만 준비된다면 net_pnl산출에 사용해도 무방하다.
    """
    return position_size * direction_of_order * (mark_price - entry_price)


def calculate_roi_by_pnl(initial_margin: float, pnl: float) -> float:
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
    sign_flip = -1
    validated_position = __validate_args_position(position=position)
    side = __validate_args_direction_of_order(validated_position) * sign_flip
    return side * ((1 - (exit_price / entry_price)) / imr)


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

    validated_leverage = __validate_args_leveragse(leverage)
    validated_position = __validate_args_position(position)
    if validated_position in BUY_TYPE:
        return entry_price * ((target_roi / validated_leverage) + 1)
    else:
        return entry_price * (1 - (target_roi / leverage))


def calculate_available_margin(
    net_collateral: float, open_order_loss: float, initial_margin: float
) -> float:
    """
    사용가능한 예수금을 계산한다.

    Args:
        net_collateral (float): ∑순 담보 (총 자산에서 부채를 제외한 값)
        open_order_loss (float): ∑미체결 주문으로 인해 발생한 잠재적 손실
        initial_margin (float): ∑현재 오픈된 포지션을 유지하는데 필요한 초기 마진

    Returns:
        float: 사용 가능 마진(예수금)

    Notes:
        총 예수금 계산한다. 토탈 금액에서 현재 보유중인 초기마진금액, 미체결 주문의 차이를 구한다.
        바이낸스 공식을 대입한 함수이며, 아직 테스트 단계다.

    Example:
        open_order_loss = 미체결 주문 합계
        net_collateral = 순 담보


        leverage = 5
        position_size = 10
        entry_price = 4.5
        imr = calculate_imr(leverage)

        initial_margin = calculate_initial_margin(position_size, entry_price, imr)

    """
    return max(0, net_collateral - open_order_loss - initial_margin)



def get_instance_client_by_market(market:str):
    market = market.upper()
    if market not in MARKETS:
        raise ValueError(f'market 오입력: {market}')
    return {MARKETS[0]:INS_CLIENT_FUTURES,
            MARKETS[1]:INS_MARKET_SPOT}.get(market)

def get_available_balance(account_data:Dict):
    result = account_data.get("availableBalance", None)
    if result is None:
        raise ValueError(f'account data 오류')
    return result    

def get_total_wallet_balance(account_data:Dict):
    result = account_data.get("totalWalletBalance", None)
    if result is None:
        raise ValueError(f'account data 오류')
    return result

def get_max_leverage(brackets_data:Dict):
    leverage = brackets_data[0]['brackets'][0].get(initialLeverage, None)
    if leverage is None:
        raise ValueError(f'brackets_data 오류')
    return leverage

def calculate_min_position_size(market_price:float, min_qty:float, step_size:float, notional:float):
    required_size = notional / current_price
    min_size = utils._round_up(value=required_size, step=step_size)
    return max(min_size, min_qty)

def calculate_max_position_size(market_price:float, leverage:int, step_size:float, balance:float):
    required_size = (balance * leverage) / market_price
    max_size = utils._round_down(value=required_size, step=step_size)
    return max_size

