from typing import List, Dict, Optional, Any, Union
from DataStoreage import *
from ConfigSetting import SystemConfig, InitialSetup, SymbolConfig, SafetyConfig
import os
import utils
import asyncio
import requests
import TradeClient
from datetime import datetime, timedelta
import importlib
from DataStoreage import TradingLog
import numpy as np

class OpenTradeLog:
    """
    현재 보유중인 포지션 정보를 임시 저장한다.
    속성명은 {symbol}_{position}으로 한다.
    """

class WalletManager:
    """
    반복적인 API를 피하기 위하여 wallet정보를 별도 관리한다.
    실제 거래시 슬리피지와 같은 계산하기 어려운 항목들은 exit_fee로 합산한다.
    """
    def __init__(self, initial_balance: float = 1_000, start_ago_hr: int = 24):
        self.trade_history: List[TradingLog] = []
        self.closed_positions: List[List[int]] = []
        self.open_positions: List[List[int]] = []
        self.number_of_stocks: int = 0
        self.initial_balance: float = initial_balance  # 초기 자산
        self.total_wallet_balance: float = 0  # 총 평가 자산
        self.active_value: float = 0  # 거래 중 자산 가치
        self.available_balance: float = 0  # 사용 가능한 예수금
        self.profit_loss: float = 0  # 손익 금액
        self.profit_loss_ratio: float = 0  # 손익률
        self.profit_preservation_balance:float = 0 #수익금 보존금액
        self.profit_preservation_ratio :float = 0 #수익금 보존 비율
        self.trade_count: int = 0  # 총 체결 횟수

        ### instance
        self.__ins_client_futures:TradeClient.FuturesClient = TradeClient.FuturesClient()
        self.__ins_client_spot:TradeClient.SpotClient = TradeClient.SpotClient()
        self.__ins_telegram:TelegramMessage = TelegramMessage()
        ### system setting
        self.start_ago_hr = start_ago_hr
        # 24시간 전 타임스템프를 확보한다.
        self.__start_timestamp: int = int(
            (datetime.now() - timedelta(hours=24)).timestamp() * 1_000
        )

    def __get_path(self) -> str:
        """
        트레이드 히스토리 파일 주소를 반환한다.
        ConfigSetting.py에 지정된 값에 의하여 Test ver, Live Ver 주소를
        획득하여 반환처리한다.

        ConfigSetting.InitialSetup.mode 설정값을 적용한다.
        """
        file_names = {
            True: SystemConfig.test_trade_history.value,
            False: SystemConfig.live_trade_history.value,
        }
        
        file_name:Optional[bool] = file_names.get(InitialSetup.mode)
        if file_name is None:
            raise ValueError(f'mode 설정 오류')
        
        path = os.path.join(
            SystemConfig.parent_folder_path.value,
            SystemConfig.data_folder_name.value,
            file_name,
        )
        return path

    def __get_attr_list(self):
        """
        OpenTradeLog 클라스의 속성이름을 확보한다.
        확보된 이름을 활용하여 getattr로 활용하기 위함이다.
        """
        getattr
        names = []
        for name in vars(OpenTradeLog):
            if "__" not in name:
                names.append(name)
        return names

    def __sum_position(self):
        """
        진행중인 포지션과 종료된 포지션 데이터를 합친 후 값을 반환한다.
        np.ndarry화 하기 위한 데이터 병합이 목적이다.
        각 평가할 값들이 본 데이터가 필요하므로 함수로 만들었다.
        """

        return self.closed_positions + self.open_positions

    def __extract_values(self, data: TradingLog) -> List:
        """
        트레이딩 로그 데이터에서 필요한 부분만 추출한다.
        추출한 데이터는 open or closed 포지션 데이터에 저장한다.
        np.ndarray화 후 백터연산을 위하여 symbol값을 10진수로 변환하였다.
        """
        symbol_decimal = utils._text_to_decimal(data.symbol)
        initial_value = data.initial_value
        position = data.position
        quantity = data.quantity
        net_pnl = data.net_pnl
        entry_fee = data.entry_fee
        exit_fee = data.exit_fee
        return [
            symbol_decimal,
            initial_value,
            position,
            quantity,
            net_pnl,
            entry_fee,
            exit_fee,
        ]

    def __trade_history_save(self):
        """
        트레이드 히스토리 데이터를 저장한다.
        저장할 데이터(self.trade_history)가 없으면 함수를 종료한다.
        """
        # Trade History가 비어있으면
        if not self.trade_history:
            # 함수를 종료한다.
            return

        # 주소를 확보한다.
        path = self.__get_path()
        # 변환이 완료된 데이터를 json데이터로 저장한다.
        utils._save_to_json(path, self.trade_history)

    def __trade_history_load(self):
        """
        저장된 Dict타입의 트레이드 히스토리를 불러온 후 속성값에 저장한다.
        본 클라스는 과거 데이터의 영향을 받는 함수가 있으므로 거래 기록이 필요하다.

        본 함수는 ConfigSetting.py의 지정값에 영향을 받는다.

        업데이트 항목
            1. self.trade_history
            2. self.close_position
        """
        # 주소를 확보한다.
        path = self.__get_path()
        # 파일 존재 유무를 확인한다.
        if not os.path.isfile(path):
            # 파일이 없으면 함수를 종료한다.
            return
        # 데이터를 불러온다.
        load_data = utils._load_json(path)
        for data in load_data:
            self.trade_history.append(TradingLog(**data))

    async def init_setting(self):
        """초기 설정을 비동기적으로 수행"""

        # 시스템 설정 초기화
        InitialSetup.initialize()

        # TradeLog 불러온다.
        self.__trade_history_load()

        # 초기 지갑 잔고 설정
        if InitialSetup.mode:
            balance = self.initial_balance
        else:
            ins_client_class = utils._get_import(
                "TradeClient", f"{SymbolConfig.market_type.value}Client"
            )
            balance = await ins_client_class().get_total_wallet_balance()

        self.initial_balance = self.total_wallet_balance = self.available_balance = (
            balance
        )

    def __update_open_positions(self):
        """'
        self.open_position데이터를 업데이트하는 함수다.
        대상 데이터는 OpenTradeLog 함수에서 정보를 수집한다.
        """
        # class 속성명 획득
        trade_log_list = self.__get_attr_list()
        # 리스트가 비었으면
        if not trade_log_list:
            # 종료한다.
            return
        # 데이터 초기화
        self.open_positions = []
        # 리스트를 반복문으로 실행
        for log in trade_log_list:
            # 클라스에서 해당 속성을 불러온다.
            data = getattr(OpenTradeLog, log)
            # 데이터 변환 작업 실행한다.
            extract_data = self.__extract_values(data)
            # open_position에 저장한다.
            self.open_positions.append(extract_data)

    def __update_close_position(self):
        """
        self.closed_positions데이터를 업데이트하는 함수다.
        대상 데이터는 self.trade_history이며, self.__start_timestamp보다
        큰값만 수집한다. WalletManager선언시 start_ago_hr설정값을 기준으로 한다.
        """
        if not self.trade_history:
            return
        # 데이터 초기화
        self.closed_positions = []
        for trade_log in self.trade_history:
            if trade_log.start_timestamp < self.__start_timestamp:
                continue
            trade_log_list = self.__extract_values(trade_log)
            self.closed_positions.append(trade_log_list)

    def __update_number_of_stock(self):
        """
        현재 운용중인 포지션 갯수를 표기한다.
        self.open_positions의 len함수를 반영해도 되나, 연산순서 오처리시
        잘못된 정보가 계산되므로 OpenTradeLog데이터의 속성 갯수를 반영한다.
        """
        self.number_of_stocks = len(self.open_positions)
        self.trade_count = len(self.closed_positions) + self.number_of_stocks
        
    def __update_active_value(self):
        """
        현재 진행중인 포지션에 발생된 비용을 계산한다.
        필요한 항목은 마진, 진입 수수료를 반영한다.

        데이터 index값을 확인이 필요할 경우 self.__extract_values함수를 참고하라.
        """
        array_ = np.array(self.open_positions, float)
        value_index = 1
        entry_fee_index = 5
        value, fee = np.sum(array_[:, [value_index, entry_fee_index]], axis=0)
        self.active_value = value + fee

    def __update_profit_loss(self):
        """
        전체 goss_pnl값과 비율을 계산한다.
        필요한 항목은 fee(진입/이탈)와 net_pnl이다.

        데이터 index값을 확인이 필요할 경우 self.__extract_values함수를 참고하라.
        """
        array_ = np.array(self.__sum_position(), float)
        profit_index = 4
        entry_fee_index = 5
        exit_fee_index = 6
        profit, entry_fee, exit_fee = np.sum(
            array_[:, [profit_index, entry_fee_index, exit_fee_index]], axis=0
        )
        self.profit_loss = profit + entry_fee + exit_fee
        self.profit_loss_ratio = self.profit_loss / self.initial_balance

    async def __update_balance(self):
        temp_totla_balance = self.initial_balance + self.profit_loss
        
        if (self.initial_balance < temp_totla_balance and not self.open_positions and SafetyConfig.profit_preservation_enabled):
            if InitialSetup.mode:
                diff_profit = self.total_wallet_balance - self.initial_balance
                
                if diff_profit < self.available_balance:
                    self.profit_preservation_balance += diff_profit
                    self.profit_preservation_ratio = self.profit_preservation_balance / self.initial_balance
                    self.available_balance -= diff_profit 
                
            else:
                if SymbolConfig.market_type == 'futures':
                    total_balance = self.__ins_client_futures.get_total_wallet_balance()
                    self.available_balance = self.__ins_client_futures.get_available_balance()
                    
                    diff_profit = total_balance - self.initial_balance
                    if diff_profit < self.available_balance:
                        self.profit_preservation_balance += diff_profit
                        self.profit_preservation_ratio = self.profit_preservation_balance / self.initial_balance
                        self.__ins_client_futures.submit_fund_transfer(amount=diff_profit, transfer_type=2)                
                
                elif SymbolConfig.market_type == 'spot':
                    total_balance = self.__ins_client_spot.get_total_wallet_balance()
                    self.available_balance = self.__ins_client_spot.get_available_balance()

                    diff_profit = total_balance - self.initial_balance
                    if diff_profit < available_balance:
                        self.profit_preservation_balance += diff_profit
                        self.profit_preservation_ratio = self.profit_preservation_balance / self.initial_balance
                        self.__ins_client_spot.submit_fund_transfer(amount=diff_profit, transfer_type=1)                
                
                self.available_balance = self.__ins_client_futures.get_available_balance()
            
            self.active_value = self.initial_balance - self.available_balance
            self.total_wallet_balance = self.initial_balance
        else:
            return

    async def __update_run(self):
        self.__update_open_positions()
        self.__update_close_position()
        self.__update_number_of_stock()
        self.__update_active_value()
        self.__update_profit_loss()
        await self.__update_balance()

    def __telegram_balance(self):
        symbols = [utils._decimal_to_text(i[0]) for i in self.open_positions]
        message =(
        f'1. 보유 포지션: {symbols}\n'
        f'2. 거래횟수: {self.trade_count} 회\n'
        f'3. 손익비용: {self.profit_loss:,.2f} USDT\n'
        f'4. 손익비율: {self.profit_loss_ratio:,.2f} %\n'
        f'5. 이익보존금: {self.profit_preservation_balance:,.2f} USDT\n'
        )
        ins_telegram.send_to_message(message)
        
    def __telegram_trade_log(self):
        trade_log = self.trade_history[-1]
        ins_telegram.send_to_message(trade_log)

    def get_current_position(self, symbol: str, position: int):
        """
        symbol값과 positions을 기준으로 포지션 보유유무를 검토한다.
        True 반환시 보유중이며,
        False 반환시 미보유로 신호를 반환한다.
        """
        attr_name = f"{symbol}_{position}"
        return hasattr(OpenTradeLog, attr_name)

    async def add_position(self, data: TradingLog, ):
        """
        신규 포지션 정보를 추가한다.
        추가 전 동일한 symbol + position이 있는지 검토한다.
        
        포지션 정보는 OpenTradeLog 클라스에 저장한다.
        
        포지션 정보 저장전 entry_fee 업데이트된 값을 저장해야한다.
        데이터 추가 후 별도 업데이트하려면 추가 로직이 필요하기 때문이다.
        """
        log_symbol = data.symbol
        log_position = data.position
        if self.get_current_position(symbol=log_symbol, position=log_position):
            raise ValueError(f'동일 항목 동일 포지션 보유중:{log_symbol}')

        attr_name = f"{log_symbol}_{log_position}"
        setattr(OpenTradeLog, attr_name, data)
        await self.__update_run()

    async def remove_position(self, symbol: str, position: int):
        if not self.get_current_position(symbol=symbol, position=position):
            raise ValueError(f'제거하려는 포지션 정보 없음:{symbol}')
        attr_name = f"{symbol}_{position}"
        ###################################
        #여기에 update_positions을 한번 더 하자#
        ###################################
        
        ## 리얼 모드일 경우 최종 거래내역을 데이터를 업데이트 후 리무브 처리해야한다.
        ## 거래종료시 강제로 api데이터 기준으로 업데이트 되므로 실제 처리 비용을 비교해야한다.
        ## 백테스트시 비용계산부분 정확성을 높여야 한다.
        
        ## exit 비용을 정확히 처리하는게 좋은데
        
        
        
        self.trade_history.append(getattr(OpenTradeLog, attr_name))
        delattr(OpenTradeLog, attr_name)
        await self.__update_run()
        self.__telegram_balance()

    async def update_position(self, kline_data: dict[str, Any], refernce_data: dict[str, Optional[float]]) -> List:
        kline_symbol: Optional[str] = kline_data.get("s", None)
        kline_price: Optional[str] = kline_data.get("c", None)
        exit_fee: Optional[float] = refernce_data.get("f", 0)
        reverse_position_ratio = refernce_data.get("r", 0)
        result = all(x is None for x in (kline_symbol, kline_price))
        if result:
            raise ValueError(f"kline_data 오류: (col or data)")
        
        assert kline_price is not None, "kline_price 는 None아님을 지정함."
        kline_price_float: float = float(kline_price)

        close_signal:[list[str]] = []

        attr_names = [f"{kline_symbol}_1", f"{kline_symbol}_2"]
        for name in attr_names:
            if hasattr(OpenTradeLog, name):
                trading_log:TradingLog = getattr(OpenTradeLog, name)
                current_timestamp = int(time.time() * 1_000)
                signal = trading_log.update_trade_data(
                    timestamp=current_timestamp, price=kline_price_float, reverse_position_ratio=reverse_position_ratio, exit_fee=exit_fee)
                setattr(OpenTradeLog, name, trading_log)
            if signal:
                close_signal.append(name)
        await self.__update_run()
        return close_signal


