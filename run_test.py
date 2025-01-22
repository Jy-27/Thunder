from enum import Enum
from typing import List, Union, Optional
import os
import utils

class TradingConfig(Enum):
    symbols: Union[List[str], str] = ['BTCUSDT', 'ETHUSDT', 'XRPUSDT', 'SOLUSDT', 'BNBUSDT', 'TRXUSDT', 'DOGEUSDT', '']  # 거래 심볼
    reconnect_cycle_hours:int = 2   #웹소켓 재접속 주기(hour) 
    safety_ratio: float = 0.2  # 계좌 안전 비율
    max_leverage: int = 20  # 최대 레버리지
    min_leverage: int = 2   # 최소 레버리지
    reference_leverage: int = 1  # 참고용 레버리지
    seed_funds: Optional[float] = None  # 초기 자본금 / None값일경우 계좌 전체 금액 반영됨.
    market_type: str = 'futures'  # 시장 유형
    stop_loss_threshold: float = 0.65  # 손절 기준 비율
    dynamic_stop_loss: bool = True  # 동적 손절 비율 사용 여부
    adjustment_rate: float = 0.005  # 동적 조정 비율
    adjustment_interval: str = '3m'  # 동적 조정 주기
    initial_stop_loss: float = 0.015  # 초기 손절 비율
    reject_repeated_loss_orders: bool = True  # 반복 손실 시 주문 거부
    allowed_loss_streaks: int = 1  # 허용된 연속 손실 횟수
    loss_reset_interval: str = '4h'  # 연속 손실 기준 시간
    max_open_positions: int = 2  # 최대 동시 거래 심볼 수
    enable_profit_preservation: bool = True  # 수익 보존 기능 활성화 여부
    use_scaled_stop_loss: bool = True  # 조정 가능한 손절가 사용 여부
    analysis_window_days: int = 0  # 데이터 분석 창(day)
    is_hedge_enabled:bool = False #헤지거래 설정여부.

class TestConfig(Enum):
    start_datetime: str = '2025-1-20 09:00:00'  # 백테스트 시작 날짜
    end_datetime: str = '2025-1-21 08:59:59'  # 백테스트 종료 날짜
    download_new_data: bool = False  # 새로운 데이터 다운로드 여부


while True:
    user_input = input("TEST MODE ? (y/n): ").strip().lower()
    if user_input == "y":
        TEST_MODE = True
        break
    elif user_input == "n":
        TEST_MODE = False
        break
    else:
        print("잘못된 입력입니다. 'y' 또는 'n'을 입력하세요.")


def validate_config(test_config: TestConfig, trading_config: TradingConfig, mode:bool=TEST_MODE):
    def __error_title(config:Union[TestConfig, TradingConfig]):
        print('\n')
        name = repr(config).split("'")[1]
        text = f"*-=-=-=-=-=-* ERROR ( {name} ) *-=-=-=-=-=-*"
        width = 80  # 출력할 총 너비
        centered_text = text.center(width)
        print(f'{centered_text}\n')
        
    ### TestConfig 검토 파트 ###
    # TEST MODE 일경우
    if mode:
        start_timestamp = utils._convert_to_timestamp_ms(test_config.start_datetime.value)
        end_timestamp = utils._convert_to_timestamp_ms(test_config.end_datetime.value)
        
        if start_timestamp > end_timestamp:
            raise ValueError(f'종료시간이 시작시간보다 큼')

        start_time_std = '09:00:00'
        end_time_std = '08:59:59'
        
        config_start_date = test_config.start_datetime.value
        config_end_date = test_config.end_datetime.value
        
        if not start_time_std in config_start_date:# and end_time_std in config_end_date:
            __error_title(test_config)
            print(f'1. 오류내용: 시작 시간 데이터 입력 오류')
            print(f'2. 해결방법: {TestConfig.start_datetime}를 09:00:00로 수정\n')
            raise ValueError(f'데이터 오류 >> config 정보 수정')
        
        if not end_time_std in config_end_date:
            __error_title(test_config)
            print(f'1. 오류내용: 종료 시간 데이터 입력 오류')
            print(f'2. 해결방법: {TestConfig.end_datetime}를 08:59:59로 수정\n')
            raise ValueError(f'데이터 오류 >> config 정보 수정')
        
        path_kline_data = '/Users/nnn/GitHub/DataStore/kline_data.json'
        path_closing_sync_data = '/Users/nnn/GitHub/DataStore/closing_sync_data.pkl'
        if not os.path.exists(path_kline_data) and test_config.download_new_data.value:
            __error_title(test_config)
            print(f'1. 오류내용: 저장된 kline_data.json 이 없음.')
            print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
            raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')
        
        if not os.path.exists(path_closing_sync_data) and test_config.download_new_data.value:
            __error_title(test_config)
            print(f'1. 오류내용: 저장된 closing_sync_data.pkl 이 없음.')
            print(f'2. 해결방법: {TestConfig.download_new_data}를 True로 수정필요\n')
            raise ValueError(f'데이터 오류 >> 신규 다운로드 필요함.')
        
        kline_data = utils._load_json(path_kline_data)
        kline_data_symbols = list(kline_data.keys())
        
        if kline_data_symbols != trading_config.symbols.value:
            __error_title(test_config)
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