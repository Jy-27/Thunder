import os
import sys

home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Services.PrivateAPI.Trading.FuturesTradingClient import (
    FuturesTradingClient,
)
import Workspace.Utils.TradingUtils as tr_utils
import Workspace.Utils.BaseUtils as base_utils
import SystemConfig

import asyncio
from typing import Optional, List


class OrderManager:
    def __init__(self):
        self.symbol: List = SystemConfig.Streaming.symbols[0]
        # self.symbol: List = "ADAUSDT"
        self.margin_type = SystemConfig.Position.margin_type
        # self.margin_type = "ISOLATED"
        # self.leverage = SystemConfig.Position.leverage
        self.leverage = 23
        self.path_api = SystemConfig.Path.bianace
        self.api_key = base_utils.load_json(self.path_api)
        self.ins_tr_client = FuturesTradingClient(**self.api_key)

        self.current_margin: Optional[float] = None
        self.current_leverage: Optional[int] = None
        self.current_isolated: Optional[bool] = None

    async def set_leverage(self):
        """
        레버리지 값을 설정한다. 기존 보유중인 포==지션이 있는 상태에서 변경시 오류발생한다.
        """
        if self.current_margin != 0:
            return
        print(f"  🔎 레버리지 설정값 유효성 검사")
        tr_utils.Validator.args_leverage(self.leverage)
        print(f"    📨 brackets 데이터 수신 시작")
        brackets_data = await self.ins_tr_client.fetch_leverage_brackets(self.symbol)
        print(f"    📨 brackets 데이터 수신 완료")
        max_leverage = tr_utils.Extractor.max_leverage(brackets_data)
        final_leverage = min(self.leverage, max_leverage)
        print(f"    🧮 최종 레버리지값 산출 완료")
        await self.ins_tr_client.set_leverage(self.symbol, final_leverage)
        print(f"    ✅ 레버리지 설정 완료")
        print(f"   {final_leverage}")

    async def set_margin_type(self):
        """
        마진 타입을 설정한다. 기존과 같은 값을 설정시 오류가 발생한다.
        """
        tr_utils.Validator.args_margin_type(self.margin_type)
        if self.current_isolated and self.margin_type == "CROSSED":
            return await self.ins_tr_client.set_margin_type(
                self.symbol, self.margin_type
            )

        elif not self.current_isolated and self.margin_type == "ISOLATED":
            return await self.ins_tr_client.set_margin_type(
                self.symbol, self.margin_type
            )

        else:
            return

    async def position_option_update(self):
        account_balance_data = await self.ins_tr_client.fetch_account_balance()
        positions_data = account_balance_data["positions"]
        current_position = next(
            position for position in positions_data if position["symbol"] == self.symbol
        )
        self.current_leverage = int(current_position["leverage"])
        self.current_isolated = bool(current_position["isolated"])
        self.current_margin = float(current_position["initialMargin"])
        return (
            current_position,
            self.current_leverage,
            self.current_isolated,
            self.current_margin,
        )

    async def run_order_setting(self):
        await self.position_option_update()
        await self.set_leverage()
        await self.set_margin_type()


if __name__ == "__main__":
    dummy_instance = OrderManager()
    asyncio.run(dummy_instance.run_order_setting())
