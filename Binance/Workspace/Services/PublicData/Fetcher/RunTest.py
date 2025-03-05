import asyncio
import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "GitHub", "Thunder", "Binance"))

from Workspace.Services.PublicData.Fetcher.FuturesMarketFetcher import (
    FuturesMarketFetcher,
)
from Workspace.Services.PublicData.Fetcher.SpotMarketFetcher import SpotMarketFetcher
from Workspace.Services.PublicData.Fetcher.MarketFetcher import MarketFetcher
import Workspace.Utils.BaseUtils as base_utils

start_time = "2025-03-05 09:00:00"
end_time = "2025-03-05 09:30:00"

start_timestamp = base_utils.convert_to_timestamp_ms(start_time)
end_timestamp = base_utils.convert_to_timestamp_ms(end_time)

ins_futures = FuturesMarketFetcher()
ins_spot = SpotMarketFetcher()

symbol = "BTCUSDT"
interval = "3m"
limit = 10

async def main(instance: MarketFetcher):
    print("    👍 fetch_ticker_price 완료")
    await instance.fetch_ticker_price(symbol)
    print("    👍 fetch_book_tickers 완료")
    await instance.fetch_book_tickers(symbol)
    print("    👍 fetch_24hr_ticker 완료")
    await instance.fetch_24hr_ticker(symbol)
    print("    👍 fetch_klines_limit 완료")
    await instance.fetch_klines_limit(symbol, interval, limit)
    print("    👍 fetch_klines_date 완료")
    await instance.fetch_klines_date(symbol, interval, start_timestamp, end_timestamp)
    print("    👍 fetch_order_book 완료")
    await instance.fetch_order_book(symbol, limit)
    print("    👍 fetch_recent_trades 완료")
    await instance.fetch_recent_trades(symbol, limit)
    print("    👍 fetch_agg_trades 완료")
    await instance.fetch_agg_trades(symbol)
    print("    👍 fetch_agg_trades 완료")
    await instance.fetch_agg_trades(symbol)
    print("    👍 ping_binance 완료")
    await instance.ping_binance()

async def spot_only(instance: SpotMarketFetcher):
    print(f"🚀 SPOT FETCHER TEST!!")
    await main(instance)
    print("    👍 fetch_exchange_info 완료")
    await instance.fetch_exchange_info(symbol)
    print("    👍 fetch_avg_price 완료")
    await instance.fetch_exchange_info(symbol)
    print("    👍 fetch_historical_trades 완료\n")

async def futures_only(instance: FuturesMarketFetcher):
    print(f"🚀 FUTURES FETCHER TEST!!")
    await main(instance)
    await instance.fetch_exchange_info()
    print("    👍 fetch_exchange_info 완료")
    await instance.fetch_mark_price(symbol)
    print("    👍 fetch_mark_price 완료")
    await instance.fetch_funding_rate(symbol, limit)
    print("    👍 fetch_funding_rate 완료")
    await instance.fetch_open_interest(symbol)
    print("    👍 fetch_open_interest 완료\n")

async def start():
    await spot_only(ins_spot)
    await futures_only(ins_futures)

if __name__ == "__main__":
    asyncio.run(start())