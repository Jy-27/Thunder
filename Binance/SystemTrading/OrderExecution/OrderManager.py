import asyncio

class OrderManager:
    def __init__(self,
                 queue_request_result:asyncio.Queue,
                 queue_response_order:asyncio.Queue,
                 queue_feed_order_status:asyncio.Queue,
                 event_feed_stop_loop:asyncio.Event,
                 event_complete_order_signal:asyncio.Event,
                 event_trigger_order:asyncio.Event):
        self.queue_request_result = queue_request_result
        self.queue_response_order = queue_response_order
        self.queue_feed_order_status = queue_feed_order_status
        self.event_feed_stop_loop = event_feed_stop_loop
        self.event_complete_order_signal = event_complete_order_signal
        self.event_trigger_order = event_trigger_order
        
    
    async def create_order(self):
        pass
    
    async def cancel_order(self):
        pass
    
    async def request_orders_data(self):
        pass
    
    async def queue_and_send(self):
        