from typing import Optional, Dict, List, Any
from copy import deepcopy


class SubStorage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """
    def __init__(self, fields:List[str]):
        self.__class__.__slots__ = tuple(fields)
        for field in fields:
            setattr(self, field, [])
    
    def clear_field(self, field:str):
        """
        🧹 지정 필드(속성)값을 초기화 한다.

        Args:
            field (str): 필드명(속성명)

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, field):
            setattr(self, field, [])
        else:
            raise ValueError(f"sub field 입력 오류: {field}")
    
    def clear_all(self):
        """
        🧹 전체 필드(속성)값을 초기화 한다.

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        for field in self.__slots__:
            setattr(self, field, [])
    
    def add_data(self, field:str, data:Any):
        """
        📥 지정 필드(속성)값에 데이터를 추가한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, field):
            getattr(self, field).append(data)

        else:
            raise ValueError(f"field 입력 오류: {field}")
    
    def get_data(self, field:str) -> List[Any]:
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
    
    def set_data(self, field:str, data:List[Any]):
        """
        📥 지정 필드(속성)값에 데이터를 저장(덮어쓰기) 한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if not isinstance(data, list):
            raise ValueError(f"data 타입 입력 오류: {type(data)}")
        
        if hasattr(self, field):
            setattr(self, field, data)
        else:
            raise ValueError(f"field 입력 오류: {field}")


    def get_field(self) -> List[Any]:
        """
        🔍 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        return list(self.__slots__.keys())
    
    
    def to_dict(self) -> Dict:
        """
        📤 전체 필드정보를 Dictionary타입으로 구성하여 반환한다.

        Returns:
            Dict: 필드 저장 데이터
        """
        result = {}
        for field in self.__slots__:
            result[field] = getattr(self, field)
        return result

    def __len__(self):
        """
        🖨️ len() 내장함수 실행시 slots의 개수를 반환한다.

        Returns:
            int: slots의 개수
        """
        return len(self.__slots__)

class MainStroage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """
    def __init__(self, fields:List, sub_storage:SubStorage):
        self.__class__.__slots__ = tuple(fields)
        for field in fields:
            setattr(self, field, deepcopy(sub_storage))
    
    def clear_field(self, main_field:str, sub_field:str):
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

    def clear_all(self, main_field:str):
        """
        🧹 서브 저장소 전체 필드(속성)값을 초기화 한다.

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            main_data.clear_all()
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")

    def add_data(self, main_field:str, sub_field:str, data:Any):
        """
        📥 서브 지정 필드(속성)값에 데이터를 추가한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            if hasattr(main_data, sub_field):
                main_data.add_data(sub_field, data)
            else:
                raise ValueError(f"sub field 입력 오류: {sub_field}")
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")
    
    def get_data(self, main_field:str, sub_field:str) -> List[Any]:
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
    
    def set_data(self, main_field:str, sub_field:str, data:List[Any]):
        """
        📥 서브 지정 필드(속성)값에 데이터를 저장(덮어쓰기) 한다.

        Args:
            field (str): 필드명(속성명)
            data (Any): 추가할 데이터

        Raises:
            ValueError: 필드명(속성명)이 존재하지 않을 때
        """
        if not isinstance(data, list):
            raise ValueError(f"data 타입 입력 오류: {type(data)}")
        
        if hasattr(self, main_field):
            main_data = getattr(self, main_field)
            if hasattr(main_data, sub_field):
                main_data.set_data(sub_field, data)
            else:
                raise ValueError(f"sub field 입력 오류: {sub_field}")
        else:
            raise ValueError(f"main field 입력 오류: {main_field}")

    def get_main_field(self) -> List[str]:
        """
        🔍 메인 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        return list(self.__slots__.keys())
    
    def get_sub_field(self) -> List[str]:
        """
        🔍 서브 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        main_fields = self.get_main_field()
        return getattr(self, main_fields[0]).get_field()

    def to_dict(self) -> Dict:
        """
        📤 MainStorage와 SubStorage 전체 필드정보를 Dictionary타입으로 구성하여 반환한다.

        Returns:
            Dict: 필드 저장 데이터
        """
        result = {}
        for field in self.__slots__:
            result[field] = getattr(self, field).to_dict()
        return result
        
        
    def __len__(self):
        """
        🖨️ len() 실행 시 MainStorage와 SubStorage의 전체 slots개수를 반환한다.

        Returns:
            int: 데이터 개수
        """
        return sum(len(getattr(self, field)) for field in self.__slots__)
    
    
if __name__ == "__main__":
    import os
    import sys
    home_path = os.path.expanduser("~")
    sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))
    
    import SystemConfig
    from pprint import pprint
    
    sub_fields = [f"interval_{i}" for i in SystemConfig.Streaming.intervals]
    sub_storage = SubStorage(sub_fields)
    
    main_fields = SystemConfig.Streaming.symbols
    main_storage = MainStroage(main_fields, sub_storage)
    
    to_dict = main_storage.to_dict()
    pprint(to_dict)