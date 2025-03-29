from collections import deque
from typing import Dict, List, Any, Optional
from copy import deepcopy

import os, sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Abstract.AbstractStorage import ReplaceStorage

from SystemConfig import Streaming

fields = Streaming.symbols


class StorageOverwrite(ReplaceStorage):
    """
    💾 Deque를 활용한 스토리지이며, 기존 데이터를 새로운 값으로 덮어쓰는 방식(Set/Replace)을 사용한다.
    """
    def __init__(self, base_type: Optional[Any]):
        self.base_type = base_type
        self.clear_all()

    def set_data(self, field: str, data: Dict):
        """
        📥 데이터를 덮어쓴다..

        Args:
            field (str): 필드명
            data (Dict): 저장할 데이터
        """
        return setattr(self, field, data)

    def get_data(self, field: str) -> Any:
        """
        📤 데이터를 불러온다.

        Args:
            field (str): 필드명

        Returns:
            any: 필드에 저장된 데이터
        """
        if not hasattr(self, field):
            raise ValueError(f"field 입력 오류: {field}")
        return getattr(self, field)

    def clear_field(self, field: str):
        """
        🧹 지정한 field를 초기화한다.

        Args:
            field (str): 필드명

        Raises:
            ValueError: 필드명이 없을 시
        """
        if not hasattr(self, field):
            raise ValueError(f"field 입력 오류: {field}")
        setattr(self, field, deepcopy(self.base_type))

    def clear_all(self):
        """
        🧹 전체 필드 데이터를 초기화한다.
        """
        for field in self.__dict__:
            if field in fields:
                setattr(self, field, deepcopy(self.base_type))

    def get_fields(self) -> List:
        """
        🔎 전체 필드명을 반환한다.

        Returns:
            List: 필드명 리스트
        """
        return [field for field in self.__dict__]

    def to_dict(self) -> Dict:
        """
        📑 데이터를 Dictionary형태로 변환하여 반환한다.

        Returns:
            Dict: 속성값 데이터
        """
        result = {}
        for field in self.__dict__:
            if field not in fields:
                continue
            result[field] = getattr(self, field)
        return result

    def __str__(self):
        """
        🖨️ print( ), str( ) 출력 형태를 대응한다.
        내용은 속성(symbols값 만)에 대한 데이터 길이 값을 출력한다.

        Returns:
            str: 속성당 데이터 길이

        Notes:
            속성에서 symbol이 아닌값은 제외함.
        """
        message = [f"\n{self.__dict__} Data Lenght info\n"]
        for attr in self.__dict__:
            if attr.endswith("USDT"):
                data = getattr(self, attr)
                if data is None:
                    data_lenght = 0
                else:
                    data_lenght = len(data)
                message.append(f"  >> {attr}: {data_lenght}\n")
        return "".join(message)

    def __repr__(self):
        """
        🖨️ print함수 사용시 출력될 내용을 정리한다.

        Returns:
            str: 속성값 정보
        """
        return str(self.to_dict())

    def __len__(self) -> int:
        """
        📏 속성의 갯수를 출력한다.
        """
        valid_attr = []
        for slot in self.__dict__:
            if slot.endswith("USDT"):
                valid_attr.append(slot)
        return len(valid_attr)


if __name__ == "__main__":
    base_type_1 = None
    base_type_2 = []

    storage_1 = StorageOverwrite(base_type_1)
    storage_2 = StorageOverwrite(base_type_2)

    storage_1.set_data("BTCUSDT", [1, 2, 3, 4])
    storage_1.set_data("XRPUSDT", [1, 2, 4])
    storage_1.set_data("BTCUSDT", [1, 2, 3, 4])
    storage_2.set_data("BTCUSDT", ["a", "b", "c", "d"])

    print(storage_1)
    print(storage_2)
