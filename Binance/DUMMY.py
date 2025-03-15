import pickle
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

path_closing = os.path.join(home_path, "github", "TestData", "closing.pkl")
path_indices = os.path.join(home_path, "github", "TestData", "indices.pkl")

print(f"  🚀 storage 로딩 시작")
with open(path_closing, "rb")as file:
    storage_closing = pickle.load(file)
print(f"    📤 storage_closing 로딩완료")
with open(path_indices, "rb")as file:
    storage_indices = pickle.load(file)
print(f"    📤 storage_indices 로딩완료")
intervals = [i.split("_")[1] for i in storage_closing.__slots__]
print(f"    🔎 intervals 추출완료: {intervals}")
print(f"  ✅ 데이터 준비 완료")