import asyncio
import TradingDataManager
import nest_asyncio
import utils

obj = TradingDataManager.FuturesDataControl()
obj.active_tickers=['BTCUSDT']
async def main():
    interval = ['kline_3m']
    # task_1 = asyncio.create_task(obj.ticker_update_loop())
    task_2 = asyncio.create_task(obj.connect_kline_loop(interval))
    task_3 = asyncio.create_task(obj.collect_kline_by_interval_loop())
    task_3 = asyncio.create_task(obj.process_kline_data_loop())
    task_4 = asyncio.create_task(obj.debug_status_loop())
    await asyncio.gather(task_2, task_3, task_4)
    
asyncio.run(main())