import DataProcess
import os
import utils
import asyncio
import nest_asyncio
import pickle
import Analysis
from pprint import pprint
import matplotlib.pyplot as plt
from matplotlib import style, ticker
from typing import Optional, List, Union


class BackTester:
    def __init__(
        self,
        symbols: str,
        # intervals: List[str],
        seed_money: Union[int, float],
        start_date: Union[int, float],
        end_date: Union[int, float],
        max_trade_number: int = 3,
        init_stop_rate: float = 0.015,
        adj_interval: str = "3m",
        start_step: int = 5_000,
        adj_rate: float = 0.0007,
        is_use_scale_stop: bool = True,
        adj_timer: bool = True,
        stop_loss_rate: float = 0.025,
        safety_balance_ratio: float = 0.2,
        is_download: bool = True,
        max_leverage: Optional[int] = None,
        # 주문신호 유효성 검토(브레이크 기능)
        is_order_break: bool = True,
        loss_chance: int = 2,
        step_interval: str = "2h",
        comparison: str = "above",
        absolute: bool = True,
        value: int = 350_000_000,
        percent: float = 0.03,
        quote_type: str = "usdt",
    ):
        self.symbols = [symbol.upper() for symbol in symbols]
        # intervals값은 Analysis에서 전담으로 관리하다. 분석 항목기준으로 interval을 구성했다.
        self.intervals = Analysis.IntervalConfig.target_interval
        self.start_date = start_date
        self.end_date = end_date
        # 전체 금액에서 안전금액 비율
        self.safety_balance_ratio = safety_balance_ratio
        self.stop_loss_rate = stop_loss_rate
        self.is_download = is_download
        self.adj_timer = adj_timer
        self.adj_rate = adj_rate
        self.adj_interval = adj_interval
        self.is_use_scale_stop = is_use_scale_stop
        self.max_leverage = max_leverage
        # 반복적인 손실발생시 해당 시나리오는 브레이크 타임을 갖는다.
        self.is_order_break = is_order_break
        # 시나리오 브레이크임 진입전 손실 횟수
        self.loss_chance: Optional[int] = loss_chance if self.is_order_break else None
        # 브레이크타임을 시간 지정 : interval값을 밀리미터로 변환.
        self.step_interval: Optional[str] = (
            step_interval if self.is_order_break else None
        )
        # TradingLog에 기록한다. 앞으로 어떻게 사용할지 고민중...
        self.test_mode: bool = True
        # 데이터를 pickle로 저장 및 로딩해야하며, 컨테이너화 하지 않는다.
        self.closing_sync_data: Optional[Dict[str, Dict[str, List[Any]]]] = None
        self.test_manager_ins = DataProcess.TestDataManager(
            symbols=self.symbols,
            intervals=self.intervals,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.test_data_manager_ins = DataProcess.TestProcessManager(
            max_leverage=self.max_leverage
        )
        self.analysis_ins = Analysis.AnalysisManager(intervals=self.intervals)
        self.seed_money = seed_money
        self.trade_analysis_ins = DataProcess.TradeAnaylsis(
            initial_balance=self.seed_money
        )
        self.constraint = DataProcess.OrderConstraint()
        self.symbol_map = None
        self.interval_map = None
        self.closing_indices_data = None
        self.target_run_interval = "map_1m"
        self.max_trade_number = max_trade_number
        self.start_step = start_step
        self.init_stop_rate = init_stop_rate

        # interval별 데이털르 저장하는 데이터셋
        self.interval_dataset = utils.DataContainer()

    # 저장데이터의 주소값을 확보한다.
    def __get_data_path(self):
        """
        1. 기능 : 백테스트에 적용될 kline_data의 주소값을 반환한다.
        2. 매개변수 : 해당없음.
        """
        # 파일명 - 속성명에 지정함.
        file_name = self.test_manager_ins.kline_closing_sync_data
        # 폴더명 - 속성명에 지정함.
        folder_name = self.test_manager_ins.storeage
        # 상위폴도명 - 함수로 확보
        base_directory = os.path.dirname(os.getcwd())
        # 주소 합성 - 상위폴더 + 폴더명 + 파일명
        path = os.path.join(base_directory, folder_name, file_name)
        # 주소 반환.
        return path

    # closing_sync_data의 유효성을 점검한다.
    def __validate_base_data(self):
        """
        1. 기능 : closing_sync_data의 유효성을 점검한다. symbol정보만 점검하며, interval데이터는 검토하지 않는다.
                (할 수 있응나 귀찮아서. [np.array화 하여 [0]index timestamp를 기준으로 전체 찾고 시작과 긑의 값 차이를 비교하여 interval 밀리초를 계산])
        2. 매개변수 : 해당없음.
        """
        # 속성에 데이터가 없다면,
        if not self.closing_sync_data:
            # 에러 발생
            raise ValueError(f"closing_sync_data가 비어있음.")
        #
        for symbol, _ in self.closing_sync_data.items():
            if not symbol in self.symbols:
                raise ValueError(f"closing_sync_data의 symbol정보 불일치: {symbol}")

    # 백테스트에 사용될 데이터를 로딩 또는 수신한다.
    async def get_base_data(self, is_save: bool = False):
        """
        1. 기능 : 백테스트에 사용될 데이터를 로딩 또는 수신한다.
        2. 매개변수
            1) is_save : 데이터를 저장할지 여부를 결정한다.
        """
        # 기존 데이터 로딩시
        if not self.is_download:
            # 파일 주소를 생성하고
            path = self.__get_data_path()
            # 해당 주소에 파일 존재여부를 점검
            # 파일 미존재시
            if not os.path.isfile(path):
                # 에러 발생시키고 중단
                raise ValueError(f"파일이 존재하지 않음: {path}")
            # 파일 존재시
            else:
                # 해당 파일을 불러온다.
                with open(path, "rb") as file:
                    self.closing_sync_data = pickle.load(file)
                    return
        # 신규 다운로드 선택시
        else:
            # kline data를 수신한다.
            data = await self.test_manager_ins.generate_kline_interval_data(
                save=is_save
            )
            # 데이터를 np.array타입으로 변환한다.
            data_array = utils._convert_kline_data_array(data)
            # closing_sync 데이터를 생성 및 속성에 저장한다.
            self.closing_sync_data = self.test_manager_ins.generate_kline_closing_sync(
                kline_data=data_array, save=is_save
            )

    # closing_sync 데이터의 index 데이터를 생성한다.
    async def get_indices_data(self):
        """
        1. 기능 : closing_sync_data의 index데이터를 생성한다.
        2. 매개변수 : 해당없음.
        """

        # symbol map, interval map, closing_indices데이터를 생성(self.get_base_data로 생성된 속성값 적용.)
        self.symbol_map, self.interval_map, self.closing_indices_data = (
            utils._convert_to_container(self.closing_sync_data)
        )
        # closing_sync index데이터를 생성 및 속성에 저장한다.
        self.test_manager_ins.get_indices_data(
            data_container=self.closing_indices_data, lookback_days=1
        )

    # 현재 진행중인 포지션이 있다면, 최종 정보를 업데트한다.(단가, 현재타임스템프)
    # 업데이트 후 StopLoss 조건 성립시 포지션 종료 신호(True)를 반환한다.
    def update_trade_info(self, symbol: str, data):
        """
        1. 기능 : 진행중인 포지션이 있다면, 최종 데이터를 업데이트한다. 업데이트 후 포지션 종료 여부를 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) data : closing_sync_data 해당 index조회 값.
        """

        # 현재 가격
        price = data[-1][4]
        # 현재 타임스템프
        close_timestamp = data[-1][6]
        # 해당 symbol이 현재 진행중인 포지션이 있는지 확인한다.
        if symbol in self.trade_analysis_ins.open_positions:
            # 현재 포지션 유지중이라면 데이터를 업데이트한다.
            # 포지션 종료신호를 반환한다. (True / False)
            return self.trade_analysis_ins.update_log_data(
                symbol=symbol, price=price, timestamp=close_timestamp
            )
        # 현재 포지션이 없다면,
        else:
            # 아무것도 하지 않고 포지션 종료 거절신호(False)를 반환한다.
            return False

    # position open전 주문 유효 점검 및 주문가능수량을 반환한다.
    async def __validate_open_signal(
        self, symbol: str, price: float
    ):  # , leverage: int):
        """
        1. 기능 : position open전 주문 유효 점검 및 주문 가능 수량을 계산 반환한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) price : 진입가격
        3. 추가사항
            - 주문 전 open_position 사전 점검하기는 한다만...혹시 모르니 추가했다.
        """
        if self.__validate_cloes_position(symbol=symbol):
            return False, 0, 0
        else:
            total_balance = self.trade_analysis_ins.total_balance
            conctraint = self.constraint.calc_fund(
                funds=total_balance,
                safety_ratio=self.safety_balance_ratio,
                count_max=self.max_trade_number,
            )
            trade_balance = conctraint.get("tradeValue")
            trade_count = conctraint.get("count")

            if self.max_leverage is None:
                leverage = leverage
            else:
                leverage = self.max_leverage

            # 주문 신호 발생기
            status, qty, lv = await self.test_data_manager_ins.calculate_order_values(
                symbol=symbol,
                leverage=leverage,
                balance=trade_balance,
                market_type="futures",
            )
            margin_ = (qty / leverage) * price
            is_cash_margin = self.trade_analysis_ins.cash_balance > margin_
            is_trade_count = self.trade_analysis_ins.number_of_stocks < trade_count

            if not status or not is_cash_margin or not is_trade_count:
                return False, 0, 0
            else:
                return True, qty, lv

    # symbol값 기준 포지션 유지여부 확인
    def __validate_cloes_position(self, symbol: str):
        """
        1. 기능 : symbol값 기준 포지션 유지여부를 확인한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
        """

        if symbol in self.trade_analysis_ins.open_positions:
            return True
        else:
            return False

    # open 주문을 생성한다.
    async def active_open_position(
        self,
        symbol: str,
        price: float,
        position: int,
        start_timestamp: int,
        scenario_type: int,
        leverage: Optional[int] = None,
    ):
        """
        1. 기능 : position open 주문을 생성한다.
        2. 매개변수
            1) symbol : 쌍거래 symbol
            2) price : 진입가격
            3) position : 1:long, 2:short
            4) start_timestamp : 시작 타임스템프
            5) secnario_type : int() / 시나리오 종류
            6) leverage : 레버리지
        """

        # 주문전 유효성 검사
        is_open_signal, quantity, leverage = await self.__validate_open_signal(
            symbol=symbol, price=price
        )

        # 주문 유혀성 검토 결과 False면,
        if not is_open_signal:
            # 함수 종료
            return

        # 브레이크 타임 설정시
        if self.is_order_break:
            # 기존 거래내역을 검토해서 브레이크 타임 적용여부 검토
            is_loss_scnario = self.trade_analysis_ins.validate_loss_scenario(
                symbol=symbol,
                scenario=scenario_type,
                chance=self.loss_chance,
                step_interval=self.step_interval,
                current_timestamp=start_timestamp,
            )
            # 브레이크 타임 해당될경우
            if not is_loss_scnario:
                # 함수 종료
                return

        # 브레이크 타임 검토 후 미적용시 주문정보 생성.
        log_data = DataProcess.TradingLog(
            symbol=symbol,
            start_timestamp=start_timestamp,
            entry_price=price,
            position=position,
            quantity=quantity,
            leverage=leverage,
            trade_scenario=scenario_type,
            test_mode=self.test_mode,
            stop_rate=self.stop_loss_rate,
            init_stop_rate=self.init_stop_rate,
            adj_timer=self.adj_timer,
            adj_rate=self.adj_rate,
            adj_interval=self.adj_interval,
            use_scale_stop=self.is_use_scale_stop,
        )
        # 주문 정보를 추가
        self.trade_analysis_ins.add_log_data(log_data=log_data)

    # 포지션 종료를 위한 함수.
    def active_close_position(self, symbol: str):
        # 포지션 종료 신호를 수신해도 symbol값 기준으로 position 유효성 검토한다.
        if self.__validate_cloes_position(symbol=symbol):
            # 유효성 확인시 해당 내용을 제거한다.
            self.trade_analysis_ins.remove_order_data(symbol=symbol)

    # 백테스트 시작시 현재 설정정보를 출력한다.
    def start_masage(self):
        """
        1. 기능 : 백테스트 시작시 현재 설정 정보를 출력한다.
        2. 매개변수 : 해당없음.
        """
        header = "=" * 100
        print(f"\n {header}\n")
        print(f"    ***-=-=-<< BACK TESTING >>-=-=-***\n")
        print(f"    1.  StartDate  : {self.start_date}")
        print(f"    2.  EndDate    : {self.end_date}")
        print(f"    3.  Symbols    : {self.symbols}")
        print(f"    4.  SeedMoney  : {self.seed_money:,.2f} USDT")
        print(f"    5.  leverage   : {self.max_leverage}x")
        print(f"    6.  Intervals  : {self.intervals}")
        print(f"    7.  ScaleStop  : {self.is_use_scale_stop}")
        print(f"    8.  StopRate   : {self.stop_loss_rate*100:.2f} %")
        print(f"    9.  AdjTimer   : {self.adj_timer}")
        print(f"    10. OrderBreak : {self.is_order_break}")
        print(f"\n {header}\n")
        print("     DateTime       Trading  trade_count   PnL_Ratio       Gross_PnL")

    # 백테스트 실행.
    async def run(self):
        """
        1. 기능 : 각종 기능을 집합하여 시계 데이터 loop 생성하고 가상의 거래를 진행한다.
        2. 매개변수 : 해당없음.
        """
        await self.get_base_data()
        self.__validate_base_data()
        await self.get_indices_data()
        self.start_masage()

        ### 데이터 타임루프 시작 ###
        for idx, data in enumerate(
            self.closing_indices_data.get_data(self.target_run_interval)
        ):
            if idx <= self.start_step:
                # utils._std_print(idx)
                continue
            # interval 기준이므로 end_timestamp는 for문 이탈시 가장 큰 값을 가진다.
            # list에 값을 추가하여 for문 종료시 min값(1분) 확보한다.
            # timestamp_min값을 초기화 한다.
            timestamp_min = []

            ### 분석에 사용될 데이터셋 초기화 ###
            self.analysis_ins.reset_cases()
            self.interval_dataset.clear_all_data()

            for interval in self.intervals:
                maps_ = self.closing_indices_data.get_data(f"map_{interval}")[idx]
                data = self.closing_indices_data.get_data(f"interval_{interval}")[maps_]

                ### 데이터셋으로 저장한다 ###

                symbol = self.symbols[maps_[0]]
                price = data[-1][4]
                end_timestamp = data[-1][6]

                timestamp_min.append(end_timestamp)

                ### 업데이트 및 이탈 검토 ###
                if interval == self.intervals[0]:
                    # 현재 정보 업데이트와 동시에 stop signal 정보를 조회한다.
                    update_and_stop_signal = self.update_trade_info(
                        symbol=symbol, data=data
                    )
                    if update_and_stop_signal:
                        self.active_close_position(symbol=symbol)
                    ### trane 출력 ###
                    date = utils._convert_to_datetime(end_timestamp)
                    utils._std_print(
                        f"{date}    {self.trade_analysis_ins.number_of_stocks}         {self.trade_analysis_ins.trade_count:,.0f}          {self.trade_analysis_ins.profit_loss_ratio*100:,.2f} %         {self.trade_analysis_ins.profit_loss:,.2f}"
                    )

                ### 포지션 보유시 연산 pass ###
                if self.trade_analysis_ins.validate_open_position(symbol):
                    continue

                ### interval data를 데이터셋으로 구성 ###
                self.interval_dataset.set_data(
                    data_name=f"interval_{interval}", data=data
                )

            ### 분석 진행을 위해 데이터셋을 Analysis로 이동###
            self.analysis_ins.set_dataset(container_data=self.interval_dataset)

            if self.trade_analysis_ins.validate_open_position(symbol):
                continue

            ### 진입 검토 ###
            # scenario_2 = self.analysis_ins.scenario_2()
            # scenario_3 = self.analysis_ins.scenario_3()

            # 사용 후 초기화

            current_timestamp = min(timestamp_min)

            # if scenario_2[0]:
            #     await self.active_open_position(
            #         symbol=symbol,
            #         price=price,
            #         position=scenario_2[1],
            #         leverage=scenario_2[2],
            #         start_timestamp=current_timestamp,
            #         scenario_type=scenario_2[3],
            #     )

            # if scenario_3[0]:
            #     await self.active_open_position(
            #         symbol=symbol,
            #         price=price,
            #         position=scenario_3[1],
            #         leverage=scenario_3[2],
            #         start_timestamp=current_timestamp,
            #         scenario_type=scenario_3[3],
            #     )

        print("\n\nEND")


if __name__ == "__main__":
    symbols = [
        "btcusdt",
        "xrpusdt",
        "adausdt",
        "linkusdt",
        "sandusdt",
        "bnbusdt",
        "dogeusdt",
        "solusdt",
    ]  # 확인하고자 하는 심볼 정보

    ### interval값은 앞으로 analysis class에 전담하는걸로.
    ### interval class에서 역으로 데이터헨들로쪽으로 정보 공유.
    intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)

    start_date = "2024-11-01 00:00:00"  # 시작 시간
    end_date = "2024-12-24 23:59:59"  # 종료 시간
    safety_balance_ratio = 0.02  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.05  # 스톱 로스 비율
    is_download = False  # 기존 데이터로 할경우 False, 신규 다운로드 True
    adj_timer = True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    adj_rate = 0.0007
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 350
    max_trade_number = 3
    start_step = 5_000
    leverage = 10
    init_stop_rate = 0.015
    adj_interval = "3m"
    is_order_break = True
    loss_chance = 2
    step_interval = "2h"

    ### Ticker Setting Option ###
    comparison = "above"  # above : 이상, below : 이하
    absolute = True  # True : 비율 절대값, False : 비율 실제값
    value = 350_000_000  # 거래대금 : 단위 USD
    target_percent = 0.03  # 변동 비율폭 : 음수 가능
    quote_type = "usdt"  # 쌍거래 거래화폐

    backtest_ins = BackTester(
        symbols=symbols,
        intervals=intervals,
        start_date=start_date,
        end_date=end_date,
        safety_balance_ratio=safety_balance_ratio,
        stop_loss_rate=stop_loss_rate,
        is_download=is_download,
        adj_timer=adj_timer,
        adj_rate=adj_rate,
        is_use_scale_stop=use_scale_stop,
        seed_money=seed_money,
        max_trade_number=max_trade_number,
        start_step=start_step,
        leverage=leverage,
        init_stop_rate=init_stop_rate,
        adj_interval=adj_interval,
        is_order_break=is_order_break,
        loss_chance=loss_chance,
        step_interval=step_interval,
        comparison=comparison,
        absolute=True,
        value=value,
        percent=target_percent,
        quote_type=quote_type,
    )

    asyncio.run(backtest_ins.run())
    analyze_statistics = DataProcess.ResultEvaluator(backtest_ins.trade_analysis_ins)
    analyze_statistics.run_analysis()

