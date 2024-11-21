import os
import asyncio
import datetime
import utils
import pickle
import json
from TradingDataManager import FuturesDataControl, SpotDataControl

PARENT_DIR = "/Users/cjupit/Desktop"

MAIN_FOLDER_NAME = "DataStore"
NESTED_FOLDER_NAME = "KlineData"  # 오타 수정

folder_path = os.path.join(PARENT_DIR, MAIN_FOLDER_NAME, NESTED_FOLDER_NAME)


def create_folder(path: str):  # 함수명 오타 수정
    if not os.path.isdir(path):
        os.makedirs(path)
    else:
        return


def pickle_dump(file_name: str, data: dict):
    create_folder(folder_path)
    path_full = os.path.join(folder_path, file_name)
    with open(path_full, "wb") as file:
        pickle.dump(data, file)
    return


def json_dump(file_name: str, data: dict):
    create_folder(folder_path)
    print(type(data))
    path_full = os.path.join(folder_path, file_name)
    with open(path_full, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)  # JSON 파일로 저장
    return


if __name__ == "__main__":
    obj = FuturesDataControl()
    intervals = [interval for interval in obj.KLINE_INTERVALS[:10]]
    print(intervals)
    tickers = ["btcusdt", "xrpusdt", "ethusdt", "dogeusdt", "solusdt", "neirousdt", "trxusdt"]

    end_date = utils._convert_to_datetime("2024-11-20 21:20:00")
    start_date = utils._convert_to_datetime("2024-9-1 00:00:00")

    for ticker in tickers:
        data = {}  # 각 티커마다 초기화
        for interval in intervals:
            data[interval] = asyncio.run(
                obj.fetch_historical_kline_hour_min(
                    symbol=ticker,
                    interval=interval,
                    start_date=start_date,
                    end_date=end_date,
                )
            )
        print(f"{ticker} 수신 완료")
        json_dump(file_name=f"{ticker.upper()}.json", data=data)
    print("END")
