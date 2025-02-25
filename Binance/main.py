import Workspace.Services.PrivateAPI.Trading.FuturesTradingClient as futures_tr_client
import SystemConfig
import Workspace.Utils.BaseUtils as base_utils
import Workspace.Utils.TradingUtils as tr_utils
from Workspace.Processor.Order.PendingOrder import PedingOrder


binance_path = SystemConfig.Path.bianace
binance_api = base_utils.load_json(binance_path)

private_api = futures_tr_client.FuturesTradingClient(**binance_api)

if __name__ == "__main__":
    symbol = 'ADAUSDT'
    
    data = private_api.fetch_order_status(symbol)
    
    account = private_api.fetch_account_balance()
    
    
    for i in data:
        print(i["type"])
    
    
    # account_data = private_api.fetch_account_balance()
    
    # validate_data = tr_utils.Extractor.current_positions(account_data)
    # print(validate_data)