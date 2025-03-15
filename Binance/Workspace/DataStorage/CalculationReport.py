from typing import Any, List
import json


class CalculationReport:
    """
    분석용 계산결과를 저장하는 클라스이다.
    지정된 속성값은 없으며, 업데이트대마다 전부 신규로 등록처리한다.
    """
    
    def __init__(self):
        ...
        
    def set_data(self, attr_name:str, data:Any):
        setattr(self, attr_name, data)
    
    def get_data(self, attr_name:str) -> Any:
        if not isinstance(attr_name, str):
            raise ValueError(f"타입 입력 오류: {type(attr_name)}")
        if not hasattr(self, attr_name):
            raise ValueError(f"name 입력 오류: {attr_name}")
            
        return getattr(self, attr_name)
    
    def get_attr_fields(self) -> List:
        return [key for key in vars(self).keys()]
    
    def __str__(self) -> str:
        return json.dumps(vars(self), indent=2)