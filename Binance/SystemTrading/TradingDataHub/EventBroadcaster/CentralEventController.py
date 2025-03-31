import asyncio

class CentralEventController:
    def __init__(self, event_a: asyncio.Event, event_b: asyncio.Event, event_stop: asyncio.Event, event_queue: asyncio.Queue):
        self.event_queue = event_queue
        self.event_a = event_a
        self.event_b = event_b
        self.event_stop = event_stop

    async def handle_order_events(self):
        message = "TEST MESSAGE"
        while not self.event_stop.is_set():
            done, pending = await asyncio.wait(
                [self.event_a.wait(), self.event_b.wait()],
                timeout=0.5,
                return_when=asyncio.ALL_COMPLETED
            )
            if len(done) == 2:
                await self.event_queue.put(message)
                self.event_a.clear()
                self.event_b.clear()

    async def run(self):
        await asyncio.gather(
            asyncio.create_task(self.handle_event_flow())
        )

if __name__ == "__main__":
    event_a = asyncio.Event()
    event_b = asyncio.Event()
    event_stop = asyncio.Event()
    event_queue = asyncio.Queue()

    controller = CentralEventController(event_a, event_b, event_stop, event_queue)
    asyncio.run(controller.run())
