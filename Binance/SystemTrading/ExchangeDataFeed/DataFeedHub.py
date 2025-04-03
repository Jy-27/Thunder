
"""
fetcher public
fetcher priave
websocekt public
websocket private
"""

from typing import Dict, Optional, List
class ExchangeDataRouter:
    def __init__(self,
                 symbols:List[str],
                 intervals:List[str],
                 api_key:Dict,
                 websocket_timeout:float,
                 listen_key_update_interval:int,
                 
                 queue_feed_fetch_ticker_price: asyncio.Queue,
                 queue_feed_fetch_book_tickers: asyncio.Queue,
                 queue_feed_fetch_24hr_ticker: asyncio.Queue,
                 queue_feed_fetch_kline_limit: asyncio.Queue,
                 queue_feed_fetch_order_book: asyncio.Queue,
                 queue_feed_fetch_recent_trades: asyncio.Queue,
                 queue_feed_fetch_agg_trades: asyncio.Queue,
                 queue_feed_fetch_server_time: asyncio.Queue,
                 queue_feed_fetch_ping_balance: asyncio.Queue,
                 queue_feed_fetch_exchange_info: asyncio.Queue,
                 queue_feed_fetch_mark_price: asyncio.Queue,
                 queue_feed_fetch_funding_rate: asyncio.Queue,
                 queue_feed_fetch_open_interest: asyncio.Queue,
                 
                 queue_feed_fetch_account_balance:asyncio.Queue,
                 queue_feed_fetch_order_status:asyncio.Queue,
                 queue_feed_fetch_leverage_brackets:asyncio.Queue,
                 queue_feed_fetch_order_history:asyncio.Queue,
                 queue_feed_fetch_trade_history:asyncio.Queue,
                 queue_feed_fetch_order_details:asyncio.Queue,
                 
                 queue_feed_websocket_ticker:asyncio.Queue,
                 queue_feed_websocket_trade:asyncio.Queue,
                 queue_feed_websocket_miniTicker:asyncio.Queue,
                 queue_feed_websocket_depth:asyncio.Queue,
                 queue_feed_websocket_aggTrade:asyncio.Queue,
                 queue_feed_websocket_kline:asyncio.Queue,
                 
                 queue_feed_websocket_execution:asyncio.Queue,
                 
                 queue_request_fetch_ticker_price: asyncio.Queue,
                 queue_request_fetch_book_tickers: asyncio.Queue,
                 queue_request_fetch_24hr_ticker: asyncio.Queue,
                 queue_request_fetch_kline_limit: asyncio.Queue,
                 queue_request_fetch_order_book: asyncio.Queue,
                 queue_request_fetch_recent_trades: asyncio.Queue,
                 queue_request_fetch_agg_trades: asyncio.Queue,
                 queue_request_fetch_mark_price: asyncio.Queue,
                 queue_request_fetch_funding_rate: asyncio.Queue,
                 queue_request_fetch_open_interest: asyncio.Queue,
                 
                 queue_request_fetch_order_status:asyncio.Queue,
                 queue_request_fetch_leverage_brackets:asyncio.Queue,
                 queue_request_fetch_order_history:asyncio.Queue,
                 queue_request_fetch_trade_history:asyncio.Queue,
                 queue_request_fetch_order_details:asyncio.Queue,
                 
                 event_trigger_shutdown_loop: asyncio.Event,
                 
                 event_trigger_fetch_server_time: asyncio.Event,
                 event_trigger_fetch_ping_balance: asyncio.Event,
                 event_trigger_fetch_exchange_info: asyncio.Event,
                 
                 event_trigger_fetch_account_balance:asyncio.Event,
                 
                 event_fired_done_fetch_ticker_price: asyncio.Event,
                 event_fired_done_fetch_book_tickers: asyncio.Event,
                 event_fired_done_fetch_ticker_24hr: asyncio.Event,
                 event_fired_done_fetch_kline_limit: asyncio.Event,
                 event_fired_done_fetch_order_book: asyncio.Event,
                 event_fired_done_fetch_recent_trades: asyncio.Event,
                 event_fired_done_fetch_agg_trade: asyncio.Event,
                 event_fired_done_fetch_server_time: asyncio.Event,
                 event_fired_done_fetch_ping_balance: asyncio.Event,
                 event_fired_done_fetch_exchange_info: asyncio.Event,
                 event_fired_done_fetch_mark_price: asyncio.Event,
                 event_fired_done_fetch_funding_rate: asyncio.Event,
                 event_fired_done_fetch_open_interest: asyncio.Event,
                 
                 event_fired_done_account_balance:asyncio.Event,
                 event_fired_done_fetch_order_status:asyncio.Event,
                 event_fired_done_fetch_leverage_brackets:asyncio.Event,
                 event_fired_done_fetch_order_history:asyncio.Event,
                 event_fired_done_fetch_trade_history:asyncio.Event,
                 event_fired_done_fetch_order_details:asyncio.Event,
                 
                 event_fired_done_exectuion_receiver_message:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_fetch_ticker_price:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_book_tickers:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_ticker_24hr:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_kline_limit:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_order_book:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_recent_trades:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_agg_trade:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_server_time:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_ping_balance:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_exchange_info:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_mark_price:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_funding_rate:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_open_interest:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_fetch_account_balance:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_order_status:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_leverage_brackets:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_order_history:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_trade_history:asyncio.Event,
                 event_fired_done_shutdown_loop_fetch_order_details:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_websocket_ticker:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_trade:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_miniTicker:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_depth:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_aggTrade:asyncio.Event,
                 event_fired_done_shutdown_loop_websocket_kline:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_websocket_execution:asyncio.Event,
                 
                 event_fired_done_shutdown_loop_listen_key_cycle:asyncio.Event,
                 
                 event_fired_done_public_rest_fetcher: asyncio.Event,
                 event_fired_done_private_rest_fetcher:asyncio.Event,
                 event_fired_done_public_websocket_hub:asyncio.Event,
                 event_fired_done_execution_receiver_websocket:asyncio.Event):
        
        self.symbols = symbols
        self.intervals = intervals
        self.api_key = api_key
        self.websocket_timeout = websocket_timeout
        self.listen_key_update_interval = listen_key_update_interval
        self.queue_feed_fetch_ticker_price = queue_feed_fetch_ticker_price
        self.queue_feed_fetch_book_tickers = queue_feed_fetch_book_tickers
        self.queue_feed_fetch_24hr_ticker = queue_feed_fetch_24hr_ticker
        self.queue_feed_fetch_kline_limit = queue_feed_fetch_kline_limit
        self.queue_feed_fetch_order_book = queue_feed_fetch_order_book
        self.queue_feed_fetch_recent_trades = queue_feed_fetch_recent_trades
        self.queue_feed_fetch_agg_trades = queue_feed_fetch_agg_trades
        self.queue_feed_fetch_server_time = queue_feed_fetch_server_time
        self.queue_feed_fetch_ping_balance = queue_feed_fetch_ping_balance
        self.queue_feed_fetch_exchange_info = queue_feed_fetch_exchange_info
        self.queue_feed_fetch_mark_price = queue_feed_fetch_mark_price
        self.queue_feed_fetch_funding_rate = queue_feed_fetch_funding_rate
        self.queue_feed_fetch_open_interest = queue_feed_fetch_open_interest
        self.queue_feed_fetch_account_balance = queue_feed_fetch_account_balance
        self.queue_feed_fetch_order_status = queue_feed_fetch_order_status
        self.queue_feed_fetch_leverage_brackets = queue_feed_fetch_leverage_brackets
        self.queue_feed_fetch_order_history = queue_feed_fetch_order_history
        self.queue_feed_fetch_trade_history = queue_feed_fetch_trade_history
        self.queue_feed_fetch_order_details = queue_feed_fetch_order_details
        self.queue_feed_websocket_ticker = queue_feed_websocket_ticker
        self.queue_feed_websocket_trade = queue_feed_websocket_trade
        self.queue_feed_websocket_miniTicker = queue_feed_websocket_miniTicker
        self.queue_feed_websocket_depth = queue_feed_websocket_depth
        self.queue_feed_websocket_aggTrade = queue_feed_websocket_aggTrade
        self.queue_feed_websocket_kline = queue_feed_websocket_kline
        self.queue_feed_websocket_execution = queue_feed_websocket_execution
        self.queue_request_fetch_ticker_price = queue_request_fetch_ticker_price
        self.queue_request_fetch_book_tickers = queue_request_fetch_book_tickers
        self.queue_request_fetch_24hr_ticker = queue_request_fetch_24hr_ticker
        self.queue_request_fetch_kline_limit = queue_request_fetch_kline_limit
        self.queue_request_fetch_order_book = queue_request_fetch_order_book
        self.queue_request_fetch_recent_trades = queue_request_fetch_recent_trades
        self.queue_request_fetch_agg_trades = queue_request_fetch_agg_trades
        self.queue_request_fetch_mark_price = queue_request_fetch_mark_price
        self.queue_request_fetch_funding_rate = queue_request_fetch_funding_rate
        self.queue_request_fetch_open_interest = queue_request_fetch_open_interest
        self.queue_request_fetch_order_status = queue_request_fetch_order_status
        self.queue_request_fetch_leverage_brackets = queue_request_fetch_leverage_brackets
        self.queue_request_fetch_order_history = queue_request_fetch_order_history
        self.queue_request_fetch_trade_history = queue_request_fetch_trade_history
        self.queue_request_fetch_order_details = queue_request_fetch_order_details
        self.event_trigger_shutdown_loop = event_trigger_shutdown_loop
        self.event_trigger_fetch_server_time = event_trigger_fetch_server_time
        self.event_trigger_fetch_ping_balance = event_trigger_fetch_ping_balance
        self.event_trigger_fetch_exchange_info = event_trigger_fetch_exchange_info
        self.event_trigger_fetch_account_balance = event_trigger_fetch_account_balance
        self.event_fired_done_fetch_ticker_price = event_fired_done_fetch_ticker_price
        self.event_fired_done_fetch_book_tickers = event_fired_done_fetch_book_tickers
        self.event_fired_done_fetch_ticker_24hr = event_fired_done_fetch_ticker_24hr
        self.event_fired_done_fetch_kline_limit = event_fired_done_fetch_kline_limit
        self.event_fired_done_fetch_order_book = event_fired_done_fetch_order_book
        self.event_fired_done_fetch_recent_trades = event_fired_done_fetch_recent_trades
        self.event_fired_done_fetch_agg_trade = event_fired_done_fetch_agg_trade
        self.event_fired_done_fetch_server_time = event_fired_done_fetch_server_time
        self.event_fired_done_fetch_ping_balance = event_fired_done_fetch_ping_balance
        self.event_fired_done_fetch_exchange_info = event_fired_done_fetch_exchange_info
        self.event_fired_done_fetch_mark_price = event_fired_done_fetch_mark_price
        self.event_fired_done_fetch_funding_rate = event_fired_done_fetch_funding_rate
        self.event_fired_done_fetch_open_interest = event_fired_done_fetch_open_interest
        self.event_fired_done_account_balance = event_fired_done_account_balance
        self.event_fired_done_fetch_order_status = event_fired_done_fetch_order_status
        self.event_fired_done_fetch_leverage_brackets = event_fired_done_fetch_leverage_brackets
        self.event_fired_done_fetch_order_history = event_fired_done_fetch_order_history
        self.event_fired_done_fetch_trade_history = event_fired_done_fetch_trade_history
        self.event_fired_done_fetch_order_details = event_fired_done_fetch_order_details
        self.event_fired_done_exectuion_receiver_message = event_fired_done_exectuion_receiver_message
        self.event_fired_done_shutdown_loop_fetch_ticker_price = event_fired_done_shutdown_loop_fetch_ticker_price
        self.event_fired_done_shutdown_loop_fetch_book_tickers = event_fired_done_shutdown_loop_fetch_book_tickers
        self.event_fired_done_shutdown_loop_fetch_ticker_24hr = event_fired_done_shutdown_loop_fetch_ticker_24hr
        self.event_fired_done_shutdown_loop_fetch_kline_limit = event_fired_done_shutdown_loop_fetch_kline_limit
        self.event_fired_done_shutdown_loop_fetch_order_book = event_fired_done_shutdown_loop_fetch_order_book
        self.event_fired_done_shutdown_loop_fetch_recent_trades = event_fired_done_shutdown_loop_fetch_recent_trades
        self.event_fired_done_shutdown_loop_fetch_agg_trade = event_fired_done_shutdown_loop_fetch_agg_trade
        self.event_fired_done_shutdown_loop_fetch_server_time = event_fired_done_shutdown_loop_fetch_server_time
        self.event_fired_done_shutdown_loop_fetch_ping_balance = event_fired_done_shutdown_loop_fetch_ping_balance
        self.event_fired_done_shutdown_loop_fetch_exchange_info = event_fired_done_shutdown_loop_fetch_exchange_info
        self.event_fired_done_shutdown_loop_fetch_mark_price = event_fired_done_shutdown_loop_fetch_mark_price
        self.event_fired_done_shutdown_loop_fetch_funding_rate = event_fired_done_shutdown_loop_fetch_funding_rate
        self.event_fired_done_shutdown_loop_fetch_open_interest = event_fired_done_shutdown_loop_fetch_open_interest
        self.event_fired_done_shutdown_loop_fetch_account_balance = event_fired_done_shutdown_loop_fetch_account_balance
        self.event_fired_done_shutdown_loop_fetch_order_status = event_fired_done_shutdown_loop_fetch_order_status
        self.event_fired_done_shutdown_loop_fetch_leverage_brackets = event_fired_done_shutdown_loop_fetch_leverage_brackets
        self.event_fired_done_shutdown_loop_fetch_order_history = event_fired_done_shutdown_loop_fetch_order_history
        self.event_fired_done_shutdown_loop_fetch_trade_history = event_fired_done_shutdown_loop_fetch_trade_history
        self.event_fired_done_shutdown_loop_fetch_order_details = event_fired_done_shutdown_loop_fetch_order_details
        self.event_fired_done_shutdown_loop_websocket_ticker = event_fired_done_shutdown_loop_websocket_ticker
        self.event_fired_done_shutdown_loop_websocket_trade = event_fired_done_shutdown_loop_websocket_trade
        self.event_fired_done_shutdown_loop_websocket_miniTicker = event_fired_done_shutdown_loop_websocket_miniTicker
        self.event_fired_done_shutdown_loop_websocket_depth = event_fired_done_shutdown_loop_websocket_depth
        self.event_fired_done_shutdown_loop_websocket_aggTrade = event_fired_done_shutdown_loop_websocket_aggTrade
        self.event_fired_done_shutdown_loop_websocket_kline = event_fired_done_shutdown_loop_websocket_kline
        self.event_fired_done_shutdown_loop_websocket_execution = event_fired_done_shutdown_loop_websocket_execution
        self.event_fired_done_shutdown_loop_listen_key_cycle = event_fired_done_shutdown_loop_listen_key_cycle
        self.event_fired_done_public_rest_fetcher = event_fired_done_public_rest_fetcher
        self.event_fired_done_private_rest_fetcher = event_fired_done_private_rest_fetcher
        self.event_fired_done_public_websocket_hub = event_fired_done_public_websocket_hub
        self.event_fired_done_execution_receiver_websocket = event_fired_done_execution_receiver_websocket
        
        
        
        
        
        
        
        
        
        
        self.public_rest_fetcher = PublicRestFetcher()
        self.private_rest_fetcher = PrivateRestFetcher()
        self.public_ws_receiver = PublicWebsocketReceiver()
        self.private_ws_receiver = PrivateWebsocketReceiver()
