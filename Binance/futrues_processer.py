import futures_trading_utils



ins_public_api_futures = PublicAPI.Futures.API()

class TradeManager:
    @classmethod
    def position_size(cls, symbol:str, mark_price:float, leverage:int, balance:float, test_mode:bool=False) -> float:
        """
        매개 변수 조건에 의한 진입 가능한 포지션 수량을 계산한다.

        Args:
            symbol (str): 'BTCUSDT'
            mark_price (float): 진입 가격
            leverage (int): 레버리지
            balance (float): 진입 금액
            test_mode (bool): 테스트 모드 여부

        Notes:
            반환값이 0일경우 최소 진입 수량조차 미달됨(예수금 부족)
            TEST MODE와 겸용으로 사용한다.

        Returns:
            float: 진입 가능한 수량값 반환
        """
        exchange_data = futures_trading_utils.Selector.exchange_info(test_mode)
        symbol_detail = Extractor.symbol_detail(symbol, exchange_data)
        filter_data = Extractor.symbol_filters(symbol_detail['filters'])
        min_qty = filter_data['minQty']
        step_size = filter_data['stepSize']
        notional = filter_data['notional']

        min_position_size = Calculator.min_position_size(mark_price=mark_price, min_qty=min_qty, step_size=step_size, notional=notional)
        max_position_size = Calculator.max_position_size(mark_price=mark_price, leverage=leverage, step_size=step_size, balance=balance)

        if min_position_size > max_position_size:
            return 0
        return max_position_size

    @classmethod
    def get_leverage(cls, symbol: str, leverage: int, test_mode: bool) -> int:
        """
        설정하고자 하는 레버리지값의 유효성을 검사하고 적용가능한 레버리지값을 반환한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 적용하고자 하는 레버리지
            test_mode (bool): 테스트 모드 여부

        Returns:
            int: 적용가능한 레버리지값
        """
        brackets_data = Selector.brackets_data(test_mode)
        max_leverage = Extractor.max_leverage(brackets_data)
        brackets_max_leverage = Extractor.max_leverage(brackets_data)
        
        min_leverage = 2
        max_leverage = 125
        
        if min_leverage <= brackets_max_leverage <= max_leverage:
            return brackets_max_leverage
        elif max_leverage < brackets_max_leverage:
            return max_leverage
        else:
            return min_leverage

class LiveTrade(TradeManager):
    @classmethod
    async def create_open_order(
        cls,
        symbol: str,
        side: Union[str, int],
        position_size: float,
        price: Optional[float] = None,
        test_mode: bool = False,
    ):
        account_balance = await Selector.account_balance(test_mode)
        exchange_info = await Selector.exchange_info(test_mode)

        kwargs = {
            "symbol": symbol,
            "side": "BUY" if Validator.contains(position, BUY_TYPE) else "SELL",
            "order_type": "MARKET",
            "quantity": position_size,
            "price": price,
            "time_in_force": "GTC",
            "position_side": "BOTH",
            "reduce_only": False,
        }

        signal = await FakeSignalGenerator.order_signal(test_mode, **kwargs)
