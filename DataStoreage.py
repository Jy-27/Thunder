import utils
from typing import List, Union, Final, Optional
from dataclasses import dataclass, fields, field, asdict
import time
import ConfigSetting
class KlineData:
    """
    Binance에서 수신한 KlineData를 interval별 저장하기 위한 class __slots__형태의 데이터 타입

    사용시 Dict 타입으로 사용이 필요하며 그 예시는 아래와 같다.
        ### 초기 세팅
            >> data = {}
            >> kline_data = List[List[Union[int, str]]] 형태의 구성
            >> data['BTCUSDT'] = KlineData()
            >> data['BTCUSDT'].initialize_data(kline_data)

        ### 데이터 업데이트
            >> latest_data = kline_data[-1] 최종 데이터
            >> data['BTCUSDT'].update_entry(latest_data)

        ### 데이터 초기화
            >> data['BTCUSDT'].reset_data()

    본 class에 저장된 데이터를 활용하기 위하여 np.ndarray(object=data, dtype=float)처리가 필요하다.
    """

    __slots__ = [f"interval_{interval}" for interval in utils._info_kline_intervals()]

    def __init__(self):
        # 슬롯 초기화
        for interval in self.__slots__:
            setattr(self, interval, [])

    def __map_interval(self, latest_entry: List[Union[int, str]]) -> str:
        """
        주어진 Kline 엔트리에 적합한 interval 이름 반환.
        """
        close_time_index: int = 6
        open_time_index: int = 0
        ms_adjustment: int = 1
        ms_minute: int = 60_000
        
        start_timestamp: int = int(latest_entry[open_time_index])
        end_timestamp: int = int(latest_entry[close_time_index])
        if not (isinstance(start_timestamp, int) and isinstance(end_timestamp, int)):
            raise ValueError(f"kline_data 데이터 형태 불일치")

        timestamp_diff_minutes: int = (
            end_timestamp - start_timestamp + ms_adjustment
        ) // ms_minute

        return {
            1: "interval_1m",
            3: "interval_3m",
            5: "interval_5m",
            15: "interval_15m",
            30: "interval_30m",
            60: "interval_1h",
            120: "interval_2h",
            240: "interval_4h",
            360: "interval_6h",
            480: "interval_8h",
            720: "interval_12h",
            1_440: "interval_1d",
            4_320: "interval_3d",
            10_080: "interval_1w",
        }.get(timestamp_diff_minutes, "interval_1M")

    def set_data(self, kline_data: List[List[Union[int, str]]]):
        """
        kline_data초기 자료를 저장한다.
        """
        if not isinstance(kline_data, list) or not kline_data:
            raise ValueError("Invalid kline_data: Must be a non-empty list")

        latest_entry: List[Union[int, str]] = kline_data[-1]
        interval_name: str = self.__map_interval(latest_entry)

        setattr(self, interval_name, kline_data)

    def update_data(self, kline_data_latest: List[Union[int, str]]):
        """
        최신 Kline 데이터를 업데이트.
        """
        if not isinstance(kline_data_latest, list):
            raise ValueError("Invalid latest_entry: Must be a list")

        interval_name: str = self.__map_interval(kline_data_latest)
        interval_data: List[List[Union[int, str]]] = getattr(self, interval_name)

        # 데이터가 없는 경우
        if not interval_data:
            interval_data.append(kline_data_latest)
            # print("Interval 리스트가 비어 있어 데이터를 추가합니다.")
            return

        # 기존 데이터와 비교
        latest_start_time: int = int(kline_data_latest[0])
        latest_end_time: int = int(kline_data_latest[6])

        current_start_time: int = int(interval_data[-1][0])
        current_end_time: int = int(interval_data[-1][6])

        if (
            latest_start_time == current_start_time
            and latest_end_time == current_end_time
        ):
            interval_data[-1] = kline_data_latest
            # print("기존 데이터를 업데이트했습니다.")
        else:
            interval_data.append(kline_data_latest)
            # print("새로운 데이터를 추가했습니다.")

    def get_data(self, interval:str) -> List[List[Union[int, str]]]:
        return getattr(self, f'interval_{interval}')

    def reset_data(self):
        """
        모든 슬롯 데이터를 초기화 (빈 리스트로 재설정).
        """
        for interval in self.__slots__:
            setattr(self, interval, [])
        # print("모든 데이터를 초기화했습니다.")


