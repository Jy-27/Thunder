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
    account_safety_ratio: float = 0.2            # 계좌 안전 비율
    profit_preservation_enabled: bool = True     # 수익 보존 기능 활성화 여부
    order_allocation_ratio: float = 0.25         # 회당 주문 가능 금액 비율(계좌전체 보유 기준)
    max_leverage: int = 20                       # 최대 레버리지
    min_leverage: int = 2                        # 최소 레버리지
    reference_leverage: int = 1                  # 참고용 레버리지

    """
    손절가 조정
    손절가를 High 또는 Low값 기준 특정 비율초과시 signaldmf qkf
    """
    scaled_stop_loss_enabled: bool = True        # 조정 가능한 손절가 사용 여부
    stop_loss_threshold: float = 0.65            # 손절 기준 비율
    
    """
    동적 손절 설정
        > interval을 timestamp로 변환 후 해당 step마다 0.005비율을 적용하여
          시작가에 반영하여 수정한다. 수정된 시작가는 현재가와의 관계를 연산하여 설정된 값 도달시
          거래종료신호를 발생시킨다.
          
    """
    negative_candle_effect_enabled:bool=True            # 포지션 반대 캔들의 영향을 활성화 여부
    dynamic_stop_loss_enabled: bool = True       # 동적 손절 비율 사용 여부
    adjustment_rate: float = 0.005       # 동적 조정 비율
    adjustment_interval: str = '3m'      # 동적 조정 주기
    """
    연속 손실 발생시 대처
        > symbol 또는 전략 연속 손실 허용횟수를 지정하고 초과서 interval시간만큼 매수 대기
          현시점 기준 4시간 이전의 거래내역을 검토하여 지정 횟수 이상 손실발견시 거래 진입 거절 처리.
          반드시 필요한 안전설정.
    """
    reject_repeated_loss_orders_enabled: bool = True  # 반복 손실 주문 거부 여부
    loss_streak_reset_interval: str = '4h'       # 연속 손실 기준 시간
    max_allowed_loss_streak: int = 1             # 허용된 연속 손실 횟수(symbol기준)
    max_strategy_loss_streak: int = 3            # 허용된 연속 손실 횟수(전략기준)

    max_concurrent_positions: int = 2            # 최대 동시 거래 포지션 수
    initial_stop_loss_rate: float = 0.025        # 초기 손절 비율
    
    ### 분석 설정
    data_analysis_window_days: int = 1           # 데이터 분석 창(일 단위)

    ### 시스템 설정
    hedge_trading_enabled: bool = False          # 헤지 거래 활성화 여부


class SymbolConfig(Enum):
    """
    Live Trading시 symbol 수집기준 정립
    """
    core_symbols:Union[List[str], str] = ['BTCUSDT', 'XRPUSDT', 'ETHUSDT', 'TRXUSDT']
    update_hour:Optional[int] = None    # 업데이트 주기 시간
    
    @classmethod
    def validate_config(cls):
        ### symbols 오입력 검증


