import numpy as np

import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from SystemConfig import Streaming

base_interval = "1m"
config_intervals = Streaming.intervals
config_intervals.insert(0, base_interval) if base_interval not in config_intervals else config_intervals
convert_to_intervals = [f"interval_{interval}" for interval in config_intervals]

class ClosingSyncStorage:
    """
    ClosingSyncDataset를 저장하는 저장소다.

    Returns:
        _type_: _description_
    """
    __slots__ = tuple(convert_to_intervals)
    
    def __init__(self):
        self.clear()
    
    def __convert_to_interval(self, interval:str):
        return f"interval_{interval}"
    
    def set_data(self, interval:str, dataset:np.ndarray):
        str_interval = self.__convert_to_interval(interval)
        setattr(self, str_interval, dataset)
    
    def get_data(self, interval:str, indices:np.ndarray):
        str_interval = self.__convert_to_interval(interval)
        return getattr(self, str_interval)[indices]
    
    def clear(self):
        for attr in self.__slots__:
            setattr(self, attr, [])

class IndicesStorage:
    """
    Closing Sync Storage에 적용될 indices값을 저장하는 저장소다.

    Returns:
        _type_: _description_
    """
    __slots__ = tuple(convert_to_intervals)
    
    def __init__(self):
        self.clear()
    
    def __convert_to_interval(self, interval:str):
        return f"interval_{interval}"
    
    def set_data(self, interval:str, indices:np.ndarray):
        str_interval = self.__convert_to_interval(interval)
        setattr(self, str_interval, indices)
    
    def get_data(self, interval:str, index:int):
        str_interval = self.__convert_to_interval(interval)
        return getattr(self, str_interval)[index]
    
    def clear(self):
        for attr in self.__slots__:
            setattr(self, attr, [])