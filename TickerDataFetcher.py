import asyncio
import utils
from typing import Optional, List
from MarketDataFetcher import SpotAPI, FuturesAPI


class BinanceTicker:
    def __init__(self, api_instance):
        self.api_instance = api_instance

    # Ticker 리스트 전체를 반환.
    async def get_tickers_all(self):
        """
        1. 기능 : Binance의 Ticker리스트 전체를 수신한다.
        2. 매개변수 : 해당없음.
        """
        ticker_data = await self.api_instance.fetch_ticker_price()
        tickers = [data.get("symbol") for data in ticker_data]
        return tickers

    # 특정 Ticker 리스트를 반환.
    async def get_asset_tickers(
        self, coin: Optional[str] = None, quote: Optional[str] = None
    ) -> List[str]:
        """
        1. 기능 : Binance의 coin/quote 값을 지정하여 Ticker리스트를 수신 후 필터 반환한다.
        2. 매개변수
            1) coin : BTC or XRP or ETH ...
            2) Quote : USDT ...
            symbol BTC(coin) / USDT(Quote)
        """
        ticker_data = await self.api_instance.fetch_ticker_price()
        filtered_tickers = set()  # 중복 방지를 위해 set 사용
        for ticker_info in ticker_data:
            symbol = ticker_info.get("symbol")
            if coin and symbol.startswith(coin.upper()):
                filtered_tickers.add(symbol)
            elif quote and symbol.endswith(quote.upper()):
                filtered_tickers.add(symbol)
        return list(filtered_tickers)

    # Tickers의 Base Assets List 반환 (BTC/USDT >> Base/Quote).
    async def get_crypto_assets(self, asset_type: str) -> List:
        """
        1. 기능 : 'Base' 또는 'Quote'에 해당하는 crypto리스트를 반환한다.
        2. 매개변수
            1) asset_type : 'Base' or 'Quote'
                >> 'Base' : BTC/XXX
                >> 'Qutote' : XXX/BTC
        """
        filtered_tickers = set()  # 중복 방지를 위해 set 사용
        exchange_data = await self.api_instance.fetch_exchange_info()

        asset = {"quote": "quoteAsset", "base": "baseAsset"}.get(asset_type.lower())

        if not asset:
            raise ValueError("asset_type를 'quote' 또는 'base'를 입력하시오.")

        for data in exchange_data.get("symbols"):
            base_asset = data.get(asset)
            filtered_tickers.add(base_asset)
        return list(filtered_tickers)

    # 특정 단가 이상 또는 이하에 해당하는 Ticker 반환.
    async def get_tickers_above_price(
        self, target_price: float, comparison: str = "above"
    ) -> List:
        """
        1. 기능 : 특정 현재가 기준 이상 / 이하에 해당하는 Ticker리스트를 반환한다.
        2. 매개변수
            1) target_rpce : 목표단가
            2) comparison : 'above', 'below'
                >> 'above' : 이상
                >> 'below' : 이하
        """
        if comparison not in ["above", "below"]:
            raise ValueError("comparison은 'above' 또는 'below' 중 하나여야 합니다.")

        ticker_data = await self.api_instance.fetch_ticker_price()
        filtered_tickers = set()

        for ticker_info in ticker_data:
            price = float(ticker_info.get("price"))
            if comparison == "above" and target_price <= price:
                filtered_tickers.add(ticker_info.get("symbol"))
            elif comparison == "below" and target_price >= price:
                filtered_tickers.add(ticker_info.get("symbol"))
        return list(filtered_tickers)

    # 특정 거래대금 이상 또는 이하에 해당하는 Ticker 반환.
    async def get_tickers_above_value(
        self, target_value: float, comparison: str = "above"
    ) -> List:
        """
        1. 기능 : 24시간 거래기준하여 특정 거래디금 이상 또는 이하에 해당하는 Ticker리스트를 반환한다.
        2. 매개변수
            1) target_value : 목표 거래대금 (단위 : USD)
            2) comparison : 'above', 'below'
                >> 'above' : 이상
                >> 'below' : 이하
        """
        if comparison not in ["above", "below"]:
            raise ValueError("comparison은 'above' 또는 'below' 중 하나여야 합니다.")
        ticker_data = await self.api_instance.fetch_24hr_ticker()
        filtered_tickers = set()

        for ticker_info in ticker_data:
            value = float(ticker_info.get("quoteVolume"))
            if comparison == "above" and target_value <= value:
                filtered_tickers.add(ticker_info.get("symbol"))
            elif comparison == "below" and target_value >= value:
                filtered_tickers.add(ticker_info.get("symbol"))
        return list(filtered_tickers)

    # Ticker의 변동률을 기준하여 리스트 반환.abs
    async def get_tickers_above_change(
        self, target_percent: float, comparison: str = "above", absolute: bool = False
    ) -> List:
        """
        1. 기능 : 24시간 거래기준하여 특정 변동률 이상 또는 이하에 해당하는 Ticker리스트를 반환한다.
        2. 매개변수
            1) target_percent : 목표 변동률 (단위 : %, 예:) 3.56% -> 3.56 입력
            2) comparison : 'above', 'below'
                >> 'above' : 이상
                >> 'below' : 이하
        """
        ticker_data = await self.api_instance.fetch_24hr_ticker()
        comparison_type = ["above", "below"]

        if not absolute and comparison not in comparison_type:
            raise ValueError(
                "absolute가 'False'일 경우 comparison은 'above' 또는 'below' 중 하나여야 합니다."
            )

        filtered_tickers = set()
        literal_data = utils._collections_to_literal(ticker_data)

        for data in literal_data:
            change_percent = data.get("priceChangePercent")
            symbol = data.get("symbol")

            if absolute:
                change_percent = abs(change_percent)

            if comparison == comparison_type[0] and change_percent >= target_percent:
                filtered_tickers.add(data.get("symbol"))
            elif comparison == comparison_type[1] and change_percent <= target_percent:
                filtered_tickers.add(data.get("symbol"))
        return list(filtered_tickers)


class SpotTickers(BinanceTicker):
    def __init__(self):
        super().__init__(SpotAPI())


class FuturesTickers(BinanceTicker):
    def __init__(self):
        super().__init__(FuturesAPI())


if __name__ == "__main__":
    spot_obj = SpotTickers()
    futures_obj = FuturesTickers()

    spot_tickers_all = asyncio.run(spot_obj.get_tickers_all())
    futures_tickers_all = asyncio.run(futures_obj.get_tickers_all())

    spot_asset_tickers = asyncio.run(spot_obj.get_asset_tickers(quote="USDT"))
    futures_asset_tickers = asyncio.run(futures_obj.get_asset_tickers(quote="USDT"))

    spot_crypto_assets = asyncio.run(spot_obj.get_crypto_assets(asset_type="base"))
    futures_crypto_assets = asyncio.run(
        futures_obj.get_crypto_assets(asset_type="base")
    )

    spot_above_price = asyncio.run(spot_obj.get_tickers_above_price(target_price=50))
    futures_above_price = asyncio.run(
        futures_obj.get_tickers_above_price(target_price=50)
    )

    spot_above_value = asyncio.run(
        spot_obj.get_tickers_above_value(target_value=150_000_000)
    )
    futures_above_value = asyncio.run(
        futures_obj.get_tickers_above_value(target_value=150_000_000)
    )

    spot_above_change = asyncio.run(
        spot_obj.get_tickers_above_change(target_percent=0.05)
    )
    futures_above_change = asyncio.run(
        futures_obj.get_tickers_above_change(target_percent=0.05)
    )
