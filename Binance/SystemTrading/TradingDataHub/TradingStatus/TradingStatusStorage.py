import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

class TradingStatus:
    def __init__(self, queue):
        self.storage = None
        self.queue_feed_wallet = None
        self.queue_request_wallet = None
        self.queue_response_wallet = None
        
        self.event_trigger_stop_loop = None
        self.event_trigger_trading_status = None
        
        self.event_fired_done_trading_status = None