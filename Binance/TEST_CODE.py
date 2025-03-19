import asyncio
import nest_asyncio
import pickle
from typing import Dict


import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

nest_asyncio.apply()

import Workspace.Utils.TradingUtils as tr_utils
import Workspace.Utils.BaseUtils as base_utils

path_closing = "/Users/hhh/github/testdata/closing.pkl"
path_indices = "/Users/hhh/github/testdata/indices.pkl"

with open(path_closing, "rb")as file:
    closing_data = pickle.load(file)
with open(path_indices, "rb")as file:
    indices_data = pickle.load(file)