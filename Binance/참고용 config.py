from enum import Enum
from typing import List, Union, Optional
import os
import Utils.BaseUtils as utils
import asyncio


class InitialSetup:
    mode:Optional[bool] = None  # 클래스 변수로 설정

    @classmethod
    def initialize(cls):
        cls.get_mode_input()

    @classmethod
    def get_mode_input(cls):
        while True:
            user_input = input("Test Mode: (y/n): ").strip().lower()  # 입력값 처리
            if user_input == "y":
                cls.mode = True
                print("Mode set to: Test Mode Enabled (True)")
                break
            elif user_input == "n":
                cls.mode = False
                print("Mode set to: Test Mode Disabled (False)")
                break
            else:
                print("y 또는 n 입력해야함. 다시 시도하세요.")


class SystemConfig(Enum):
    ### 데이터 수신 (LIVE MODE)
    websocket_reconnect_interval_hours: int = 2  # 웹소켓 재연결 주기 (시간 단위)
    ### 분석 설정
    data_analysis_window_days: int = 2  # 데이터 분석 창(일 단위)

    ### 트레이드 히스토리 적용 범위(hr)
    trade_history_range:int = 24

    ### 폴더이름 (전체)
    parent_folder_path = os.path.dirname(os.getcwd())
    api_folder_name = "API"
    data_folder_name = "DataStore"

    ### 파일이름 (전체))
    api_binance = "binance.json"
    api_telegram = "telegram.json"
    test_trade_history = "test_trade_history.json"
    live_trade_history = "live_trade_history.json"
    
    kline_data = 'kline_data.json'
    closing_sync_data = "closing_sync_data.pkl"

    path_binance_api = os.path.join(parent_folder_path, api_folder_name, api_binance)
    path_telegram_api = os.path.join(parent_folder_path, api_folder_name, api_telegram)
    path_test_trade_history = os.path.join(parent_folder_path, data_folder_name, test_trade_history)
    path_live_trade_history = os.path.join(parent_folder_path, data_folder_name, test_trade_history)

    path_kline_data = os.path.join(parent_folder_path, data_folder_name, kline_data)
    path_closing_sync_data = os.path.join(parent_folder_path, data_folder_name, closing_sync_data)

class SymbolConfig(Enum):
    """
    라이브 트레이딩에 필요한 symbol정보 설정
    """

    core_symbols: Union[List[str], str] = ["BTCUSDT", "XRPUSDT", "ETHUSDT", "TRXUSDT"]
    update_hour: Optional[int] = None  # 업데이트 주기 시간 (라이브 트레이딩 전용)
    market_type: str = "Futures"  # 시장 유형 (라이브 트레이딩 전용)

    @classmethod
    async def validate_config(cls):
        error_messages = []

        # 순환참조 방지 지연임포트
        import MarketDataFetcher
        # 시장 유형에 따른 MarketDataFetcher 인스턴스 생성
        if cls.market_type.value == "Futures":
            ins_market = MarketDataFetcher.FuturesMarket()
        elif cls.market_type.value == "Spot":
            ins_market = MarketDataFetcher.SpotMarket()
        else:
            message = (
                f"Error : {cls.__name__}.market_type\n"
                f"  1. 오류내용: market_type 값 입력 오류.\n"
                f"  2. 해결방법: {cls.__name__}.market_type을 'Futures' 또는 'Spot' 중 하나로 설정하십시오.\n"
                f"  현재 설정값: {cls.market_type}\n"
            )
            error_messages.append(message)

        # 24시간 심볼 데이터 수집 및 필터링
        symbols_24hr = await ins_market.fetch_24hr_ticker()
        symbols = [
            data["symbol"] for data in symbols_24hr if data["symbol"].endswith("USDT")
        ]

        # core_symbols 검증

        error_symbol_name = []
        for symbol in cls.core_symbols.value:
            if not symbol in symbols:
                error_symbol_name.append(symbol)

        if error_symbol_name:
            message = (
                f"Error : {cls.__name__}.core_symbols\n"
                f"  1. 오류내용: 오입력 symbol값 존재함.\n"
                f"  2. 해결방법: {cls.__name__}.core_symbols 재검(오류symbol: {error_symbol_name}).\n"
            )
            error_messages.append(message)

        # 오류 메시지 출력 및 예외 처리
        if error_messages:
            for error_message in error_messages:
                print(error_message)
            raise ValueError(f"{cls.__name__} 검증 실패")

        print(f"{cls.__name__} 검증 성공")