"""
최대한 백테스트에서 구현한 후 해당 내용을 본 트레이딩에 적용한다.
백테스트와 실제 트레이딩간의 설정값을 지정방법에 차이점을 두지 않는다.

다만 실시간 티켓정보 업데이트가 필요한데, 데이터의 양과 메모리의 한계 때문에 
백테스트의 경우 티커 초기값을 지정한다.



단계별 또는 total_balance기준 일정 비율 적용여부를 검토한다.

단계별시 특정 스탭별로 정해진 금액으로만 포지션 진행하고
total_balance기준 일정 비율 적용은 간단하게 total_balance X Rate를 반영한다.

DataProcess.OrderConstraint에 해당 내용을 반영한다.

calc_fund의 기능을 분리한다.


특정 금액 초과시 이체기능 추가.
익절 금액 보존 위함.

포지션 유지 수량도 재검토 한다.




# 실제 트레이딩 메모
    >> kline_data를 지정된 interval값에 맞게 수신하고, websocket 데이터를 실시간으로 수신받되
        data container 또는 Dict자료형을 활용하여 가장 마지막값만 저장한다.(마지막값 계속 업데이트)
        연산이 필요할때만 kline_data마지막 index값에 마지막값을 대입하며, 두 데이터간 start_timestamp / end_timestamp가 동일할경우에만
        업데이트하고 동일하지 않으면서 start_timeatamp가 마지막값의 start_timestamp 보다 클 경우에는 마지막값에 "추가" 한다.
        
        추가된 데이터를 interval별로 묶어서 numpy처리 후 data container에 저장한다.
            주의사항 : websocket데이터의 수신값중 거래내역이 없을경우 수신데이터가 없으며, 해당값을 반영하여 np.array처리시 길이 문제 때문에 오류가 발생한다.
                    패딩 / 슬라이스 둘중 더 효과적인 방법을 사용하여 데이터를 만든다.
        
        데이터 분석을 마친 후 data container를 초기화 시킨다.
        
        현재 검토중인 time step은 20초이다. 초단위를 낮출경우 캔들의 길이 검토에 오해석이 있을 수 있으므로 낮은값이 무조건 좋은것은 아니다.
        
        다중 scenario에서 첫번째 중복되는 조건이 발생할 수 있으므로 이를 주의깊게 검토하고, 공통된 조건이 발생할 경우 대표 데이터를 속성값에 등록하여
        반복 연산을 피할 수 있도록 한다.
        
        scenario의 반환값은 (상태, 포지션, 레버리지, 수량)을 기초로 하고 있으나, (상태, 포지션)만 반환하는건 어떤지 검토가 필요하다.
        
        각 함수별로 단일 기능을 수행하고 각 단일기능을 묶을 매니저급 함수를 생성하는것을 검토해야한다.

"""
