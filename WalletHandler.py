from typing import List, Dict, Optional, Any, Union
from DataStoreage import *
import ConfigSetting
import os
import utils
import asyncio
import requests
import TradeClient
from datetime import datetime, timedelta
import importlib
from DataStoreage import TradingLog
import numpy as np
from pprint import pprint
class OpenTradeLog:
    """
    현재 보유중인 포지션 정보를 임시 저장한다.
    속성명은 {symbol}_{position}으로 한다.
    """

class WalletManager(OpenTradeLog):
    """
    반복적인 API를 피하기 위하여 wallet정보를 별도 관리한다.
    실제 거래시 슬리피지와 같은 계산하기 어려운 항목들은 exit_fee로 합산한다.
    """
    def _init_(self, current_timestamp:int, initial_balance: float = 1_000, start_ago_hr: int = 24):
        self.trade_history: List[TradingLog] = []
        self.closed_positions: List[List[int]] = []
        self.open_positions: List[List[int]] = []
        self.trading_count: int = 0 # 거래중인 자산 종목 수
        self.initial_balance: float = initial_balance  # 초기 자산
        self.total_wallet_balance: float = 0  # 총 평가 자산
        self.initial_margins: float = 0  # 거래 중 자산 가치
        self.available_balance: float = 0  # 사용 가능한 예수금
        self.profit_loss: float = 0  # 손익 금액
        self.profit_loss_ratio: float = 0  # 손익률
        self.profit_preservation_balance:float = 0 #수익금 보존금액
        self.profit_preservation_ratio :float = 0 #수익금 보존 비율
        self.total_trade_count: int = 0  # 총 체결 횟수

        ### instance
        self._ins_client_futures:TradeClient.FuturesClient = TradeClient.FuturesClient()
        self._ins_client_spot:TradeClient.SpotClient = TradeClient.SpotClient()
        self._ins_telegram:TelegramMessage = utils.TelegramMessage(ConfigSetting.SystemConfig.path_telegram_api.value)
        ### system setting
        self.start_ago_hr = start_ago_hr
        ### 시간관리 속성
        self.current_timestamp:int = current_timestamp  # 현재시간 지정(kline_data 수신시 지속 업데이트)
        self._start_timestamp_history: int = self.current_timestamp - (self.start_ago_hr * 3_600 * 1_000)  # trade log data로딩 범위 지정
        self._start_timestamp_pnl:int = current_timestamp # 수익보존 상황발생시 self.current_timestamp기준으로 자동 업데이트

    async def init_setting(self):
        """
        WalletManager 실행시 필요한 기초 정보를 설정한다.
        단독 테스트 실행시 ConfigSetting.InitialSetup.initialize()이 우선 실행되어야한다.
        mode에 대한 설정이 필요하기 때문이다.
        
            1. 기능: 본 클라스의 기초정보 설정.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """

        # TradeLog 불러온다.
        self._trade_history_load()

        # 초기 지갑 잔고 설정
        if ConfigSetting.InitialSetup.mode:
            balance = self.initial_balance
        else:
            ins_client_class = utils._get_import(
                "TradeClient", f"{ConfigSetting.SymbolConfig.market_type.value}Client"
            )
            balance = await ins_client_class().get_total_wallet_balance()

        self.initial_balance = self.total_wallet_balance = self.available_balance = (
            balance
        )

    def _get_path(self) -> str:
        """
        트레이드 히스토리 주소를 생성 및 반환한다. 
        ConfigSetting.py에서 ConfigSetting.InitialSetup.mode값을 기준으로 생성되는 주소값이 달라진다.
        mode에서 True일 경우 TEST MODE, 이며, False일 경우 LIVE MODE를 의미한다.
        
            1. 기능: TradeHistory 데이터 주소를 반환.
            2. 매개변수: 해당없음.
            3. 반환값 : str형태 주소값
        """
        
        # 파일이름을 래핑형태로 변수등록한다.
        file_name:Optional[bool] = {
            True: ConfigSetting.SystemConfig.test_trade_history.value,
            False: ConfigSetting.SystemConfig.live_trade_history.value,
        }.get(ConfigSetting.InitialSetup.mode, None)
        
        # 결과값이 None나오면 오류처리한다. None이 나오면 안된다.
        if file_name is None:
            raise ValueError(f'mode 설정 오류')
        
        # 주소값을 생성한다.
        path = os.path.join(
            ConfigSetting.SystemConfig.parent_folder_path.value,
            ConfigSetting.SystemConfig.data_folder_name.value,
            file_name,
        )
        return path

    def _get_attr_list(self) -> List:
        """
        OpenTradeLog 클라스의 속성이름을 확보한다.
        확보된 이름을 활용하여 getattr로 활용하기 위함이다.
        
            1. 기능: OpenTradeLog의 속성값을 리스트 형태로 생성 및 반환.
            2. 매개변수: 해당없음.
            3. 반환값 : list형태의 속성명
        """
        # 저장할 변수값을 초기화한다.
        names = []
        # OpenTradeLog 클라스에 저장된 속성명을 반복문을 이용해서 조회한다.
        for name in vars(OpenTradeLog):
            # 속성명에서 "_"가 포함된 항목은 제외하고 변수값이 추가한다.
            if "_" not in name:
                names.append(name)
        return names

    def _merged_positions_data(self) -> List:
        """
        보유중 포지션과 거래종료 포지션 데이터를 하나의 list형태로 합친 후 반환한다.
        
            1. 기능: open포지션과 close포지션을 하나의 리스트로 반환.
            2. 매개변수: 해당없음.
            3. 반환값: 중첩리스트
        """

        # 두 속성값을 합친다. 비어있을경우 빈 list가 반환된다.
        return self.closed_positions + self.open_positions

    def _extract_values(self, data: TradingLog) -> List:
        """
        트레이딩 로그 데이터에서 필요한 부분만 추출한다.
        추후 np.ndarray 백터연산처리를 위하여 symbol값을 10진수로 변환하였다.
        
        해당값 수정이 필요할경우 연결된 모든 code를 수정해야하므로 주의가 필요하다.
        수정사항이 많아질경우 Dict형태로 생성 후 언팩처리하는것도 염두할 필요가 있다.
        
            1. 기능: TradingLog에서 필요한 값만 추출 및 반환.
            2. 매개변수: 해당없음.
            3. 반환값: list[float]형태의 자료
        
        """
        # symbol값을 문자형태로 반환시 백터연산을 할 수 없으므로 10진수 형태로 변환한다.
        symbol_decimal = utils._text_to_decimal(data.symbol)
        #start timestamp
        start_timestamp = data.start_timestamp
        #시나리오 번호
        strategy = data.strategy_no
        # 기초 자금
        initial_value = data.initial_value
        # 포지션 (1:long, 2:short)
        position = data.position
        # 수량
        quantity = data.quantity
        # 손익금액
        net_pnl = data.net_pnl
        # 진입 수수료
        entry_fee = data.entry_fee
        # 종료 수수료
        exit_fee = data.exit_fee
        return [
            symbol_decimal,#0
            start_timestamp,#1
            strategy,#2
            initial_value,#3
            position,#4
            quantity,#5
            net_pnl,#6
            entry_fee,#7
            exit_fee,#8
        ]

    def _trade_history_save(self):
        """
        트레이드 히스토리 데이터를 저장한다.
        저장할 데이터(self.trade_history)가 없으면 함수를 종료한다.

            1. 기능: self.trade_history 데이터를 저장.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        # Trade History가 비어있으면
        if not self.trade_history:
            # 함수를 종료한다.
            return

        # 주소를 확보한다.
        path = self._get_path()
        
        save_data = []
        for trade_log in self.trade_history:
            trade_log_dict = trade_log._dict_
            save_data.append(trade_log_dict)
        
        # 변환이 완료된 데이터를 json데이터로 저장한다.
        utils._save_to_json(path, save_data)

    def _trade_history_load(self):
        """
        저장된 Dict타입의 트레이드 히스토리를 불러온 후 속성값에 저장한다.
        본 클라스는 과거 데이터의 영향을 받는 함수가 있으므로 거래 기록이 필요하다.

        본 함수는 ConfigSetting.py의 지정값에 영향을 받는다.

        업데이트 항목
            >> self.trade_history
            >> self.close_position

            1. 기능: 로컬에 저장된 트레이드 히스리를 불러온 후 self.trade_history에 저장.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        # 주소를 확보한다.
        path = self._get_path()
        # 파일 존재 유무를 확인한다.
        if not os.path.isfile(path):
            # 파일이 없으면 함수를 종료한다.
            return
        # 데이터를 불러온다.
        load_data = utils._load_json(path)
        # 데이터를 for문 순환처리해서 하나씩 조호한다.
        for data in load_data:
            # 조회된 값을 언팩킹 한다.
            self.trade_history.append(TradingLog(**data))

    def _update_open_positions(self):
        """'
        self.open_position데이터를 업데이트하는 함수다.
        대상 데이터는 OpenTradeLog 함수에서 정보를 수집한다.
        
            1. 기능: self.open_positions를 업데이트.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        
        """
        # class 속성명 획득
        trade_log_list = self._get_attr_list()
        # 리스트가 비었으면
        self.open_positions = []
        if not trade_log_list:
            # 종료한다.
            return
        # 데이터 초기화
        # 리스트를 반복문으로 실행
        for log in trade_log_list:
            # 클라스에서 해당 속성을 불러온다.
            data = getattr(OpenTradeLog, log)
            # pprint(data)
            # 데이터 변환 작업 실행한다.
            extract_data = self._extract_values(data)
            # open_position에 저장한다.
            self.open_positions.append(extract_data)

    def _update_closed_positions(self):
        """
        self.closed_positions데이터를 업데이트하는 함수다.
        대상 데이터는 self.trade_history이며, self._start_timestamp_history보다
        큰값만 수집한다. WalletManager선언시 start_ago_hr설정값을 기준으로 한다.
        
            1. 기능: self.closed_positions를 업데이트.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        if not self.trade_history:
            return
        # 데이터 초기화
        self.closed_positions = []
        # start_timestamp를 래핑한다.
        start_timestamp = {False:self._start_timestamp_history,
                           True:0}.get(ConfigSetting.InitialSetup.mode)
        # 만약 래핑조회 값이 None이면 오류처리한다.
        if start_timestamp is None:
            raise ValueError(f'start_timestamp값 오류')
        # 트레이드 히스토리를 반복문으로 조회한다.
        for trade_log in self.trade_history:
            # 레핑 조회된 start_timestamp값보다 trade_log.start_timestamp가 작을경우 불러오지 않는다.
            # 데이터 과잉 확보를 방지하기 위함이다.
            # 기본적으로 라이브 트레이딩 기준 1일전(24시간) 데이터부터 확보한다.
            if trade_log.start_timestamp < start_timestamp:
                continue
            # TradeLog데이터를 list화 한다.
            trade_log_list = self._extract_values(trade_log)
            # list화한 데이fmf closed_positions에 추가한다.
            self.closed_positions.append(trade_log_list)

    def _update_trade_count(self):
        """
        현재 운용중인 포지션 갯수를 표기한다.
        self.open_positions의 len함수를 반영해도 되나, 연산순서 오처리시
        잘못된 정보가 계산되므로 OpenTradeLog데이터의 속성 갯수를 반영한다.
        
            1. 기능: trading_count, total_trade_count 업데이트한다.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        # 보유중인 데이터의 길이를 계산한다.
        self.trading_count = len(self.open_positions)
        # 종료된 포지션과 보유중인 포지션의 데이터길이를 합친다.
        self.total_trade_count = len(self.closed_positions) + self.trading_count
        
    def _update_initial_margins(self):
        """
        현재 진행중인 포지션에 발생된 비용을 계산한다.
        필요한 항목은 마진, 진입 수수료를 반영한다.

        주로 백테스트에 주로 사용된다. 라이브 트레이딩은 balance 업데이트시 api를 수신하여 보정한다.
        데이터 index값을 확인이 필요할 경우 self._extract_values함수를 참고하라.
        
            1. 기능: self.initial_margins 업데이트.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        # 유지중인 포지션이 없으면
        if not self.open_positions:
            # 비용은 0
            self.initial_margins = 0
            return
        # 데이터를 np.ndarray타입으로 변환
        array_ = np.array(self.open_positions, float)
        # index 정보(매직넘버 최소화) >> 함수 self._extract_values() 반환값을 참고
        value_index = 3
        entry_fee_index = 7
        # 각각의 비용을 계산
        value, fee = np.sum(array_[:, [value_index, entry_fee_index]], axis=0)
        # 비용 합계
        self.initial_margins = value + fee


    def _update_profit_loss(self):
        """
        전체 goss_pnl값과 비율을 계산한다.
        필요한 항목은 fee(진입/이탈)와 net_pnl이다.

        데이터 index값을 확인이 필요할 경우 self._extract_values함수를 참고하라.
        
            1. 기능: PNL정보 업데이트.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        
        # open, closed 포지션 데이터 정보 병합
        merged_positions_data = self._merged_positions_data()
        # np.ndarray형태로 변환
        array_ = np.array(merged_positions_data, float)
        # 데이터가 없으면,
        if array_.size == 0:
            # 종료한다.
            return
        
        # pnl 수집 기준이될 데이터 index획득
        condition = np.where(array_[:, 1]>=self._start_timestamp_pnl)
        array_ = array_[condition]
        # index 정보(매직넘버 최소화) >> 함수 self._extract_values() 반환값을 참고
        profit_index = 6
        entry_fee_index = 7
        exit_fee_index = 8
        # 각 항목에 대해서 합계 계산.
        profit, entry_fee, exit_fee = np.sum(
            array_[:, [profit_index, entry_fee_index, exit_fee_index]], axis=0
        )
        # gross_pnl을 계산한다. (손익 전체)
        self.profit_loss = profit - (entry_fee + exit_fee)
        # gross_pnl 비율을 계산한다.
        self.profit_loss_ratio = self.profit_loss / self.initial_balance

    async def _update_balance(self):
        """
        balance 파트를 업데이트한다. 아직 불안요소가 많다. 테스트버전과 라이브버전을 동시에 구현해야 하다보니
        연산순서에 따라 생각치 못한 결과가 발생할수도 있다. 특히 available_balance가 변수인데, 정확한 값으로 나올지의문이다.
        중간에 api데이터 수신해서 보정해주긴하지만 아직 테스트가 필요하다.
        
        과도한 API발생시 ip 차단을 염려해야만 한다.
        
            1. 기능: balance관련 데이터 업데이트
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        # 초기금액과 손익금액을 더한다.
        

        # 기본설정
        self.total_wallet_balance = self.initial_balance + self.profit_loss
        self.available_balance = self.total_wallet_balance - self.initial_margins
        
        # 수익보존 설정 활성화일 경우
        if ConfigSetting.SafetyConfig.profit_preservation_enabled.value:
            # 초과수익금을 계산
            over_pnl = ConfigSetting.SafetyConfig.profit_preservation_amount.value - self.total_wallet_balance
            
            # 현재 보유 포지션이 없을 것.
            is_open_position = len(self.open_positions)==0
            # 초과수익금이 +일 것.
            is_over_pnl = over_pnl > 0
            # 예수금보다 초과수익금이 작을 것(이체가능한도 검토, 사실 해당절차 불필요함. is_open_position이 이미 증명했음.)
            is_availabe = self.available_balance > over_pnl
            
            # 위 조건 모두 일치시
            if is_open_position and is_over_pnl and is_availabe:
                # 이체처리
                self.profit_preservation_balance += over_pnl
                # 비율재계산
                self.profit_preservation_ratio = self.profit_preservation_balance / self.initial_balance
                # pnl 초기화
                self.profit_loss = 0
                # pnl 비율 초기화
                self.profit_loss_ratio = 0
                # 총 금액 초기화
                self.total_wallet_balance = self.initial_balance
                # 예수금 초기화
                self.available_balance = self.initial_balance
                # 현재시간 초기화
                self._start_timestamp_pnl = self.current_timesatmp
            
            # 만약 라이브 트레이딩이면 실제 이체를 발생 및 값 교정
            if not ConfigSetting.InitialSetup.mode and over_pnl > 0: #live모드시 이체를 실행한다.
                obj_and_type = {'Futures':[self._ins_client_futures, 2],
                                'Spot':[self._ins_client_spot, 1]}.get(ConfigSetting.SymbolConfig.market_type.value, None)
                # 값 교정
                self.total_wallet_balance = self.initial_margins = await obj_and_type[0].get_total_wallet_balance()
                # 그럴리 없지만 만약 None값이 나오면 오류발생
                if obj_and_type is None:
                    raise ValueError(f'instance 호출 오류')
                await obj_and_type[0].submit_fund_transfer(amount=over_pnl, transfer_type=obj_and_type[1])
                await asyncio.sleep(1)

    async def update_run(self):
        """
        위의 업데이트 함수들을 일괄 실행하는 함수다.
        
            1. 기능: 업데이트 관련 함수를 일괄 실행.
            2. 매개변수: 해당없음.
            3. 반환값: 해당없음.
        """
        self._update_open_positions()
        self._update_closed_positions()
        self._update_trade_count()
        self._update_initial_margins()
        self._update_profit_loss()
        await self._update_balance()

    def check_position_status(self, symbol: str, position: int):
        """
        symbol값과 positions을 기준으로 포지션 보유유무를 검토한다.
        True 반환시 보유중이며,
        False 반환시 미보유로 신호를 반환한다.
        
            1. 기능: OpenTradeLog 속성 이름을 생성하고 검증한다.
            2. 매개변수:
                1) symbol: 쌍거래심볼
                2) position:
                    >> 1:Long or Buy
                    >> 2:Sell or Short
            3. 반환값:
                1) True : 유효함.
                2) False : 유효하지 않음.
        """
        # 가상 속성명을 생성
        attr_name = f"{symbol}_{position}"
        # 실제 존재여부를 검토하고 결과값 반환.
        return hasattr(OpenTradeLog, attr_name)

    async def add_position(self, data: TradingLog, ):
        """
        신규 포지션 정보를 추가한다.
        추가 전 동일한 symbol + position이 있는지 검토한다.
        
        포지션 정보는 OpenTradeLog 클라스에 저장한다.
        
        포지션 정보 저장전 entry_fee 업데이트된 값을 저장해야한다.
        데이터 추가 후 별도 업데이트하려면 추가 로직이 필요하기 때문이다.
        
            1. 기능: 신규 거래 발생시 정보(TradingLog)를 추가한다.
            2. 매개변수:
                1) TradingLog : DataStoreage.TradingLog데이터
            3. 반환값: 해당없음.
        """
        log_symbol = data.symbol
        log_position = data.position
        if self.check_position_status(symbol=log_symbol, position=log_position):\
            raise ValueError(f'동일 항목 동일 포지션 보유중:{log_symbol}')

        attr_name = f"{log_symbol}_{log_position}"
        setattr(OpenTradeLog, attr_name, data)
        await self.update_run()

    async def remove_position(self, symbol: str, position: int):
        """'
        포지션이 종료되면 트레이드 로그 데이터를 거래종료 항목으로 데이터를 옮긴다.
        옮기기전에 실전 거래시 API정보를 수집하여 데이터 매칭을 시킨 후 이동처리한다.
        거래내역은 트레이드 히스토리를 활용한다.
        
            1. 기능: 거래종료시 각종 데이터를 이동처리한다.
            2. 매개변수:
                1) symbol: 쌍거래심볼
                2) position:
                    >> 1:Buy or Long
                    >> 2:Sell or Short
        """
        # 현재 포지션정보가 있는지 점검한다. 클라스에 저장된 데이터가 있는지 여부를 체크한다.
        if not self.check_position_status(symbol=symbol, position=position):
            # ###DEBUG
            # print(OpenTradeLog._dict_)
            raise ValueError(f'제거하려는 포지션 정보 없음:{symbol}')
        # 속성명을 생성한다.
        attr_name = f"{symbol}_{position}"

        # instance를 래핑한다.
        obj = {'Futures':self._ins_client_futures,
               'Spot':self._ins_client_spot}.get(ConfigSetting.SymbolConfig.market_type.value, None)

        # 그럴리 없겠지만, 만약 None이면 오류발생시킨다.
        if obj is None:
            raise ValueError(f'Client Instance 조회 오류')
        
        # dataclass의 TradingLog데이터를 불러온다.
        trade_log:TradingLog = getattr(OpenTradeLog, attr_name)
        
        # 만약 라이브 모드라면,
        if not ConfigSetting.InitialSetup.mode:
            # 과거 거래기록을 api로 조회한다.
            trade_history = await obj.fetch_trade_history(symbol)
            # 마지막 index가 최신 정보이므로 최신정보를 분류한다.
            last_trade_history = trade_history[-1]
            
            # 시간정보를 조회한다.
            self.current_timesatmp = int(last_trade_history['time'])
            # 거래단가 정보를 조회한다.
            price = float(last_trade_history['price'])
            # 수수료 정보를 조회한다.
            exit_fee = float(last_trade_history['commission'])
            
            # 거래종료에 따른 별도 데이터를 업데이트한다.
            trade_log.update_closed_trading_log(timestamp=self.current_timesatmp, price=price, exit_fee=exit_fee)
        
        # 트레이드 히스토리에 해당 트레이드 로그를 저장한다.
        self.trade_history.append(trade_log)
        # OpenTradeLog에서 해당 로그값을 삭제한다.
        delattr(OpenTradeLog, attr_name)
        # 전체 업데이트한다.
        await self.update_run()
        # 수정된 trade history 전체를 로컬에 저장한다.
        self._trade_history_save()
        # 텔레그램 메시지를 발송한다.
        self._telegram_balance()

    def _reverse_position_ratio(self, position:int, start_timestamp:int, kline_data: list[List[Any]]) -> float:
        """
        현재 포지션과 반대 움직임 캔들 body비율의 합계를 계산하고 반환한다.
        update_position에 적용할 보조 함수다.

            1. 기능: 포지션 보유시점부터 포지션방향과 반대 움직임에 대한 캔들 비율의 합계를 구함.
            2. 매개변수:
                1) position:
                    >> 1: Buy 또는 Long
                    >> 2: Sell 또는 Short
                2) start_timestamp: TradingLog데이터의 start_timestamp
                3) kline_data: 수신된 kline_data
        """
        if isinstance(kline_data, list):
            kline_data = np.array(kline_data, float)  # 리스트를 NumPy 배열로 변환

        if position == 1:
            condition = np.where((kline_data[:, 4] < kline_data[:, 1])&
                                 (kline_data[:,0]>=start_timestamp))[0]
        elif position == 2:
            condition = np.where((kline_data[:, 1] < kline_data[:, 4])&
                                 (kline_data[:,0]>=start_timestamp))[0]
        else:
            raise ValueError(f"TradeLog데이터 오류: {position}")

        if condition.size == 0:
            return 0
        #DEBUG
        # print(condition)

        select_data = kline_data[condition]
        diff = np.abs(select_data[:, 4] - select_data[:, 1])  # 차이값 계산
        ratio = diff / select_data[:, 1]  # 비율 계산
        return np.sum(ratio)
            

    async def update_position(self, symbol:str, kline_data: list[List[Any]]) -> List:
        """'
        보유중인 포지션 정보를 업데이트한다. 시간, 가격, 반대 캔들의 비율 합계 등을 업데이트하여 이탈 가격을 계산한다.
        업데이트 후 포지션 종료가 필요한 항목들을 리스트 형태로 구성하여 반환한다.
        
            1. 기능: 보유중인 포지션에 대해서 현재 정보를 업데이트.
            2. 매개변수:
                1) kline_data: kline_data(백테스트)
                2) reverse_position_ratio: 현재 포지션 역방향 캔들의 비율 합산
            3. 반환값: list타입으로 포지션 종료가 필요한 OpenTradeLog의 속성값
        """
            
        # kline_price 초기 데이터는 str형태이므로 float형태로 변형한다.
        kline_price_float: float = float(kline_data[-1][4])
        # 종료 리스트 내역을 초기화 한다.
        close_signal:[list[str]] = []

        # 예상가능한 속성명을 리스트로 생성한다. long or short
        attr_names = [f"{symbol}_1", f"{symbol}_2"]
        # 속성명을 반복문 처리하여
        for name in attr_names:
            # 실제 존재여부를 검증한다.
            if hasattr(OpenTradeLog, name):
                # 있으면 해당 로그값을 불러온다.
                trading_log:TradingLog = getattr(OpenTradeLog, name)

                # 테스트모드일 경우 데이터기준으로 현재타임스템프를 추출한다.
                if ConfigSetting.InitialSetup.mode:
                    self.current_timesatmp:int = int(kline_data[-1, 6])
                # 라이브모드일 경우 함수로 현재시간을 생성한다.
                else:
                    self.current_timesatmp:int = int(time.time() * 1_000)
                                
                reversed_ratio = self._reverse_position_ratio(position=trading_log.position,
                                                               start_timestamp=trading_log.start_timestamp,
                                                               kline_data=kline_data)
                target_ratio = reversed_ratio * ConfigSetting.StopLossConfig.negative_reference_rate.value
                # 위 내용 기준으로 업데이트한다. update_open_trading_log함수 자체가 stop flag를 반환하므로 signal 변수에 해당값 저장된다.
                signal = trading_log.update_open_trading_log(
                    timestamp=self.current_timesatmp, price=kline_price_float, reverse_position_ratio=target_ratio)#, exit_fee=exit_fee)
                # signal이 True인것들은 name변수를 close_signal에 추가한다.
                if signal:
                    close_signal.append(name)
                # 업데이트가 되면 trading_log를 "덮어씌운다.". 수정이 안되므로...
                setattr(OpenTradeLog, name, trading_log)
        # 전체 업데이트한다.
        await self.update_run()
        # close_signal값을 반환한다.
        return close_signal

    def _telegram_balance(self):
        """
        텔레그램으로 발송할 메시지를 구성한다. 아직 정리단계 함수.
        
        """
        symbols = [utils._decimal_to_text(i[0]) for i in self.open_positions]
        message =(
        f'1. 보유 포지션: {symbols}\n'
        f'2. 거래횟수: {self.total_trade_count} 회\n'
        f'3. 손익비용: {self.profit_loss:,.2f} USDT\n'
        f'4. 손익비율: {self.profit_loss_ratio:,.2f} %\n'
        f'5. 이익보존금: {self.profit_preservation_balance:,.2f} USDT\n'
        )
        self._ins_telegram.send_to_message(message)
        
    def _telegram_trade_log(self):
        """
        텔레그램으로 발송할 메시지를 구성한다. 아직 정리단계 함수.
        """
        trade_log = self.trade_history[-1]
        self._ins_telegram.send_to_message(trade_log)



# CODE TEST
if _name_ == "_main_":
    
    import asyncio
    import nest_asyncio
    from pprint import pprint
    
    nest_asyncio.apply()
    # ins_telegram = utils.TelegramMessage()
    # # 시스템 설정 초기화
    ConfigSetting.InitialSetup.initialize()
    
    obj = WalletManager()
    asyncio.run(obj.init_setting())
    welcom_message = f'1. Test: {ConfigSetting.InitialSetup.mode}\n 실행되었습니다.'

    # obj.send_to_message(welcom_message)

    trade_log = TradingLog(
        symbol="TRXUSDT",
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
        "s": "TRXUSDT",
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
    pprint(OpenTradeLog.TRXUSDT_1)
    asyncio.run(obj.remove_position(symbol='TRXUSDT', position=1))