class SafetyConfig(Enum):
    reject_repeated_loss_orders_enabled: bool = True  # 반복 손실 주문 거부 여부
    loss_streak_reset_interval: str = "4h"  # 연속 손실 기준 시간
    max_allowed_loss_streak: int = 1  # 허용된 연속 손실 횟수(symbol기준)
    max_strategy_loss_streak: int = 3  # 허용된 연속 손실 횟수(전략기준)
    profit_preservation_enabled: bool = True  # 수익 보존 기능 활성화 여부
    profit_preservation_amount: float = (
        0  # 수익 보존 기준 금액 (해당 금액 초과금은 Spot계좌로 이체처리.)
    )
    ### 시스템 설정
    account_safety_ratio: float = 0.5  # 계좌 안전 비율


class TelegramConfig(Enum):
    status_message_send_enabled: bool = False  # 메시지 전송 여부
    status_message_interval_minutes: int = 10  # 상태 메시지 발송 주기
    open_position_message_enabled: bool = False  # 포지션 진입 시 메시지 발송 여부
    close_position_message_enabled: bool = False  # 포지션 종료 시 메시지 발송 여부
    account_balance_message_enabled: bool = False  # 계좌정보 메시지 발송여부

    @classmethod
    def validate_config(cls):
        error_messages = []

        if not isinstance(cls.status_message_send_enabled.value, bool):
            message = (
                f"Error : {cls.__name__}.status_message_send_enabled\n"
                f" 1. 오류내용: type 입력 오류\n"
                f" 2. 해결방법: {cls.__name__}.status_message_send_enabled를 True or False 입력\n"
                f" 3. 현재설정: {cls.status_message_send_enabled.value}\n"
            )
            error_messages.append(message)

        if (
            not cls.status_message_send_enabled.value
            and cls.open_position_message_enabled.value
        ):
            message = (
                f"Error : {cls.__name__}.open_position_message_enabled\n"
                f" 1. 오류내용: status_message_send_enabled가 False일때 open_position_message_enabled도 False만 가능.\n"
                f" 2. 해결방법: {cls.__name__}.open_position_message_enabled에 False값 입력.\n"
                f" 3. 현재설정: {cls.cls.open_position_message_enabled.value}\n"
            )
            error_messages.append(message)

        if (
            not cls.status_message_send_enabled.value
            and cls.close_position_message_enabled.value
        ):
            message = (
                f"Error : {cls.__name__}.close_position_message_enabled\n"
                f" 1. 오류내용: status_message_send_enabled가 False일때 close_position_message_enabled도 False만 가능.\n"
                f" 2. 해결방법: {cls.__name__}.close_position_message_enabled에 False값 입력.\n"
                f" 3. 현재설정: {cls.cls.close_position_message_enabled.value}\n"
            )
            error_messages.append(message)

        if (
            not cls.status_message_send_enabled.value
            and cls.account_balance_message_enabled.value
        ):
            message = (
                f"Error : {cls.__name__}.account_balance_message_enabled\n"
                f" 1. 오류내용: status_message_send_enabled가 False일때 close_position_message_enabled도 False만 가능.\n"
                f" 2. 해결방법: {cls.__name__}.account_balance_message_enabled False값 입력.\n"
                f" 3. 현재설정: {cls.cls.account_balance_message_enabled.value}\n"
            )
            error_messages.append(message)

            # 오류 메시지 출력 및 예외 처리
        if error_messages:
            for error_message in error_messages:
                print(error_message)
            raise ValueError(f"{cls.__name__} 검증 실패")

        print(f"{cls.__name__} 검증 성공")


