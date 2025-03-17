from collections import deque
from typing import Dict, List

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming
fields = Streaming.symbols

class StorageOverwrite:
    __slots__ = tuple(fields)

    def __init__(self):
        self.clear_all()

    def set_data(self, field:str, data:Dict):
        """
        📥 데이터를 덮어쓴다..

        Args:
            field (str): field값
            data (Dict): 저장할 데이터
        """
        return setattr(self, field, data)

    def get_data(self, field:str):
        """
        📤 데이터를 불러온다.

        Args:
            field (str): 불러올 속성명

        Returns:
            deque: deque
        """
        return list(getattr(self, field))

    def clear_field(self, field:str):
        """
        🧹 지정한 field값을 초기화한다.

        Args:
            field (str): field 명

        Raises:
            ValueError: field명이 없을 시
        """
        if not hasattr(self, field):
            raise ValueError(f"field 입력 오류: {field}")
        setattr(self, field, [])

    def clear_all(self):
        """
        🧹 전체 field 데이터를 초기화한다.
        """
        for field in self.__class__.__slots__:
            if field in fields:
                setattr(self, field, [])

    def get_fields(self) -> List:
        """
        🔎 데이터가 저장된 fields값을 반환한다.

        Returns:
            List: _description_
        """
        return [field for field in self.__class__.__slots__ if field in fields]

    def to_dict(self) -> Dict:
        """
        📑 데이터를 Dictionary형태로 변환하여 반환한다.

        Returns:
            Dict: 속성값 데이터
        """
        result = {}
        for field in self.__class__.__slots__:
            if field not in fields:
                continue
            result[field] = list(getattr(self, field))
        return result

    def __repr__(self):
        """
        🖨️ print함수 사용시 출력될 내용을 정리한다.

        Returns:
            str: 속성값 정보
        """
        return str(self.to_dict())

if __name__ == "__main__":
    storage_1 = StorageDeque()
    storage_2 = StorageDeque()
    
    storage_1.set_data("BTCUSDT", [1,2,3,4])
    storage_2.set_data("BTCUSDT", ["a","b","c","d"])
    
    print(storage_1)
    print(storage_2)
    