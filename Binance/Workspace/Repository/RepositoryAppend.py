from typing import Any

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Abstract.AbstractRepository import ReplaceRepository

class RepositoryAppend(ReplaceRepository):
    """
    💾 저장용으로 사용할 스토리지로써 Dict 자료형을 클라스화 한 것이다.
    """
    def __init__(self):
        pass
    
    def set_data(self, field:str, data:Any):
        """
        📥 데이터를 덮어쓴다..

        Args:
            field (str): 필드명
            data (Dict): 저장할 데이터
        """
        setattr(self, field, data)
        
    def get_data(self, field:str) -> Any:
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
    
    def clear_field(self, field:str):
        """
        🧹 지정한 field를 삭제한다.

        Args:
            field (str): 필드명

        Raises:
            ValueError: 필드명이 없을 시
        """
        if not hasattr(self, field):
            raise ValueError(f"field 입력 오류: {field}")
        delattr(self, field)
        
    def clear_all(self):
        """
        🧹 전체 필드 데이터를 삭제한다.
        """
        for attr in self.__dict__:
            delattr(self, attr)
    
    def get_fields(self):
        """
        🔎 전체 필드명을 반환한다.

        Returns:
            List: 필드명 리스트
        """
        return [field for field in self.__dict__]
    
    def to_dict(self):
        """
        📑 데이터를 Dictionary형태로 변환하여 반환한다.

        Returns:
            Dict: 속성값 데이터
        """
        result = {}
        for field in self.__dict__:
            result[field] = getattr(self, field)
        return result
    
    def __str__(self):
        """
        🖨️ print( ), str( ) 출력 형태를 대응한다.
        내용은 속성(symbols값 만)에 대한 데이터 길이 값을 출력한다.

        Returns:
            str: 속성당 데이터 길이
        """
        message = [f"\n{self.__class__.__name__} Data info\n"]
        for attr in self.__dict__:
            data = getattr(self, attr)
            if data is None:
                data_lenght = 0
            else:
                data_lenght = len(data)
            message.append(f"  >> {attr} type : {type(data)}\n")
            message.append(f"  >> {attr} len  : {data_lenght}\n")
        return "".join(message)
    
    def __repr__(self):
        """
        🖨️ print함수 사용시 출력될 내용을 정리한다.

        Returns:
            str: 속성값 정보
        """
        return str(self.to_dict())
    
    def __len__(self):
        """
        📏 속성의 갯수를 출력한다.
        """
        return len(self.__dict__)
    
if __name__ == "__main__":
    dummy_data = {"a":[12,2,14], "b":["a","b","C"]}
    
    storage = StorageRecorder()
    storage.set_data("test", dummy_data)
    print(storage)
    