@dataclass
class TradingLog:
    """
    Position 진입 주문 시 관련 정보를 기록하며, 이 데이터를 기반으로 거래 내역 및 현재 지갑 상태를 관리한다.
    힌트에서 Optional(None)으로 설정된 항목들은 거래 종료 후 또는 사후에 추가될 데이터들을 나타내며,
    속성값 배열의 정렬을 고려하여 기본값을 None으로 미설정 및 세부 설정은 삭제하였다.
    """
    
    ### 주문 관련 정보
    symbol: str  # 심볼 (예: BTCUSDT)
    position: int  # 포지션 유형 (1: Long, 2: Short)
    quantity: float  # 주문 수량
    hedge_enable: bool  # 헤지 여부 (진행 중인 포지션과 반대 방향의 주문 여부)
    leverage: int  # 레버리지 배율
    
    ### 가격 정보
    open_price: float  # 진입 가격 (Open Price)
    high_price: float  # 최고 가격
    low_price: float  # 최저 가격
    close_price: float  # 현재 가격 (Close Price)
    
    ### 거래정보
    strategy_no:int # 전략정보를 넣는다.

    ### 시간 정보
    start_timestamp: int  # 시작 타임스탬프
    end_timestamp: Optional[int]=None  # 현재 시간 타임스탬프(포지션 종료 시점)
    
    
    ### 손절 및 종료 설정
    scale_stop_enable: bool = True  # final 손절율 or scale 손절율 적용 여부
    initial_stop_rate:float = 0.015  # 초기 손절 비율
    trailing_stop_rate: float = 0.65  # 트레일링 손절 비율 (후기 손절 비율)
    reverse_position_ratio: float = 0  # 포지션과 반대의 흐름 비율 (반대 캔들 비율)
    time_based_adjustment_rate: float = 0.0007  # 시간 흐름에 따른 비율 조정 값
    adjusted_interval:str = '3m'    # 조종 변동 step
    adjusted_entry_price: Optional[float]=None  # 조정된 진입 가격 (StopLoss 기준)
    stop_loss_price: Optional[float]=None  # 손절 가격 또는 종료 가격

    ### 포지션 평가
    initial_value: Optional[float]=None  # 진입 시점의 평가 가치 (수수료 제외)
    current_value: Optional[float]=None  # 현재(종료) 시점의 평가 가치 (수수료 제외)
    net_pnl: float=0  # 순 손익 금액 (Net Profit or Loss, 수수료 제외)
    net_pnl_rate: float=0  # 순 손익 비율 (Net Profit or Loss Rate, 수수료 제외)
    gross_pnl: float=0  # 총 손익 금액 (Gross Profit or Loss, 수수료 포함)
    gross_pnl_rate: float=0  # 총 손익 비율 (Gross Profit or Loss Rate, 수수료 포함)

    
    ### 수수료 관련
    entry_fee: float=0  # 진입 수수료
    exit_fee: float=0  # 종료 수수료
    
    def __post_init__(self):
        """
        TradingLog 선언시 진입금액과 현재금액을 계산한다.
        """
        # 진입금액(마진)을 계산한다.
        if self.initial_value is None:
            self.initial_value = (self.open_price * self.quantity) / self.leverage
        # 현재금액을 계산한다.
        if self.current_value is None:
            self.current_value = (self.close_price * self.quantity) / self.leverage
    
    def update_trade_data(self, timestamp:int, price:Optional[Union[float, int]]=None, reverse_position_ratio:float=0, exit_fee:float=0):
        """
        신규 데이터를 TradingLog데이터에 반영 및 연산한다.
        """
        # 현재시간을 업데이트한다.
        self.end_timestamp = timestamp
        self.reverse_position_ratio = reverse_position_ratio
        self.exit_fee = exit_fee
        # price 데이터 입력시 포지션에 맞게 high_price or low_price를 업데이트 한다.
        if price is not None:
            if self.position == 1:
                self.high_price = max(self.high_price, price)
            elif self.position == 2:
                self.low_price = min(self.low_price, price)
            self.close_price = price
        
        # 현재 평가금액을 계산한다.
        self.__cals_value()
        # 손절 또는 종료연산에 필요한 값을 계산하고 포지션 종료여부를 결정한다.
        self.__cals_stop_loss()
    
    def __cals_value(self):
        """
        현재 평가금액, PNL을 계산한다. 
        """
        
        # 현재 평가금액 계산한다.
        self.current_value = (self.close_price * self.quantity) / self.leverage
        
        # 포지션에 따라서 수수료 제외한 pnl을 계산한다.
        if self.position == 1:
            self.net_pnl = self.current_value - self.initial_value
        elif self.position == 2:
            self.net_pnl = self.initial_value - self.current_value
        # 수수료 제외한 pnl의 비율을 계산한다.
        self.net_pnl_rate = self.net_pnl / self.initial_value
        
        
        # 수수료는 시장가 기준으로 0.05%를 적용했으며, 정확한 공식 적용이 어려우므로 슬리피지는 별도 적용하지 않는다.
        FEE_RATE:Final[float] = 0.0005
        # 테스트 모드 여부를 확인한다.
        if ConfigSetting.InitialSetup.mode:
            # 진입 수수료를 계산한다.
            self.entry_fee = (self.open_price * self.quantity * FEE_RATE)
            # 종료 수수료를 계산한다.
            self.exit_fee = (self.close_price * self.quantity * FEE_RATE)
        
        
        
        # 수수료 총 합계를 계산한다.
        total_fee = self.entry_fee + self.exit_fee
        # 수수료 비용을 포함한 pnl을 계산한다.
        self.gross_pnl = self.net_pnl - total_fee
        # 수수료 비용을 포함한 pnl비율을 계산한다.
        self.gross_pnl_rate = self.gross_pnl / self.initial_value
    
    
    def __cals_stop_loss(self):
        """
        스탑 또는 종료 관련값을 계산한다.
        """
        # interval값에 대한 밀리초 값을 구한다.
        target_ms_seconds = utils._get_interval_ms_seconds(self.adjusted_interval)
        # interval값 오입력시 프로그램 종료한다.
        if target_ms_seconds is None:
            # interval 값은 바이낸스 interval값을 기준으로 한다.
            raise ValueError(f'interval값이 유효하지 않음:{self.adjusted_interval}')
        # 종료 타임스템프와 시작타임스템프의 차이를 구한다.
        time_diff = self.end_timestamp - self.start_timestamp
        # 거래발생부터 현재시간을 interval값으로 나누어 횟수를 구하고 지정된 비율을 곱하여 추가적용할 비율을 계산한다.
        dynamic_time_rate = int(time_diff / target_ms_seconds) * self.time_based_adjustment_rate
        
        # 포지션이 롱일경우 스탑로스를 계산한다.
        if self.position == 1:
            # 설정상 scale_stop_enable이 참 일경우
            if self.scale_stop_enable:
                # 스탑로스 비율을 계산한다.
                stop_loss_rate = self.initial_stop_rate - (self.reverse_position_ratio + dynamic_time_rate)
                # 유동적 시작가를 계산한다.
                self.adjusted_entry_price = self.open_price * (1-stop_loss_rate)
                # 포지션을 종료 금액을 계산한다.
                self.stop_loss_price = self.adjusted_entry_price + ((self.high_price - self.adjusted_entry_price) * (1-stop_loss_rate))
            # 설정상 scale_stop_enable이 거짓일 경우
            else:
                # 포지션 종료 금액을 계산한다.
                self.stop_loss_price = self.high_price * (1-self.trailing_stop_rate)
            # 현재가격이 포지션 종료금액 이하시 True변환
            self.stop_trigger_enable = True if self.stop_loss_price >= self.close_price else False

        # 포지션이 숏일경우 스탑로스를 계산한다.
        elif self.position == 2:
            # 설정상 scale_stop_enable이 참 일경우
            if self.scale_stop_enable:
                # 스탑로스 비율을 계산한다.
                stop_loss_rate = self.initial_stop_rate - (self.reverse_position_ratio + dynamic_time_rate)
                # 유동적 시작가를 계산한다.
                self.adjusted_entry_price = self.open_price * (1+stop_loss_rate)
                # 포지션을 종료 금액을 계산한다.
                self.stop_loss_price = self.adjusted_entry_price - ((self.adjusted_entry_price - self.low_price) * (1-stop_loss_rate))
            
            else:
                # 포지션 종료 금액을 계산한다.
                self.stop_loss_price = self.low_price * (1+self.trailing_stop_rate)
            # 현재가격이 포지션 종료금액 이상시 True 반환
            self.stop_trigger_enable = True if self.stop_loss_price <= self.close_price else False