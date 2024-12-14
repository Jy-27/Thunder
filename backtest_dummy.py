import json
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import style, ticker


class TradeAnalysis:
    def __init__(self, file_path):
        with open(file_path, "r") as file:
            data = json.load(file)

        self.closed_positions = data[0]["closed_positions"]
        self.initial_balance = data[0]["initial_balance"]
        self.total_balance = data[0]["total_balance"]
        self.profit_loss = data[0]["profit_loss"]
        self.data = data
        self.df = self.create_dataframe()
        self.summary = None

    def create_dataframe(self):
        records = []
        for symbol, trades in self.closed_positions.items():
            for trade in trades:
                records.append(
                    {
                        "Symbol": symbol,
                        "Close Time": trade[6],
                        "Profit/Loss": trade[9],
                        "Entry Price": trade[1],
                        "Exit Price": trade[10],
                        "Volume": trade[2],
                        "Entry Fee": trade[-2],
                        "Exit Fee": trade[-1],
                        "Total Fee": trade[-2] + trade[-1],
                    }
                )
        return pd.DataFrame(records)

    def analyze_profit_loss(self):
        summary = self.df.groupby("Symbol").agg(
            Total_Profits=("Profit/Loss", lambda x: x[x > 0].sum()),
            Total_Losses=("Profit/Loss", lambda x: abs(x[x < 0].sum())),
            Max_Profit=(
                "Profit/Loss",
                lambda x: x[x > 0].max() if not x[x > 0].empty else 0,
            ),
            Min_Profit=(
                "Profit/Loss",
                lambda x: x[x > 0].min() if not x[x > 0].empty else 0,
            ),
            Max_Loss=(
                "Profit/Loss",
                lambda x: x[x < 0].min() if not x[x < 0].empty else 0,
            ),
            Min_Loss=(
                "Profit/Loss",
                lambda x: x[x < 0].max() if not x[x < 0].empty else 0,
            ),
            Net_PnL=("Profit/Loss", "sum"),
            Avg_PnL=("Profit/Loss", "mean"),
            Trades=("Profit/Loss", "count"),
            Total_Entry_Fees=("Entry Fee", "sum"),
            Total_Exit_Fees=("Exit Fee", "sum"),
            Total_Fees=("Total Fee", "sum"),
        )
        summary.loc["Total"] = summary.sum(numeric_only=True)
        summary.loc["Total", "Trades"] = self.df[
            "Symbol"
        ].count()  # 합계 행의 거래 횟수 수동 조정
        # 컬럼 순서 조정: Total_Fees를 가장 마지막으로 이동
        column_order = [
            "Total_Profits",
            "Total_Losses",
            "Max_Profit",
            "Min_Profit",
            "Max_Loss",
            "Min_Loss",
            "Net_PnL",
            "Avg_PnL",
            "Trades",
            "Total_Entry_Fees",
            "Total_Exit_Fees",
            "Total_Fees",
        ]
        self.summary = summary[column_order].fillna(0)

    def plot_profit_loss(self):
        if self.summary is None:
            raise ValueError(
                "Summary has not been calculated. Run analyze_profit_loss first."
            )

        style.use("ggplot")  # 세련된 스타일 적용
        plt.figure(figsize=(12, 6), facecolor="white")  # 배경 흰색
        sorted_summary = self.summary.drop("Total", errors="ignore").sort_values(
            "Net_PnL"
        )
        bar_width = 0.6  # 스틱 두께 조정

        # 순손익 바
        plt.bar(
            sorted_summary.index,
            sorted_summary["Net_PnL"],
            color="#1f77b4",
            edgecolor="black",
            linewidth=1.5,
            label="Net PnL",
            width=bar_width,
        )

        # 수익과 손실 바 겹쳐 그리기
        plt.bar(
            sorted_summary.index,
            sorted_summary["Total_Profits"],
            color="#2ca02c",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
            label="Total Profits",
            width=bar_width,
        )
        plt.bar(
            sorted_summary.index,
            -sorted_summary["Total_Losses"],
            color="#d62728",
            alpha=0.7,
            edgecolor="black",
            linewidth=1.5,
            label="Total Losses",
            width=bar_width,
        )

        # 텍스트 크기 조정
        plt.title("Profit/Loss Breakdown by Symbol", fontsize=14)
        plt.ylabel("Profit/Loss (with commas)", fontsize=12)
        plt.xlabel("Symbol", fontsize=12)
        plt.xticks(rotation=45, fontsize=10)

        # 천 단위 쉼표 추가
        ax = plt.gca()
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))

        plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.legend(fontsize=10)
        plt.tight_layout()
        plt.show()

    def print_summary(self):
        print(f"Initial Balance: {self.initial_balance:,.2f}")
        print(f"Total Balance: {self.total_balance:,.2f}")
        print(f"Net Profit/Loss: {self.profit_loss:,.2f}")
        print(f"Profit/Loss Ratio: {self.data[0]['profit_loss_ratio']:.2f}%")
        print()

    def run_analysis(self):
        self.analyze_profit_loss()
        self.print_summary()
        # 데이터프레임 전체 출력 설정
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", 1000)
        pd.set_option("display.float_format", "{:,.2f}".format)
        print(self.summary)
        self.plot_profit_loss()


# 실행
if __name__ == "__main__":
    analyzer = TradeAnalysis("trade_closed_data.json")
    analyzer.run_analysis()
