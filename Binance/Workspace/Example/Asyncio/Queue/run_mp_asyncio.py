import asyncio
import os
import sys
import multiprocessing

# 홈 디렉토리의 GitHub 프로젝트 경로를 시스템 경로에 추가
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance", "Workspace"))

class AsyncQueueProcessor:
    """
    asyncio 함수와 multiprocessing Queue 간 통신 방식 예제.
    
    1. multiprocessing.Queue를 이용하여 프로세스 간 신호를 전달.
    2. queue.get()을 호출하면 새로운 데이터가 입력될 때까지 블로킹 상태 유지.
    3. 새로운 데이터가 입력되면, 대기 상태에서 깨어나 처리 후 다음 신호를 큐에 삽입.
    4. queue.task_done()은 사용하지 않음.

    ✅ 각 함수는 신호를 대기하고 있다가 새로운 이벤트가 발생하면 처리하는 독립적인 구조를 가짐.
    ✅ 연속적인 함수 호출이 아닌, 개별 함수가 독립적으로 실행되어 이벤트 기반 방식으로 동작.
    """
    
    def __init__(self):
        """
        클래스 초기화: 프로세스 간 통신을 위한 큐 생성 및 초기 데이터 설정.
        """
        self.signal_queue_1 = multiprocessing.Manager().Queue()  # 첫 번째 신호 큐
        self.signal_queue_2 = multiprocessing.Manager().Queue()  # 두 번째 신호 큐
        self.signal_queue_3 = multiprocessing.Manager().Queue()  # 세 번째 신호 큐
        self.signal_queue_4 = multiprocessing.Manager().Queue()  # 네 번째 신호 큐
        self.shared_data = 1  # 공유 데이터 (이벤트 발생 시 연산될 값)
        self.loop = None  # asyncio 루프 저장 변수
    
    async def event_generator(self):
        """
        [비동기 함수] 일정 시간마다 첫 번째 신호 큐에 이벤트를 발생시키는 함수.
        1. 5초 간격으로 queue에 True 값을 삽입하여 run_2()의 대기를 해제.
        2. 10회 반복 후 종료.
        """
        self.loop = asyncio.get_running_loop()
        for _ in range(10):
            self.signal_queue_1.put(True)  # 첫 번째 이벤트 트리거
            print(f"Event Generator Triggered: {self.shared_data}")
            await asyncio.sleep(5)  # 5초 대기 후 다음 이벤트 생성
    
    async def process_signal_1(self):
        """
        [비동기 함수] 첫 번째 큐에서 신호를 대기하고 처리하는 함수.
        1. queue.get()을 통해 데이터가 들어올 때까지 블로킹 상태 유지.
        2. 신호를 받으면 shared_data 값을 증가시키고, 두 번째 큐에 신호 전달.
        """
        while True:
            await self.loop.run_in_executor(None, self.signal_queue_1.get)  # 신호 대기 (CPU 사용 없음)
            self.shared_data += 1
            print(f"Process Signal 1: {self.shared_data}")
            self.signal_queue_2.put(True)  # 다음 신호 전달
    
    async def process_signal_2(self):
        """
        [비동기 함수] 두 번째 큐에서 신호를 대기하고 처리하는 함수.
        1. queue.get()을 통해 데이터가 들어올 때까지 블로킹 상태 유지.
        2. 신호를 받으면 shared_data 값을 증가시키고, 세 번째 큐에 신호 전달.
        """
        while True:
            await self.loop.run_in_executor(None, self.signal_queue_2.get)
            self.shared_data += 1
            print(f"Process Signal 2: {self.shared_data}")
            self.signal_queue_3.put(True)  # 다음 신호 전달
    
    async def process_signal_3(self):
        """
        [비동기 함수] 세 번째 큐에서 신호를 대기하고 처리하는 함수.
        1. queue.get()을 통해 데이터가 들어올 때까지 블로킹 상태 유지.
        2. 신호를 받으면 shared_data 값을 증가시킴.
        """
        while True:
            await self.loop.run_in_executor(None, self.signal_queue_3.get)
            self.shared_data += 1
            print(f"Process Signal 3: {self.shared_data}")
    
    async def start_processing(self):
        """
        [비동기 함수] 모든 작업을 실행하는 메인 함수.
        1. asyncio 루프를 초기화.
        2. 4개의 비동기 작업을 실행하여 병렬적으로 이벤트 처리.
        """
        task1 = asyncio.create_task(self.event_generator())
        task2 = asyncio.create_task(self.process_signal_1())
        task3 = asyncio.create_task(self.process_signal_2())
        task4 = asyncio.create_task(self.process_signal_3())
        
        await asyncio.gather(task1, task2, task3, task4)  # 모든 작업 병렬 실행

if __name__ == "__main__":
    """
    메인 실행 부분:
    1. AsyncQueueProcessor 인스턴스를 생성.
    2. asyncio.run()을 통해 비동기 루프 시작.
    """
    processor = AsyncQueueProcessor()
    asyncio.run(processor.start_processing())
