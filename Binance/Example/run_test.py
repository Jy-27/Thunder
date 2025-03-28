import asyncio

class TestLoop:
    def __init__(self, timesleep:int):
        self.timesleep = timesleep
        self.event_stop_loop = asyncio.Event()
    
    async def timer(self):
        await asyncio.sleep(self.timesleep)
        print(f"  시간 종료")
        self.event_stop_loop.set()
        print(f"  event 활성화 완료")
    
    async def loop_1(self):
        n = 0
        while not self.event_stop_loop.is_set():
            await asyncio.sleep(1)
            print(f"  Loop_1: {n}회차 ")
            n += 1
        print(f"  Loop1 종료")
        
    async def loop_2(self):
        i = 0
        while not self.event_stop_loop.is_set():
            await asyncio.sleep(2)
            print(f"  Loop_2: {i}회차 ")
            i += 1
        print(f"  Loop2 종료")
    
    async def  main(self):
        tasks = [
            asyncio.create_task(self.timer()),
            asyncio.create_task(self.loop_1()),
            asyncio.create_task(self.loop_2())
        ]
        print(f"  AsyncioGather 실행")
        await asyncio.gather(*tasks)
        print(f"  AsyncioGather 종료")
        # asyncio.get_event_loop().close()
        # print(f"  asyncio loop 완전 종료됨")
        
if __name__ == "__main__":
    instance = TestLoop(10)
    asyncio.run(instance.main())
                