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

class BackTester:
    def __init__(
        self,
        symbols,
        intervals,
        start_date,
        end_date,
        safety_balance_ratio,
        stop_loss_rate,
        is_download,
        adj_timer,
        adj_rate,
        use_scale_stop,
        leverage,
        seed_money,
        max_trade_number,
        start_step,
        init_stop_rate,
        adj_interval,
    ):
        self.symbols = [symbol.upper() for symbol in symbols]
        self.intervals = intervals
        self.start_date = start_date
        self.end_date = end_date
        self.safety_balance_ratio = safety_balance_ratio
        self.stop_loss_rate = stop_loss_rate
        self.is_download = is_download
        self.adj_timer = adj_timer
        self.adj_rate = adj_rate
        self.adj_interval = adj_interval
        self.use_scale_stop = use_scale_stop
        self.leverage = None
        self.test_mode = True
        self.closing_sync_data = None
        self.test_manager_ins = DataProcess.TestDataManager(
            symbols=self.symbols,
            intervals=self.intervals,
            start_date=self.start_date,
            end_date=self.end_date,
        )
        self.test_data_manager_ins = DataProcess.TestProcessManager()
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

    def __get_data_path(self):
        file_name = self.test_manager_ins.kline_closing_sync_data
        folder_name = self.test_manager_ins.storeage
        base_directory = os.path.dirname(os.getcwd())
        path = os.path.join(base_directory, folder_name, file_name)
        return path

    def __validate_base_data(self):
        # symbol정보만 점검함. interval 정보는 확인이 가능하나 귀찮음. (np.array화 하여 [0]index timestamp를 기준으로 전체 찾고 시작과 긑의 값 차이를 비교하여 interval 밀리초를 계산)
        if not self.closing_sync_data:
            raise ValueError(f"closing_sync_data가 비어있음.")
        for symbol, _ in self.closing_sync_data.items():
            if not symbol in self.symbols:
                raise ValueError(f"closing_sync_data의 symbol정보 불일치: {symbol}")

    async def get_base_data(self):
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
            data = await self.test_manager_ins.generate_kline_interval_data(save=False)
            data_array = utils._convert_kline_data_array(data)
            self.closing_sync_data = self.test_manager_ins.generate_kline_closing_sync(
                kline_data=data_array, save=True
            )

    async def get_indices_data(self):
        self.symbol_map, self.interval_map, self.closing_indices_data = (
            utils._convert_to_container(self.closing_sync_data)
        )
        self.test_manager_ins.get_indices_data(
            data_container=self.closing_indices_data, lookback_days=1
        )

    def update_trade_info(self, symbol: str, data):
        price = data[-1][4]
        close_timestamp = data[-1][6]
        if symbol in self.trade_analysis_ins.open_positions:
            return self.trade_analysis_ins.update_log_data(
                symbol=symbol, price=price, timestamp=close_timestamp
            )
        else:
            return False

    def analyze_data(self, data):
        self.analysis_ins.case_1_data_length(data)
        self.analysis_ins.case_2_candle_length(data)
        self.analysis_ins.case_3_continuous_trend_position(data)
        self.analysis_ins.case_7_ocillator_value(data)
        self.analysis_ins.case_8_sorted_indices(data, 2, 3)

    async def __validate_open_position(self, symbol: str, price: float, leverage: int):
        if symbol in self.trade_analysis_ins.open_positions:
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

            if self.leverage is None:
                leverage = leverage
            else:
                leverage = self.leverage

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

    def __validate_cloes_position(self, symbol: str):
        if symbol in self.trade_analysis_ins.open_positions:
            return True
        else:
            return False

    async def active_open_position(
        self,
        symbol: str,
        price: float,
        position: int,
        leverage: int,
        start_timestamp: int,
        scenario_type: int,
    ):
        is_open_signal, quantity, leverage= await self.__validate_open_position(
            symbol=symbol, price=price, leverage=leverage
        )
               
        if not is_open_signal:
            return
        else:
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
                use_scale_stop=self.use_scale_stop,
            )
            self.trade_analysis_ins.add_log_data(log_data=log_data)

    def active_close_position(self, symbol: str):
        if self.__validate_cloes_position(symbol=symbol):
            self.trade_analysis_ins.remove_order_data(symbol=symbol)


    async def run(self):
        await self.get_base_data()
        self.__validate_base_data()
        await self.get_indices_data()

        header = "=" * 70
        print(f"\n {header}\n")
        print(f"    *****=-_( BACK TESTING )_-=*****\n")
        print(f"    1. start     : {self.start_date}")
        print(f"    2. end       : {self.end_date}")
        print(f"    3. symbols   : {self.symbols}")
        print(f"    4. intervals : {self.intervals}")
        print(f"\n {header}\n")
        print('     DateTime             Number     PnL_Ratio        Gross_PnL')

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
            for interval in self.intervals:
                
                
                maps_ = self.closing_indices_data.get_data(f"map_{interval}")[idx]
                data = self.closing_indices_data.get_data(f"interval_{interval}")[maps_]
                
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
                    utils._std_print(f"{date}         {self.trade_analysis_ins.number_of_stocks}          {self.trade_analysis_ins.profit_loss_ratio:,.2f}            {self.trade_analysis_ins.profit_loss:,.2f}")
                    # await asyncio.sleep(0.1)
                
                ### 분석 진행 ###
                self.analyze_data(data)
            # asyncio.sleep(0.05)
            ### 진입 검토 ###
            scenario_2 = self.analysis_ins.scenario_2()

            # 사용 후 초기화
            self.analysis_ins.reset_cases()
            
            if scenario_2[0]:
                await self.active_open_position(
                    symbol=symbol,
                    price=price,
                    position=scenario_2[1],
                    leverage=scenario_2[2],
                    start_timestamp=min(timestamp_min),
                    scenario_type=scenario_2[3],
                )
        print("\n\nEND")
        


if __name__ == "__main__":
    symbols = ["btcusdt", "xrpusdt", "adausdt", "linkusdt", "sandusdt", "bnbusdt", "dogeusdt", "solusdt"]  # 확인하고자 하는 심볼 정보
    intervals = ["1m", "5m", "15m"]  # 백테스트 적용 interval값(다운로드 항목)
    start_date = "2024-11-01 00:00:00"  # 시작 시간
    end_date = "2024-12-24 23:59:59"  # 종료 시간
    safety_balance_ratio = 0.02  # 잔고 안전금액 지정 비율
    stop_loss_rate = 0.025  # 스톱 로스 비율
    is_download = True  # 기존 데이터로 할경우 False, 신규 다운로드 True
    adj_timer = True  # 시간 흐름에 따른 시작가 변동률 반영(stoploss에 영향미침.)
    adj_rate = 0.0007
    use_scale_stop = True  # final손절(False), Scale손절(True)
    seed_money = 350
    max_trade_number = 3
    start_step = 5_000
    leverage = 10
    init_stop_rate = 0.015
    adj_interval = "3m"

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
        use_scale_stop=use_scale_stop,
        seed_money=seed_money,
        max_trade_number=max_trade_number,
        start_step=start_step,
        leverage=leverage,
        init_stop_rate=init_stop_rate,
        adj_interval=adj_interval,
    )
    
    asyncio.run(backtest_ins.run())
    analyze_statistics = DataProcess.ResultEvaluator(backtest_ins.trade_analysis_ins)
    analyze_statistics.run_analysis()