class OrderConfig(Enum):
    """
    주문시 필요한 설정정보
    """

    hedge_trading_enabled: bool = True  # 헤지 거래 활성화 여부
    max_leverage: int = 125  # 최대 레버리지
    min_leverage: int = 5  # 최소 레버리지
    reference_leverage: Union[int, float] = 1  # 참고용 레버리지
    order_allocation_ratio: Optional[float] = None  # 회당 주문 가능 금액 비율
    order_allocation_amount: Optional[float] = (
        342.86  # 회당 주문 가능 금액 (자산이 해당금액보다 낮아질경우 셧다운 처리할 것.)
    )
    max_concurrent_positions: int = 2  # 최대 동시 거래 포지션 수
    margin_mode: str = "cross"

    @classmethod
    async def validate_config(cls):
        error_messages = []

        ### 해지거래 관련 설정 검토
        if not isinstance(cls.hedge_trading_enabled.value, bool):
            message = (
                f"Error : {cls.__name__}.hedge_trading_enabled\n"
                f" 1. 오류내용: type 입력 오류\n"
                f" 2. 해결방법: {cls.__name__}.hedge_trading_enabled를 True or False입력\n"
                f" 3. 현재설정: {cls.hedge_trading_enabled.value}\n"
            )
            error_messages.append(message)

        ### 최대 레버리지 설정 검토
        if not cls.max_leverage.value <= 125:
            message = (
                f"Error : {cls.__name__}.hedge_trading_enabled\n"
                f" 1. 오류내용: Leverage 시스템 최대치 초과\n"
                f" 2. 해결방법: {cls.__name__}.max_leverage를 125이하로 입력\n"
                f" 3. 현재설정: {cls.max_leverage.value}\n"
            )
            error_messages.append(message)

        if not cls.max_leverage.value > 0:
            message = (
                f"Error : {cls.__name__}.hedge_trading_enabled\n"
                f" 1. 오류내용: Leverage 시스템 최소치 미달\n"
                f" 2. 해결방법: {cls.__name__}.max_leverage를 1이상 입력\n"
                f" 3. 현재설정: {cls.max_leverage.value}\n"
            )
            error_messages.append(message)

        if not isinstance(cls.max_leverage.value, int):
            message = (
                f"Error : {cls.__name__}.max_leverage\n"
                f" 1. 오류내용: 입력타입 오류\n"
                f" 2. 해결방법: {cls.__name__}.max_leverage 정수 입력\n"
                f" 3. 현재설정: {type(cls.max_leverage.value)}\n"
            )
            error_message.append(message)

        ### 최소 레버리지 설정 검토
        if not cls.min_leverage.value <= 125:
            message = (
                f"Error : {cls.__name__}.min_leverage\n"
                f" 1. 오류내용: Leverage 시스템 최대치 초과\n"
                f" 2. 해결방법: {cls.__name__}.min_leverage를 125이하로 입력\n"
                f" 3. 현재설정: {cls.min_leverage.value}\n"
            )
            error_messages.append(message)

        if not cls.min_leverage.value > 0:
            message = (
                f"Error : {cls.__name__}.min_leverage\n"
                f" 1. 오류내용: Leverage 시스템 최소치 미달\n"
                f" 2. 해결방법: {cls.__name__}.min_leverage를 1이상 입력\n"
                f" 3. 현재설정: {cls.min_leverage.value}\n"
            )
            error_messages.append(message)

        if not isinstance(cls.min_leverage.value, int):
            message = (
                f"Error : {cls.__name__}.min_leverage\n"
                f" 1. 오류내용: 입력타입 오류\n"
                f" 2. 해결방법: {cls.__name__}.min_leverage 정수 입력\n"
                f" 3. 현재설정: {type(cls.min_leverage.value)}\n"
            )
            error_message.append(message)

        ### 참고용 레버리지 설정 검토
        if not isinstance(cls.reference_leverage.value, (int, float)):
            message = (
                f"Error : {cls.__name__}.reference_leverage\n"
                f" 1. 오류내용: 입력타입 오류\n"
                f" 2. 해결방법: {cls.__name__}.reference_leverage값을 int or float타입으로 입력\n"
                f" 3. 현재설정: {type(cls.reference_leverage.value)}\n"
            )
            error_messages.append(message)

        ### 주문 금액 설정 검토
        if (
            cls.order_allocation_ratio.value is not None
            and cls.order_allocation_ratio.value >= 1
        ):
            message = (
                f"Error : {cls.__name__}.order_allocation_ratio\n"
                f" 1. 오류내용: 입력값 오류\n"
                f" 2. 해결방법: {cls.__name__}.order_allocation_ratio는 1미만 값 입력\n"
                f" 3. 현재설정: {cls.order_allocation_ratio.value}\n"
            )
            error_messages.append(message)

        if (
            cls.order_allocation_amount.value is None
            and cls.order_allocation_ratio.value is None
        ):
            message = (
                f"Error : {cls.__name__}.order_allocation_ratio\n"
                f"Error : {cls.__name__}.order_allocation_amount\n"
                f" 1. 오류내용: 입력 오류\n"
                f" 2. 해결방법: 두 값중 하나만 값 입력할 것.(둘중 하나만 값 입력할 것)\n"
                f" 3. 현재설정: amount -({cls.order_allocation_amount.value})\n"
                f"            ratio - ({cls.order_allocation_ratio.value})\n"
            )
            error_messages.append(message)

        # 순환참조 방지 지연임포트
        import TradeClient
        if SymbolConfig.market_type.value == "Futures":
            ins_client = TradeClient.FuturesClient()
        elif SymbolConfig.market_type.value == "Spot":
            ins_client = TradeClient.SpotClient()

        total_balance = await ins_client.get_total_wallet_balance()
        available_ratio = 1 - SafetyConfig.account_safety_ratio.value
        live_available_funds = total_balance * available_ratio
                
        # live trading 조건을 변수로 분리
        is_live_mode = not InitialSetup.mode
        is_live_valid_allocation = (
            cls.order_allocation_amount.value is not None
            and live_available_funds >= cls.order_allocation_amount.value
        )

        # live trading 조건문에서 사용
        if is_live_mode and not is_live_valid_allocation:
            message = (
                f"Error : {cls.__name__}.order_allocation_amount\n"
                f" 1. 오류내용: 보유 자산보다 주문 금액이 더 높음.\n"
                f" 2. 해결방법: {cls.__name__}.order_allocation_amount값을 {live_available_funds:,.2f} 이하로 설정\n"
                f" 3. 현재설정: {cls.order_allocation_amount.value}\n"
            )
            error_messages.append(message)

        test_available_funds = TestConfig.seed_funds.value * available_ratio
        # test trading 조건을 변수로 분리
        is_test_mode = InitialSetup.mode
        is_test_valid_allocation = (
            cls.order_allocation_amount.value is not None
            and test_available_funds >= cls.order_allocation_amount.value
        )

        # live trading 조건문에서 사용
        if is_test_mode and not is_test_valid_allocation:
            message = (
                f"Error : {cls.__name__}.order_allocation_amount\n"
                f" 1. 오류내용: 보유 자산보다 주문 금액이 더 높음.\n"
                f" 2. 해결방법: {cls.__name__}.order_allocation_amount값을 {test_available_funds:,.2f} 이하로 설정\n"
                f" 3. 현재설정: {cls.order_allocation_amount.value}\n"
            )
            error_messages.append(message)

        if (
            cls.order_allocation_amount.value is not None
            and cls.order_allocation_ratio.value is not None
        ):
            message = (
                f"Error : {cls.__name__}.order_allocation_ratio\n"
                f"Error : {cls.__name__}.order_allocation_amount\n"
                f" 1. 오류내용: 입력 오류\n"
                f" 2. 해결방법: 두 값중 하나만 값 입력할 것.(둘중 하나만 값 입력할 것)\n"
                f" 3. 현재설정: amount - ({cls.order_allocation_amount.value})\n"
                f"            ratio - ({cls.order_allocation_ratio.value})\n"
            )
            error_messages.append(message)

        ### 포지션 보유 수량 관련
        if not isinstance(cls.max_concurrent_positions.value, int):
            message = (
                f"Error : {cls.__name__}.max_concurrent_positions\n"
                f" 1. 오류내용: 타입 입력 오류\n"
                f" 2. 해결방법: 정수값을 입력할 것.\n"
                f" 3. 현재설정: {type(cls.max_concurrent_positions.value)}\n"
            )
            error_messages.append(message)

        ### 마진모드 설정
        mode_allowed_range = ["cross", "isolated"]

        if not cls.margin_mode.value.lower() in mode_allowed_range:
            message = (
                f"Error : {cls.__name__}.margin_mode\n"
                f" 1. 오류내용: 입력오류\n"
                f' 2. 해결방법: {", ".join(mode_allowed_range)}" 중 1개 선택 입력\n'
                f" 3. 현재설정: {cls.margin_mode.value}"
            )
            error_messages.append(message)
        # 오류 메시지 출력 및 예외 처리
        if error_messages:
            for error_message in error_messages:
                print(error_message)
            raise ValueError(f"{cls.__name__} 검증 실패")

        print(f"{cls.__name__} 검증 성공")


