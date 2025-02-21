from typing import Optional, Dict, List, Any
from dataclasses import dataclass
import os
import sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from typing import List, Any
from copy import deepcopy


class SubStorage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """
    def __init__(self, fields:List[str]):
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
        for field in self.__dict__:
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
        return list(self.__dict__.keys())
    
    def __repr__(self):
        """
        🖨️ print 함수 사용시 속성값을 출력한다.

        Returns:
            str: 필드값 전체
        """
        result = {}
        for field in self.__dict__:
            result[field] = getattr(self, field)
        return str(result)


class MainStroage:
    """
    💾 메인 저장소의 field에 저장될 보조 저장소다.
    Node Tree를 구현하기 위함이다.
    """
    def __init__(self, fields:List, sub_storage:SubStorage):
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
        return list(self.__dict__.keys())
    
    def get_sub_field(self) -> List[str]:
        """
        🔍 서브 저장소의 필드명(속성명)을 반환한다.

        Returns:
            List[str]: 메인 필드명
        """
        main_fields = self.get_main_field()
        return getattr(self, main_fields[0]).get_field()
    
    
    def __repr__(self):
        """
        🖨️ print 함수 사용시 속성값을 출력한다.

        Returns:
            str: 필드값 전체
        """
        result = {}
        for main_field in self.__dict__:
            result[main_field] = {}
            main_data = getattr(self, main_field)
            for sub_field in main_data.__dict__:
                result[main_field][sub_field] = getattr(main_data, sub_field)
        return str(result)