from enum import Enum
from typing import List, Union, Optional
import os
import utils

###검증에 필요함###
import MarketDataFetcher

class TradingConfig(Enum):
    ### 데이터 수신
    websocket_reconnect_interval_hours: int = 2  # 웹소켓 재연결 주기 (시간 단위)
    market_type: str = 'futures'                 # 시장 유형
    
    ### 계좌 설정
    account_safety_ratio: float = 0.2            # 계좌 안전 비율
    profit_preservation_enabled: bool = True     # 수익 보존 기능 활성화 여부

    ### 주문 설정
    # 진입 (Buy or Position Open)
    max_leverage: int = 20                       # 최대 레버리지
    min_leverage: int = 2                        # 최소 레버리지
    
    
    # 종료 (Sell or Position Close)
    reference_leverage: int = 1                  # 참고용 레버리지
    stop_loss_threshold: float = 0.65            # 손절 기준 비율
    
    # SET 1
    dynamic_stop_loss_enabled: bool = True       # 동적 손절 비율 사용 여부
    dynamic_adjustment_rate: float = 0.005       # 동적 조정 비율
    dynamic_adjustment_interval: str = '3m'      # 동적 조정 주기
    
    # SET 2
    loss_streak_reset_interval: str = '4h'       # 연속 손실 기준 시간
    max_allowed_loss_streak: int = 1             # 허용된 연속 손실 횟수
    
    reject_repeated_loss_orders_enabled: bool = True  # 반복 손실 주문 거부 여부
    initial_stop_loss_rate: float = 0.025        # 초기 손절 비율
    # 
    
    max_concurrent_positions: int = 2            # 최대 동시 거래 심볼 수
    scaled_stop_loss_enabled: bool = True        # 조정 가능한 손절가 사용 여부
    
    
    
    ### 분석 설정
    data_analysis_window_days: int = 1           # 데이터 분석 창(일 단위)

    ### 시스템 설정
    hedge_trading_enabled: bool = False          # 헤지 거래 활성화 여부


class SymbolConfig(Enum):
    core_symbols:Union[List[str], str] = ['BTCUSDT', 'XRPUSDT', 'ETHUSDT', 'TRXUSDT']
    symbol_update_enabled:bool = True   # 주기적 업데이트 여부
    update_hour:Optional[int] = None    # 업데이트 주기 시간
    # symbol 선별 기준
    

class TestConfig(Enum):
    symbols:Union[List[str], str] = ['BTCUSDT', 'TRUMPUSDT', 'XRPUSDT']
    seed_funds: float = 1_000  # 초기 자본금 / None값일경우 계좌 전체 금액 반영됨.
    start_datetime: str = '2025-1-20 09:00:00'  # 백테스트 시작 날짜
    end_datetime: str = '2025-1-21 08:59:59'  # 백테스트 종료 날짜
    download_new_data: bool = False  # 새로운 데이터 다운로드 여부


class run:
    def __init__(self, trading_config:TradingConfig, test_config:TestConfig):
        # 초기화 메서드에서 실행
        self.test_mode = self.check_test_mode()
        self.symbols = TestConfig.symbols.value if self.test_mode else None

        self.trading_config = trading_config
        self.test_config = test_config
        self.symbols: Optional[Union[List[str], str]] = None


        ###instance
        self.ins_market = MarketDataFetcher.FuturesMarket()
        
    def check_test_mode(self):
        while True:
            user_input = input("TEST MODE ? (y/n): ").strip().lower()
            if user_input == "y":
                return True
            elif user_input == "n":
                return False
            else:
                print("잘못된 입력입니다. 'y' 또는 'n'을 입력하세요.")



    def validate_config(self):
        # 에러발생시 타이틀 발생
        def __error_title(config:Union[TestConfig, TradingConfig]):
            print('\n')
            name = repr(config).split("'")[1]
            text = f"*-=-=-=-=-=-* ERROR ( {name} ) *-=-=-=-=-=-*"
            width = 80  # 출력할 총 너비
            centered_text = text.center(width)
            print(f'{centered_text}\n')
            
        # symbol 유효성 검사
        def __validate_symbol():
            tickers_data = 
            
        ### TestConfig 검토 파트 ###
        # TEST MODE 일경우
        if self.test_mode:
            start_timestamp = utils._convert_to_timestamp_ms(self.test_config.start_datetime.value)
            end_timestamp = utils._convert_to_timestamp_ms(self.test_config.end_datetime.value)
            
            if start_timestamp > end_timestamp:
                raise ValueError(f'종료시간이 시작시간보다 큼')

            start_time_std = '09:00:00'
            end_time_std = '08:59:59'
            
            config_start_date = self.test_config.start_datetime.value
            config_end_date = self.test_config.end_datetime.value
            
            if not start_time_std in config_start_date:# and end_time_std in config_end_date:
                __error_title(self.test_config)
                print(f'1. 오류내용: 시작 시간 데이터 입력 오류')
                print(f'2. 해결방법: {TestConfig.start_datetime}를 09:00:00로 수정\n')
                raise ValueError(f'데이터 오류 >> config 정보 수정')
            
            if not end_time_std in config_end_date:
                __error_title(self.test_config)
                print(f'1. 오류내용: 종료 시간 데이터 입력 오류')
                print(f'2. 해결방법: {TestConfig.end_datetime}를 08:59:59로 수정\n')
                raise ValueError(f'데이터 오류 >> config 정보 수정')
            
            path_kline_data = '/Users/nnn/GitHub/DataStore/kline_data.json'
            path_closing_sync_data = '/Users/nnn/GitHub/DataStore/closing_sync_data.pkl'
            if not os.path.exists(path_kline_data) and self.test_config.download_new_data.value:
                __error_title(self.test_config)
                print(f'1. 오류내용: 저장된 kline_data.json 이 없음.')
                print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
                raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')
            
            if not os.path.exists(path_closing_sync_data) and self.test_config.download_new_data.value:
                __error_title(self.test_config)
                print(f'1. 오류내용: 저장된 closing_sync_data.pkl 이 없음.')
                print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
                raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')
            
            kline_data = utils._load_json(path_kline_data)
            kline_data_symbols = list(kline_data.keys())
            
            if kline_data_symbols != trading_config.symbols.value:
                __error_title(self.test_config)
                print(f'1. 오류내용: kline data의 symbol정보 불일치')
                print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
                raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')
            
            intervals = list(kline_data[kline_data_symbols[0]].keys())
            select_data = kline_data[kline_data_symbols[0]][intervals[0]]
            
            is_start_timestamp = select_data[0][0] == start_timestamp
            is_end_timestamp = select_data[-1][6] == end_timestamp
            if not is_start_timestamp and not is_end_timestamp:
                __error_title()
                print(f'1. 오류내용: kline data의 기간정보 불일치')
                print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
                raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')


    validate_config(test_config=TestConfig, trading_config=TradingConfig)