class TestConfig(Enum):
    test_symbols:Union[List[str], str] = ['BTCUSDT', 'XRPUSDT', 'ETHUSDT', 'TRXUSDT']
    seed_funds: float = 1_000  # 초기 자본금 / None값일경우 계좌 전체 금액 반영됨.
    start_datetime: str = '2025-1-20 09:00:00'  # 백테스트 시작 날짜
    end_datetime: str = '2025-1-21 08:59:59'  # 백테스트 종료 날짜
    download_new_data: bool = True  # 새로운 데이터 다운로드 여부

    @classmethod
    def validate_config(cls):
        error_messages = []
        min_config_amount = 10
        
        ### seed_funds 검증
        if not cls.seed_funds.value >= min_config_amount:
            message = (
                f"Error : {cls.__name__}.seed_funds\n"
                f"  1. 오류내용: 설정 금액이 최소거래금액보다 낮음.\n"
                f"  2. 해결방법: {cls.__name__}.seed_funds를 {min_config_amount}이상 입력\n"
            )
            error_messages.append(message)

        ## datetime 검증_1
        start_timestamp = utils._convert_to_timestamp_ms(cls.start_datetime.value)
        end_timestamp = utils._convert_to_timestamp_ms(cls.end_datetime.value)
        # 시작일과 종료일 크기 비교
        if not start_timestamp < end_timestamp:
            message = (
                f"Error : {cls.__name__}.start_datetime, end_datetime\n"
                f"  1. 오류내용: 시작일보다 종료일이 낮음.\n"
                f"  2. 해결방법: {cls.__name__}.start_datetime 또는 end_datetime을 수정\n"
            )
            error_messages.append(message)
            
        # 시간 오입력 검사
        start_time_str = '09:00:00'
        end_time_str = '08:59:59'
        
        if not start_time_str in cls.start_datetime.value:
            message = (
                f"Error : {cls.__name__}.start_datetime\n"
                f"  1. 오류내용: 시간입력 오류.\n"
                f"  2. 해결방법: {cls.__name__}.start_datetime의 시간 {start_time_str}입력\n"
            )
            error_messages.append(message)
        if not end_time_str in cls.end_datetime.value:
            message = (
                f"Error : {cls.__name__}.end_datetime\n"
                f"  1. 오류내용: 시간입력 오류.\n"
                f"  2. 해결방법: {cls.__name__}.end_datetime의 시간 {end_time_str}입력\n"
            )
            error_messages.append(message)
        
        # 기본주소
        base_path = os.path.dirname(os.getcwd())
        # 폴더명
        folder_name = 'DataStore'
        # 파일명 kline_data
        file_name_kline_data = 'kline_data.json'
        # 파일명 closing_data
        file_name_closing_data = 'closing_sync_data.pkl'
        # 파일주소 kline_data
        path_kline_data = os.path.join(base_path, folder_name, file_name_kline_data)
        # 파일주소 closing_data
        path_closing_sync_data = os.path.join(base_path, folder_name, file_name_kline_data)
        
        # 기존데이터 활용시 검증
        if not cls.download_new_data.value:
        
            if not os.path.exists(path_kline_data):
                message = (
                    f"Error : {cls.__name__}.download_new_data\n"
                    f"  1. 오류내용: {file_name_kline_data} 파일이 없음..\n"
                    f"  2. 해결방법: {cls.__name__}.download_new_data를 True입력(현재: {cls.download_new_data})\n"
                )
                error_messages.append(message)
            
            if not os.path.exists(path_closing_sync_data):
                message = (
                    f"Error : {cls.__name__}.download_new_data\n"
                    f"  1. 오류내용: {file_name_closing_data} 파일이 없음..\n"
                    f"  2. 해결방법: {cls.__name__}.download_new_data를 True입력(현재: {cls.download_new_data.value})\n"
                )
                error_messages.append(message)
            
            kline_data = utils._load_json(path_kline_data)
            kline_data_symbols = list(kline_data.keys())
            
            if not set(cls.test_symbols.value) == set(kline_data_symbols):
                message = (
                    f"Error : {cls.__name__}.test_symbols\n"
                    f"  1. 오류내용: symbols 데이터 정보 불일치.\n"
                    f"  2. 해결방법: {cls.__name__}.download_new_data 를 True 입력(현재: {cls.download_new_data.value})\n"
                )
                error_messages.append(message)
            
            
            
            intervals = list(kline_data[kline_data_symbols[0]].keys())
            select_data = kline_data[kline_data_symbols[0]][intervals[0]]
            
            is_start_timestamp = select_data[0][0] == start_timestamp
            is_end_timestamp = select_data[-1][6] == end_timestamp
            if not is_start_timestamp and not is_end_timestamp:
                message = (
                    f"Error : {cls.__name__}.test_symbols\n"
                    f"  1. 오류내용: 데이터 기간 정보 불일치.\n"
                    f"  2. 해결방법: {cls.__name__}.download_new_data 를 True 입력(현재: {cls.download_new_data.value})\n"
                )
                error_messages.append(message)
        
        if error_messages:
            for error_message in error_messages:
                print(error_message)
            raise ValueError(f"{cls.__name__} 검증 실패")
        print(f'{cls.__name__} 검증 성공')        