class StopLossConfig(Enum):
    """
    손절가 조정
    손절가를 High 또는 Low값 기준 특정 비율초과시 signaldmf qkf
    """

    scaled_stop_loss_enabled: bool = True  # 조정 가능한 손절가 사용 여부
    stop_loss_threshold: float = 0.65  # 손절 기준 비율
    """
    동적 손절 설정
        > interval을 timestamp로 변환 후 해당 step마다 0.005비율을 적용하여
          시작가에 반영하여 수정한다. 수정된 시작가는 현재가와의 관계를 연산하여 설정된 값 도달시
          거래종료신호를 발생시킨다.
    """
    negative_candle_effect_enabled: bool = False  # 포지션 반대 캔들의 영향을 활성화 여부
    negative_reference_rate: float = 0.2 #반대 캔들 비율의 조정율
    dynamic_stop_loss_enabled: bool = True  # 동적 손절 비율 사용 여부
    adjustment_rate: float = 0.005  # 동적 조정 비율
    adjustment_interval: str = "3m"  # 동적 조정 주기
    """
    연속 손실 발생시 대처
        > symbol 또는 전략 연속 손실 허용횟수를 지정하고 초과서 interval시간만큼 매수 대기
          현시점 기준 4시간 이전의 거래내역을 검토하여 지정 횟수 이상 손실발견시 거래 진입 거절 처리.
          반드시 필요한 안전설정.
    """
    initial_stop_loss_rate: float = 0.025  # 초기 손절 비율


