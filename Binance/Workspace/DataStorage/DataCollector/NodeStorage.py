from typing import Optional, Dict, List, Any
from copy import deepcopy

class SubStorage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """

    def __new__(cls, fields: List[str]):
        """
        동적으로 __slots__이 설정된 클래스를 생성하고 반환.
        """
        new_cls = type(cls.__name__, (cls,), {"__slots__": tuple(fields)})
        instance = super().__new__(new_cls)
        instance._fields = fields  # deepcopy 시 사용하기 위한 내부 변수
        return instance

    def __init__(self, fields: List[str]):
        """
        각 인스턴스가 독립적인 필드를 가지도록 초기화.
        """
        for field in fields:
            setattr(self, field, None)

    def __deepcopy__(self, memo):
        """
        deepcopy 지원: 새 인스턴스를 만들고 기존 값들을 복사.
        """
        new_copy = SubStorage(self._fields)  # 새로운 인스턴스 생성
        for field in self._fields:
            setattr(new_copy, field, deepcopy(getattr(self, field), memo))
        return new_copy

    def clear_field(self, field: str):
        """
        🧹 지정 필드(속성)값을 초기화 한다.

        Args:
            field (str): 필드명(속성명)

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, field):
            setattr(self, field, None)
        else:
            raise ValueError(f"sub field 입력 오류: {field}")

    def clear_all(self):
        """
        🧹 전체 필드(속성)값을 초기화 한다.

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        for field in self.__slots__:
            setattr(self, field, None)

    def get_data(self, field: str) -> Any:
        """
        📤 지정 필드(속성)값을 반환한다.

        Args:
            field (str): 필드명(속성명)

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때

        Returns:
            List[Any]: 필드 저장 데이터
        """
        if hasattr(self, field):
            return getattr(self, field)
        else:
            raise ValueError(f"field 입력 오류: {field}")

    def set_data(self, field: str, data: Any):
        """
        📥 지정 필드(속성)값에 데이터를 저장(덮어쓰기) 한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, field):
            setattr(self, field, data)
        else:
            raise ValueError(f"field 입력 오류: {field}")

    def get_fields(self) -> List[str]:
        """
        🔍 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        return list(self.__slots__)

    def to_dict(self) -> Dict:
        """
        📤 전체 필드정보를 Dictionary타입으로 구성하여 반환한다.

        Returns:
            Dict: 필드 저장 데이터
        """
        return {field: getattr(self, field) for field in self.__slots__}

    def __str__(self):
        """
        🖨️ 전체적인 필드에 대한 정보를 출력한다.

        Returns:
            str: 전체 필드 출력
        """
        return str(self.to_dict())

    def __len__(self):
        """
        🖨️ len() 내장함수 실행시 slots의 개수를 반환한다.

        Returns:
            int: slots의 개수
        """
        return len(self.__slots__)


class MainStorage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """

    def __new__(cls, fields: List[str], sub_storage: SubStorage):
        """
        동적으로 __slots__을 설정하고, SubStorage를 저장하는 구조.
        """
        new_cls = type(cls.__name__, (cls,), {"__slots__": tuple(fields)})
        instance = super().__new__(new_cls)
        instance._fields = fields
        return instance

    def __init__(self, fields: List[str], sub_storage: SubStorage):
        for field in fields:
            setattr(self, field, deepcopy(sub_storage))

    def clear_field(self, main_field: str, sub_field: str):
        """
        🧹 서브 저장소 지정 필드(속성)값을 초기화 한다.

        Args:
            field (str): 필드명(속성명)

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            if hasattr(main_data, sub_field):
                main_data.clear_field(sub_field)

    def clear_all(self, main_field: str):
        """
        🧹 서브 저장소 전체 필드(속성)값을 초기화 한다.

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, main_field):
            getattr(self, main_field).clear_all()
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")

    def set_data(self, main_field: str, sub_field:str, data:Any):
        """
        📥 서브 지정 필드(속성)값에 데이터를 저장(덮어쓰기) 한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            if hasattr(main_data, sub_field):
                main_data.set_data(sub_field, data)
            else:
                raise ValueError(f"sub field 입력 오류: {sub_field}")
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")


    def get_data(self, main_field: str, sub_field: str) -> Any:
        """
        📤 서브 지정 필드(속성)값을 반환한다.

        Args:
            field (str): 필드명(속성명)

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때

        Returns:
            List[Any]: 필드 저장 데이터
        """
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            if hasattr(main_data, sub_field):
                return main_data.get_data(sub_field)
            else:
                raise ValueError(f"sub field 입력 오류: {sub_field}")
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")

    def get_fields(self) -> List[str]:
        """
        🔍 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        return list(self.__slots__)

    def to_dict(self, main_field:str) -> Dict:
        """
        📤 MainStorage와 SubStorage 지정 필드정보를 Dictionary타입으로 구성하여 반환한다.

        Returns:
            Dict: 필드 저장 데이터
        """
        return getattr(self, main_field).to_dict()

    def __str__(self):
        """
        🖨️ 전체적인 필드(하위 포함)에 대한 정보를 출력한다.

        Returns:
            str: 전체 필드 출력
        """
        return str(self.to_dict())


if __name__ == "__main__":
    import os
    import sys
    from pprint import pprint

    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    import asyncio
    import SystemConfig
    import Workspace.Receiver.Futures.Public.KlineCycleFetcher as kline_cycle
    import time
    sub_fields_intervals = [f"interval_{i}" for i in SystemConfig.Streaming.intervals]
    sub_fields_order_type = ["MARKET", "LIMIT", "TAKE_PROFIT", "STOP_MARKET", "TAKE_PROFIT_MARKET"]
    


    # ✅ 서브 저장소 생성
    sub_fields = [f"interval_{i}" for i in SystemConfig.Streaming.intervals]
    sub_storage = SubStorage(sub_fields)

    # ✅ 메인 저장소 생성
    main_fields = SystemConfig.Streaming.symbols
    main_storage = MainStorage(main_fields, sub_storage)

    dummy_queue = asyncio.Queue()
    obj = kline_cycle.KlineCycleFetcher(dummy_queue)
    
    async def main():
        print(f"  🚀 kline_data 수신 시작")
        start_time = time.time()
        for symbol in SystemConfig.Streaming.symbols:
            for interval in SystemConfig.Streaming.intervals:
                await obj.fetch_and_enqueue(symbol, interval)
                data = await dummy_queue.get()
                conver_to_interval = f"interval_{interval}"
                main_storage.set_data(symbol, conver_to_interval, data)
        end_time = time.time()
        print(f"  ✅ kline_data 수신 완료")
        diff_time = end_time - start_time
        print(f"  ⏱️ 소요시간: {diff_time:,.2f} sec")

    asyncio.run(main())
    # ✅ 데이터 확인
