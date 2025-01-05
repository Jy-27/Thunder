from setuptools import setup, Extension
from Cython.Build import cythonize
import os

# Cython으로 컴파일할 파일 목록
extensions = [
    Extension("main", ["run_trading.py"]),
    Extension("SimulateTrading", ["SimulateTrading.py"]),
    Extension("TradeComputation", ["TradeComputation.py"]),
]

# 컴파일 설정
setup(
    name="TradingBacktest",
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",  # Python 3 코드 호환
            "boundscheck": False,   # 경계 검사 비활성화
            "wraparound": False,    # 배열 인덱싱 최적화
        },
    ),
    zip_safe=False,
)