from typing import Union, Final, Tuple, List, Dict, Optional
import asyncio
import os
import sys
import psutil
import platform
import socket
import subprocess

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))


import Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher as futures_market
import Workspace.Services.PrivateAPI.Trading.FuturesTradingClient as futures_client
import SystemConfig
import Workspace.Utils.BaseUtils as utils

### 전역 상수 선언
config_max_leverage = 125
config_min_leverage = 2
BUY_TYPE: Tuple[int, str] = (1, "BUY")
SELL_TYPE: Tuple[int, str] = (2, "SELL")
MARKETS: List = ["FUTURES", "SPOT"]
SYMBOLS_STATUS: List = ["TRADING", "SETTLING", "PENDING_TRADING", "BREAK"]

### API 로드
api_keys = utils.load_json(SystemConfig.Path.bianace)
### 인스턴스 생성
ins_futures_market = futures_market.FuturesMarketFetcher()
ins_futures_client = futures_client.FuturesTradingClient(**api_keys)

### 백테스트용 base data

async def init_data():
    global init_account_balance, init_exchange_info, init_brackets_data
    init_account_balance = await ins_futures_client.fetch_account_balance()
    init_exchange_info = await ins_futures_market.fetch_exchange_info()
    init_brackets_data = {
        symbol: await ins_futures_client.fetch_leverage_brackets(symbol)
        for symbol in SystemConfig.Streaming.symbols
    }

asyncio.run(init_data())

class Validator:
    ### 함수 동작을 위한 내함수
    @staticmethod
    def args_position(position: Union[int, str]) -> Union[int, str]:
        """
        입력된 position값의 유효성을 검토한다.

        Args:
            position (Union[int, str]):
                >> Long : 1 or BUY
                >> Short : 2 or SELL

        Raises:
            ValueError: 잘못된 값 입력시
            ValueError: 데이터 타입이 int or str타입이 아닐 경우

        Returns:
            Union[int, str]: 1 or 2
        """
        # position타입이 문자형인 경우
        if isinstance(position, str):
            position = position.upper()
            if position not in {BUY_TYPE[1], SELL_TYPE[1]}:
                raise ValueError(f"position 입력 오류: {position}")

        # position타입이 int형인 경우
        elif isinstance(position, int):
            if position not in {BUY_TYPE[0], SELL_TYPE[0]}:
                raise ValueError(f"position 입력 오류: {position}")
        # positions 타입이 int or str타입이 아닌 경우
        else:
            raise ValueError(f"position은 int 또는 str만 입력 가능: {type(position)}")
        return position

    @staticmethod
    def args_leverage(leverage: int) -> int:
        """
        입력된 leverage값의 유효성을 검토한다.

        Args:
            leverage (int): leverage값

        Raises:
            ValueError: 입력값이 int형이 아닌 경우
            ValueError: 입력값이 125를 초과한 경우
            ValueError: 입력값이 config_min_leverage미만인 경우

        Returns:
            int: leverage
        """
        if not isinstance(leverage, int):
            raise ValueError(f"leverage 타입 입력 오류: {type(leverage)}")
        if config_max_leverage < leverage:
            raise ValueError(
                f"leverage는 {config_max_leverage}를 초과할 수 없음: {leverage}"
            )
        if config_min_leverage > leverage:
            raise ValueError(
                f"leverage는 최소 {config_min_leverage} 이상이어야 함: {leverage}"
            )
        return leverage

    @staticmethod
    def args_direction_of_order(validate_position: Union[int, str]) -> int:
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

    @staticmethod
    def contains(item, collection):
        return item in collection

    # def funds_sufficient(balance:)