class TestConfig(Enum):
    """
    백테스트에 필요한 정보를 설정
    """

    test_symbols: Union[List[str], str] = ["BTCUSDT", "XRPUSDT", "ETHUSDT", "TRXUSDT"]
    # test_symbols: Union[List[str], str] = ["TRXUSDT"]
    seed_funds: Union[float, int] = 6857.3  # 초기 자본금 / None값일경우 계좌 전체 금액 반영됨.
    start_datetime: str = "2024-12-1 09:00:00"  # 백테스트 시작 날짜
    end_datetime: str = "2025-1-1 08:59:59"  # 백테스트 종료 날짜
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
        start_timestamp = utils.convert_to_timestamp_ms(cls.start_datetime.value)
        end_timestamp = utils.convert_to_timestamp_ms(cls.end_datetime.value)
        # 시작일과 종료일 크기 비교
        if not start_timestamp < end_timestamp:
            message = (
                f"Error : {cls.__name__}.start_datetime, end_datetime\n"
                f"  1. 오류내용: 시작일보다 종료일이 낮음.\n"
                f"  2. 해결방법: {cls.__name__}.start_datetime 또는 end_datetime을 수정\n"
            )
            error_messages.append(message)

        # 시간 오입력 검사
        start_time_str = "09:00:00"
        end_time_str = "08:59:59"

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
        folder_name = "DataStore"
        # 파일명 kline_data
        file_name_kline_data = "kline_data.json"
        # 파일명 closing_data
        file_name_closing_data = "closing_sync_data.pkl"
        # 파일주소 kline_data
        path_kline_data = os.path.join(base_path, folder_name, file_name_kline_data)
        # 파일주소 closing_data
        path_closing_sync_data = os.path.join(
            base_path, folder_name, file_name_kline_data
        )

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

            kline_data = utils.load_json(path_kline_data)
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
        print(f"{cls.__name__} 검증 성공")


async def run():
    await SymbolConfig.validate_config()
    await OrderConfig.validate_config()
    TelegramConfig.validate_config()
    TestConfig.validate_config()

if __name__ == "__main__":
    InitialSetup.initialize()
    asyncio.run(run())
