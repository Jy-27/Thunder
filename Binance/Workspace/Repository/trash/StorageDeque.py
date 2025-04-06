from collections import deque
from typing import Dict, List
import json

import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Abstract.AbstractStorage import AppendStorage

from SystemConfig import Streaming

fields = Streaming.symbols


class StorageDeque(AppendStorage):
    """
    💾 Deque를 활용한 스토리지이며, 기본적으로 데이터 추가 방법을 사용한다.
    """

    __slots__ = tuple(fields + ["max_length"])

    def __init__(self, max_length: int):
        self.max_length = max_length
        self.clear_all()

    def add_data(self, field: str, data: Dict):
        """
        📥 데이터를 추가한다.

        Args:
            field (str): field값
            data (Dict): 저장할 데이터
        """
        return getattr(self, field).append(data)

    def get_data(self, field: str):
        """
        📤 데이터를 불러온다.

        Args:
            field (str): 불러올 속성명

        Returns:
            deque: deque
        """
        return list(getattr(self, field))

    def clear_all(self):
        """
        🧹 전체 field 데이터를 초기화한다.
        """
        for field in self.__class__.__slots__:
            if field in fields:
                setattr(self, field, deque(maxlen=self.max_length))

    def clear_field(self, field: str):
        """
        🧹 지정한 field값을 초기화한다.

        Args:
            field (str): field 명

        Raises:
            ValueError: field명이 없을 시
        """
        if not hasattr(self, fields):
            raise ValueError(f"field 입력 오류: {field}")
        setattr(self, field, deque(maxlen=self.max_length))

    def get_fields(self) -> List:
        """
        🔎 데이터가 저장된 fields값을 반환한다.

        Returns:
            List: 전체 필드명
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

    def __str__(self) -> str:
        """
        🖨️ print( ), str( ) 출력 형태를 대응한다.
        내용은 속성(symbols값 만)에 대한 데이터 길이 값을 출력한다.

        Returns:
            str: 속성당 데이터 길이

        Notes:
            속성에서 symbol이 아닌값은 제외함.

        """
        message = [f"\n{self.__class__.__name__} Data Legnth info\n"]
        for attr in self.__slots__:
            if attr.endswith("USDT"):
                data_length = len(getattr(self, attr))
                message.append(f"  >> {attr}: {data_length}\n")
        return "".join(message)

    def __repr__(self) -> str:
        """
        🖨️ repr( ) 사용시 출력될 내용을 정리한다.

        Returns:
            str: 정렬된 dict 형태 출력
        """
        return str(self.to_dict())

    def __len__(self) -> int:
        """
        📏 속성의 갯수를 출력한다.
        """
        valid_attr = []
        for slot in self.__slots__:
            if slot.endswith("USDT"):
                valid_attr.append(slot)
        return len(valid_attr)


if __name__ == "__main__":
    max_length = 300

    storage_1 = StorageDeque(max_length)
    storage_2 = StorageDeque(max_length)

    storage_1.add_data("BTCUSDT", [1, 2, 3, 4])
    storage_1.add_data("BTCUSDT", [5, 6, 7, 8])
    storage_1.add_data("BTCUSDT", [5, 6, 7, 8])
    storage_1.add_data("BTCUSDT", [5, 6, 7, 8])
    storage_2.add_data("BTCUSDT", ["a", "b", "c", "d"])
    storage_2.add_data("BTCUSDT", ["e", "f", "g", "h"])

    print(storage_1)
    print(storage_2)