class Calculator:
    @staticmethod
    def imr(leverage: int) -> float:  # 🚀
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
        validate_leverage = Validator.args_leverage(leverage)
        return 1 / validate_leverage

    # 초기 마진값 산출
    @staticmethod
    def initial_margin(
        position_size: float,
        entry_price: float,
        imr: float,
    ) -> float:  # 🚀
        """
        Binance Futures 거래시 초기 마진값을 계산한다. Spot 거래에서는 사용하지 않는다.

        Args:
            position_size (float): 진입 수량
            entry_price (float): 진입 가격
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
            imr = Calculator.imr(leverage)

            initial_margin = Calculator.initial_margin(position_size, entry_price, imr)
        """
        return float(position_size * entry_price * imr)

    # 손익금 산출
    @staticmethod
    def net_pnl(
        position: Union[int, str],
        entry_price: float,
        exit_price: float,
        position_size: float,
    ) -> float:  # 🚀
        """
        포지션(롱/숏)에 따른 손익(PnL)을 계산하는 함수이며 현물거래시 position은 항상 1이다.

        Args:
            position (Union[int, str]): 포지션 (1 또는 'BUY' / 2 또는 'SELL')
            entry_price (float): 진입 가격
            exit_price (float): 종료 가격
            position_size (float): 계약 수량 (Futures거래시 position_size를 의미함.)

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

            pnl = Calculator.net_pnl(position, entry_price, exit_price, position_size)
        """
        validated_position = _validate_args_position(position=position)
        # PnL 계산 (롱 포지션인지, 숏 포지션인지 판별)
        if validated_position in {BUY_TYPE[0], BUY_TYPE[1]}:  # 롱(매수) 포지션
            return float((exit_price - entry_price) * position_size)
        else:  # 숏(매도) 포지션
            return float((entry_price - exit_price) * position_size)

    # 미실현 손익금 산출
    @staticmethod
    def unrealized_pnl(
        entry_price: float,
        mark_price: float,
        position_size: float,
        direction_of_order: int,
    ) -> float:  # 🚀
        """
        미실현 손익(pnl)을 계산한다. direction_of_order가 항상 1이다.

        Args:
            entry_price (float): 진입가격
            mark_price (float): 현재가격(websocket 수신데이터의 close_price)
            position_size (float): position_size(Futures 시장에서는 position_size라고 사용함)
            direction_of_order (float): _validate_args_direction_of_order(validate_position:Union[int, str]) -> int: 적용 1 또는 -1

        Returns:
            _type_: _description_

        Notes:
            Calculator.net_pnl 함수의 결과값과 같다.(미세한 오차는 있음.)
            다만 매개변수 적용방법과 공식의 차이일 뿐이다. 매개변수만 준비된다면 net_pnl산출에 사용해도 무방하다.
        """
        return float(position_size * direction_of_order * (mark_price - entry_price))

    # 수익률 산출 (PNL 기준)
    @staticmethod
    def roi_by_pnl(
        initial_margin: float,
        pnl: float,
    ) -> float:
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
    @staticmethod
    def roi_by_price(
        entry_price: float,
        exit_price: float,
        position: Union[int, str],
        imr: float,
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

        side = direction_of_order(validated_position) * sign_flip
        return side * ((1 - (exit_price / entry_price)) / imr)

    # 손익률 기준 목표금액 산출
    @staticmethod
    def target_price(
        entry_price: float,
        target_roi: float,
        leverage: int,
        position: Union[float, str],
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

        validated_leverage = Validator.args_leverage(leverage)
        validated_position = Validator.args_position(position)
        if validated_position in BUY_TYPE:
            return entry_price * ((target_roi / validated_leverage) + 1)
        else:
            return entry_price * (1 - (target_roi / leverage))

    # 가용 마진금액
    @staticmethod
    def available_margin(
        net_collateral: float,
        open_order_losses: float,
        initial_margins: float,
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

    # 최소 Position Size 산출
    @staticmethod
    def min_position_size(
        mark_price: float,
        min_qty: float,
        step_size: float,
        notional: float,
    ):
        required_size = notional / mark_price
        min_size = utils.round_up(value=required_size, step=step_size)
        return max(min_size, min_qty)

    # 최대 Position Size 산출
    @staticmethod
    def max_position_size(
        mark_price: float,
        leverage: int,
        step_size: float,
        balance: float,
    ):
        required_size = (balance * leverage) / mark_price
        max_size = utils.round_down(value=required_size, step=step_size)
        return max_size


class Extractor:
    # API availableBalance 필터 및 반환
    @staticmethod
    def available_balance(
        account_data: ins_futures_client.fetch_account_balance,
    ) -> float:
        """
        Futures 계좌의 예수금을 필터한다.
        """
        result = account_data["availableBalance"]
        return float(result)

    # API totalWalletBalance 필터 및 반환
    @staticmethod
    def total_wallet_balance(
        account_data: ins_futures_client.fetch_account_balance,
    ) -> float:
        result = account_data["totalWalletBalance"]
        return float(result)

    # API 최대 레버리지값 필터 및 반환
    @staticmethod
    def max_leverage(brackets_data: ins_futures_client.fetch_leverage_brackets) -> int:
        leverage = brackets_data[0]["brackets"][0]["initialLeverage"]
        return int(leverage)

    @staticmethod
    def refine_exchange_data(
        symbol: str, exchange_data: ins_futures_market.fetch_exchange_info
    ) -> dict:  # 🚀
        """
        exchange 데이터의 "symbols" 정보를 추출한다.

        Args:
            symbol (str): 필터하고 싶은 symbol정보
            exchange_data (dict): MarketDataFetcher.FuturesMarket().fetch_exchange_info() 반환값

        # Returns:
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
            symbol_info = extract_exchange_symbol_info('BTCUSDT', exchange_data)

        """
        symbols_data = exchange_data["symbols"]
        symbol_info = next(item for item in symbols_data if item["symbol"] == symbol)
        filters_data = symbol_info["filters"]

        return {
            "tickSize": float(
                filters_data[0]["tickSize"]
            ),  # 가격의 최소 단위 (1틱당 가격)
            "minPrice": float(
                filters_data[0]["minPrice"]
            ),  # 주문 가능한 최저 가격 (range)
            "maxPrice": float(
                filters_data[0]["maxPrice"]
            ),  # 주문 가능한 최고 가격 (range)
            "minQty": float(filters_data[1]["minQty"]),  # 주문 가능한 최소 수량
            "maxQty": float(filters_data[1]["maxQty"]),  # 주문 가능한 최대 수량
            "stepSize": float(filters_data[1]["stepSize"]),  # 주문 가능한 최소 단위
            "marketMinQty": float(
                filters_data[2]["minQty"]
            ),  # 시장가 주문 최소 주문 가능 수량
            "marketMaxQty": float(
                filters_data[2]["maxQty"]
            ),  # 시장가 주문 최대 주문 가능 수량
            "limitOrders": float(
                filters_data[3]["limit"]
            ),  # 동시에 열 수 있는 주문 개수
            "limitAlgoOrders": float(
                filters_data[4]["limit"]
            ),  # 알고리즘 주문(조건부 주문 내역)
            "notional": float(filters_data[5]["notional"]),  # 명복가치, 계약가치
            "multiplierUp": float(
                filters_data[6]["multiplierUp"]
            ),  # 주문 가능한 최저 비율
            "multiplierDown": float(
                filters_data[6]["multiplierDown"]
            ),  # 주문 가능한 최고 비율
            "multiplierDecimal": float(filters_data[6]["multiplierDecimal"]),
        }  # 가격제한 정밀도(소수점)

    # 거래가능한 symbol 리스트 필터 및 반환
    @staticmethod
    def trading_symbols(exchange_data: dict) -> List[str]:
        """
        마켓에서 거래가능한 symbol 리스트를 필터 및 반환한다.

        Args:
            status (str):
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            List: symbol 리스트
        """
        status = "TRADING"
        return [
            data["symbol"]
            for data in exchange_data["symbols"]
            if data["status"] == status
        ]

    # 거래불가한 symbol 리스트 필터 및 반환
    @staticmethod
    def settling_symbols(exchange_data: dict) -> List[str]:
        """
        마켓에서 일시적 거래중단(정산진행중) symbol 리스트르르 필터 및 반환한다.

        Args:
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            List: symbol 리스트
        """
        status = "SETTLING"
        return [
            data["symbol"]
            for data in exchange_data["symbols"]
            if data["status"] == status
        ]

    @staticmethod
    def all_symbols(exchange_data: dict) -> List:
        """
        마켓에 거래중인 전체 symbol리스트를 필터 및 반환한다.

        Args:
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            List: symbol 리스트
        """
        return [data["symbol"] for data in exchange_data["symbols"]]

    @staticmethod
    def pending_symbols(exchange_data: dict) -> List:
        """
        마켓에 거래 보류중인 symbol리스트를 필터 및 반환한다.

        Args:
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            List: symbol 리스트
        """
        status = "PENDING_TRADING"
        return [
            data["symbol"]
            for data in exchange_data["symbols"]
            if data["status"] == status
        ]

    @staticmethod
    def break_symbols(exchange_data: dict) -> List:
        """
        거래 중단된 symbol리스트를 필터 및 반환한다.

        Args:
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            List: symbol 리스트
        """
        status = "BREAK"
        return [
            data["symbol"]
            for data in exchange_data["symbols"]
            if data["status"] == status
        ]

    # 지정 symbol값에 대한 포지션 정보를 반환한다.
    @staticmethod
    def position_detail(symbol: str, account_data: Dict) -> Dict:
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
        position_data = next(
            data for data in account_data["positions"] if data["symbol"] == symbol
        )
        return position_data

    @staticmethod
    def symbol_detail(symbol: str, exchange_data: dict):
        """
        symbol에 대한 상세 정보를 필터 및 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            exchange_data (dict): public의 fetch_exchange_info() 함수 반환값

        Returns:
            Dict: 상세 내역 필터
        """
        return next(
            data for data in exchange_data["symbols"] if data["symbol"] == symbol
        )

    # 보유중인 포지션 정보 전체를 반환한다.
    @staticmethod
    def current_positions(
        account_data: ins_futures_client.fetch_account_balance,
    ) -> Dict:  # 🚀
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
            ins_futures_client = TradeClient.FuturesClient()
            account_data = asyncio.run(ins_futures_client.fetch_account_balance())

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

    @staticmethod
    def format_websocket(message: dict) -> tuple:
        """
        market websocket message에서 symbol, interval, kline data를 추출한다.

        Args:
            message (dict): market websocket

        Returns:
            tuple: symbol, interval
        """
        main_data = message["data"]
        kline_data = main_data["k"]
        symbol = kline_data["s"]
        interval = kline_data["i"]

        return symbol, interval

    @staticmethod
    def format_kline_data(real_time_data) -> List[Union[int, float]]:
        """
        kline 웹소켓 수신데이터를 kline history data에 맞게 재정렬한다.

        Args:
            ws_data (_type_): 웹소켓 ['k'] 데이터

        Returns:
            List: kline data
        """
        data = real_time_data["data"]
        kline_data = data["k"]
        return [
            kline_data["t"],
            kline_data["o"],
            kline_data["h"],
            kline_data["l"],
            kline_data["c"],
            kline_data["v"],
            kline_data["T"],
            kline_data["q"],
            kline_data["n"],
            kline_data["V"],
            kline_data["Q"],
            kline_data["B"],
        ]

    @staticmethod
    def unpack_message(message:Dict) -> Tuple:
        """
        Packager class의 pack_message처리된 데이터를 unpack처리 한다.

        Args:
            message (Dict): kline data

        Returns:
            Tuple: main_key, sub_key, data
        """
        for symbol, value in message.items():
            for interval, data in value.items():
                ...
        return symbol, interval, data

class Convertor:
    @staticmethod
    def agg_trade_message(message:Dict) -> Tuple:
        """
        Websocket stream(aggTrade) 데이터를 storage에 저장하기 용이하도록 재구성한다.
        반환되는 값은 매수자 관점이다.(Notes참조)

        Args:
            message (Dict): websocket stream(aggTrade) data

        Returns:
            Tuple: symbo, execution_type, data
            
        Notes:
            ‼️ 중요
            Taker: 시장가 주문(Makrket)주문 -> 유동성 소비
            Maker: 지정가 주문(Limit)주문 -> 유동성 공급
            
            관점의 차이. 주의요망.
            m(매수자 관점)): True(매도자 Taker) / False(매도자 Maker)
        """
        select_data = message["data"]
        symbol = select_data["s"]
        m_field = select_data["m"]
        if m_field:
            execution_type = "maker"
        else:
            execution_type = "taker"

        data = [select_data["E"], select_data["p"], select_data["q"]]
        
        return symbol, execution_type, data

    @staticmethod
    def orderbook_depth_message(message:Dict) -> Tuple:
        seletc_data = message["data"]
        bids_data = [seletc_data['E']]
        asks_data = [seletc_data["E"]]
        
        
        return event_timestamp, bids, asks

class Packager:
    @staticmethod
    def pack_kline_fetcher_message(main_key, sub_key, data) -> Dict:
        """
        websocket 또는 기타 방식의 데이터를 Dict형태로 변환하여 이름표를 추가한다.
        Queue와 같은 데이터 전송시 본래의 데이터에 symbol, interval 값 미기입시 해당값을 저장한다.

        Returns:
            Dict: symbol(main_key), interval(sub_key)값 추가된 Dict
        """
        return {main_key: {sub_key:data}}

    def pack_kline_websocket_message(data) -> Dict:
        symbol = data['data']['s']
        interval = data['data']['k']['i']
        return {symbol: {interval:Extractor.format_kline_data(data)}}
        

class System:
    @staticmethod
    def os() -> Dict:
        """운영체제 정보 반환"""
        os_type = platform.system()
        os_version = platform.version()
        os_detail = platform.platform()
        return {"Type": os_type, "Version": os_version, "Detail": os_detail}

    @staticmethod
    def process_id() -> dict:
        """현재 프로세스 및 부모 프로세스 ID 반환"""
        current_p_id = os.getpid()
        parent_p_id = os.getppid()
        return {"CurrentID": current_p_id, "ParentID": parent_p_id}

    @staticmethod
    def cpu() -> Dict:
        """CPU 정보 반환"""
        processor = platform.processor()
        login_core = psutil.cpu_count(logical=True)
        physical_core = psutil.cpu_count(logical=False)
        freq = psutil.cpu_freq().max if psutil.cpu_freq() else None
        return {
            "Processor": processor,
            "LoginCore": login_core,
            "PhysicalCore": physical_core,
            "MaxFrequencyMHz": freq,
        }

    @staticmethod
    def memory() -> Dict:
        """메모리 사용량 반환"""
        memory_info = psutil.virtual_memory()
        return {
            "Total": memory_info.total,
            "Used": memory_info.used,
            "Available": memory_info.available,
            "UsedPercent": memory_info.percent,
            "Unit": "byte",
        }

    @staticmethod
    def disk() -> Dict:
        """디스크 사용량 반환"""
        disk_info = psutil.disk_usage("/")
        return {
            "Total": disk_info.total,
            "Used": disk_info.used,
            "Available": disk_info.free,
            "UsedPercent": disk_info.percent,
            "Unit": "byte",
        }

    @staticmethod
    def network_status() -> Dict:
        """네트워크 송수신량 반환"""
        net_info = psutil.net_io_counters()
        return {
            "Sent": net_info.bytes_sent,
            "Received": net_info.bytes_recv,
            "Unit": "byte",
        }

    @staticmethod
    def execute_command(command: str) -> Tuple[int, str]:
        """
        시스템 명령어 실행
        :param command: 실행할 명령어 (예: 'ls', 'pwd', 'echo hello')
        :return: (리턴 코드, 실행 결과 문자열)
        """
        try:
            result = subprocess.run(command, shell=True, text=True, capture_output=True)
            return result.returncode, result.stdout.strip()
        except Exception as error:
            return -1, str(error)


class Selector:
    # instance 래핑
    ## 본 class는 폐기 검토함.
    @staticmethod
    def account_balance(test_mode: bool):
        if test_mode:
            return FakeSignalGenerator.account_balance()
        else:
            return ins_futures_client.fetch_account_balance()

    @staticmethod
    def exchange_info(test_mode: bool):
        if test_mode:
            return FakeSignalGenerator.exchange_info()
        else:
            return ins_futures_market.fetch_exchange_info()

    @staticmethod
    def brackets_data(symbol: str, test_mode: bool):
        if test_mode:
            return FakeSignalGenerator.brackets(symbol)
        else:
            return ins_futures_client.fetch_leverage_brackets(symbol)

    @staticmethod
    def set_leverage(symbol: str, leverage: int, test_mode: bool):
        if test_mode:
            return
        else:
            return ins_futures_client.send_leverage(symbol, leverage)

    @staticmethod
    def order_signal(test_mode: bool, **kwargs):
        if test_mode:
            return FakeSignalGenerator.order_signal(**kwargs)
        else:
            return ins_futures_client.send_order(**kwargs)


class FakeSignalGenerator:
    @staticmethod
    def account_balance():
        return init_account_balance

    @staticmethod
    def exchange_info():
        return init_exchange_info

    @staticmethod
    def brackets(symbol: str):
        return init_brackets_data[symbol]

    @staticmethod
    def order_signal(**kwargs): ...