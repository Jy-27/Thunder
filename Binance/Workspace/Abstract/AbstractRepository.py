from abc import ABC, abstractmethod
from typing import Any

class BaseRepository(ABC):
    """
    Storage에 사용될 추상메소드 항목
    """
    @abstractmethod
    def get_data(self, field: str):
        """
        📤 저장된 데이터를 불러온다.
        """
        pass
    
    @abstractmethod
    def clear_field(self, field: str):
        """
        🧹 특정 필드를 삭제한다.

        Args:
            field (str): 필드명
        """
        pass
    
    @abstractmethod
    def clear_all(self):
        """
        🧹 전체 필드를 삭제한다.
        """
        pass
    
    @abstractmethod
    def get_fields(self):
        """
        🔎 전체 필드명을 반환한다.
        """
        pass
    
    @abstractmethod
    def to_dict(self):
        """
        📑 fields데이터를 Dict형태로 변환 및 반환한다.
        """
        pass
    
    @abstractmethod
    def __str__(self):
        """
        🖨️ print( ), str( ) 출력 형태를 구성한다.
        """
        pass
    
    @abstractmethod
    def __repr__(self):
        """
        🖨️ repr( ) 출력 형태를 구성한다.
        """
        # return json.dumps(vars(self), indent=2)
        pass
    
    @abstractmethod
    def __len__(self):
        """
        📏 len(  ) 출력 형태를 구성한다.
        """


class AppendRepository(BaseRepository):
    @abstractmethod
    def add_data(self, field: str, data: Any):
        """
        📥 field에 데이터를 추가한다.

        Args:
            field (str): 필드명
            data (Any): 저장할 데이터
        """
        pass

class ReplaceRepository(BaseRepository):
    @abstractmethod
    def set_data(self, field: str, data: Any):
        """
        📥 field에 데이터를 덮어쓴다.

        Args:
            field (str): 필드명
            data (Any): 저장할 데이터
        """
        pass