class TelegramMessage:
    def __init__(self):
        self.chat_id:Optional[str] = None
        self.token: Optional[str] = None
        self.set_config()
    
    def set_config(self):
        parent_folder_path = ConfigSetting.SystemConfig.parent_folder_path.value
        folder = ConfigSetting.SystemConfig.api_folder_name.value
        file = ConfigSetting.SystemConfig.api_telegram.value    
        path = os.path.join(parent_folder_path, folder, file)
        api_key = utils._load_json(path)
        
        self.chat_id = api_key['chat_id']
        self.token = api_key['token']

    def send_to_message(self, message:str):
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
        }
        response = requests.post(url, data=payload)
        return response.json()

# CODE TEST
if __name__ == "__main__":
    import asyncio
    import nest_asyncio
    from pprint import pprint
    
    nest_asyncio.apply()
    ins_telegram = TelegramMessage()    
    obj = WalletManager()
    asyncio.run(obj.init_setting())
    welcom_message = f'1. Test: {ConfigSetting.InitialSetup.mode}\n 실행되었습니다.'

    ins_telegram.send_to_message(welcom_message)

    trade_log = TradingLog(
        symbol="XRPUSDT",
        position=1,
        quantity=1,
        hedge_enable=False,
        strategy_no=1,
        leverage=1,
        open_price=3.1,
        high_price=3.3,
        low_price=1,
        close_price=3.3,
        start_timestamp=1738296720000-(24*60*60_000),
    )

    dummy = {
        "t": 1738296720000,
        "T": 1738296899999,
        "s": "XRPUSDT",
        "i": "3m",
        "f": 939359504,
        "L": 939360627,
        "o": "3.08200000",
        "c": "2.08050000",
        "h": "3.08250000",
        "l": "3.08050000",
        "v": "134976.00000000",
        "n": 1124,
        "x": False,
        "q": "415956.90630000",
        "V": "70867.00000000",
        "Q": "218391.90910000",
        "B": "0",
    }

    asyncio.run(obj.add_position(trade_log))
    asyncio.run(obj.update_position(dummy))
    pprint(OpenTradeLog.XRPUSDT_1)
    asyncio.run(obj.remove_position(symbol='XRPUSDT', position=1))