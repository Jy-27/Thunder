import ConfigSetting
import TradeClient


from typing import Optional, Union

class Leverage:
    def __init__(self):
        self.market = ConfigSetting.SymbolConfig.market_type.value
        self.ins_trade_client:Optional[Union[TradeClient.FuturesClient, TradeClient.SpotClient]] = None
        
        self.__init_setting()
        
    def __init_setting(self):
        self.ins_trade_client = {'Futures':TradeClient.FuturesClient(),
                                 'Spot':TradeClient.SpotClient()}.get(self.market, None)
        if self.ins_trade_client is None:
            raise ValueError(f'Market 설정 오류: {self.market}')
    ...
    def get_max_leverage(self, symbol:str):
        if self.market == "Spot":
            return 1
    ...
    
    def get_min_leverage(self, symbol:str):
        if self.market == "Spot":
            return 1
    ...
    
    def set_leverage(self, symbol:str, leverage:int):
        if self.market == "Spot":
            return
        
        
#     ...

# class Quantity:
#     def __init__(self):
#         ...
#     def get_max_quantity(self, symbol: str, leverage:int, balance:float):
    
    
#     def get_min_quantity(self, symbol: str, ):


# class MarginType:
#     ...

if __name__ == "__main__":
    obj = Leverage()
    print(vars(obj))