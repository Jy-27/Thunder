from abc import ABC, abstractmethod
from typing import Dict


class Setting(ABC):
    @classmethod
    @abstractmethod
    def set_leveraege(cls, symbol:str, leverage:int) -> Dict:
        """
        레버리지 값을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            leverage (int): 지정하려는 레버리지 값
            
        Return:
            Dict: 레버리지 설정값 피드백
        """
        pass
    
    @classmethod
    @abstractmethod
    def set_margin_type(cls, symbol:str, margin_type:str) -> Dict:
        """
        마진 타입을 설정한다.

        Args:
            symbol (str): 'BTCUSDT'
            margin_type (str): 지정하는 마진 타입

        Returns:
            Dict: 설정상태 피드백
        """
        pass