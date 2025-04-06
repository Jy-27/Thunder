


# class PublicRestFetcher:
#     def __init__(self):
#         self.ticker_price = None
#         self.book_tickers = None
#         self.ticker_24hr = None
#         self.kline_limit = None #interval값 반영
#         self.order_book = None
#         self.recent_trades = None
#         self.agg_trade = None
#         self.server_time = None
#         self.ping_binance = None
#         self.exchange_info = None
#         self.mark_price = None
#         self.funding_rate = None
#         self.open_interest = None
    
# class PublicWebsocketHub:
#     def __init__(self):
#         self.route_message_ticker = None
#         self.route_message_tread = None
#         self.route_message_miniTicker = None
#         self.route_message_depth = None
#         self.route_message_aggTrade = None
#         self.route_message_kline = None #interval값 반영
        
# class PrivateRestFetch:
#     def __init__(self):
#         self.account_balance = None
#         self.order_status = None
#         self.leverage_brackets = None
#         self.order_history = None
#         self.trade_history = None
#         self.order_details = None

# """
# RDER_TRADE_UPDATE', 'T': 1743921954052, 'E': 1743921954052, 'o': {'s': 'BTCUSDT', 'c': 'electron_ryq3OOw07CAlurSaYDLK', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '88068.2', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 648154658192, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743921954052, 't': 0, 'b': '0', 'a': '169.1422', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743921955653, 'E': 1743921955653, 'o': {'s': 'BTCUSDT', 'c': 'ios_FzS3eDhS11TlfcLg3Bbm', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '84571.1', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 647776087583, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743921955653, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743921958600, 'E': 1743921958600, 'o': {'s': 'ETHUSDT', 'c': 'ios_jOtXmJYb7Tap0W79RfUo', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.075', 'p': '1875.9', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 8389765870067665061, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743921958600, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743921992568, 'E': 1743921992568, 'o': {'s': 'BTCUSDT', 'c': 'electron_C5fQ9Tdc9uKGWXiEH7Cl', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '80343.9', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 648414889152, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743921992568, 't': 0, 'b': '160.6878', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922002880, 'E': 1743922002880, 'o': {'s': 'BTCUSDT', 'c': 'electron_DiPymqbLB8b2nuYTugC9', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '90164.2', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 648415001368, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922002880, 't': 0, 'b': '160.6878', 'a': '180.3284', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922042719, 'E': 1743922042719, 'o': {'s': 'ALGOUSDT', 'c': 'electron_f8jWUFppG4KGJVzyZZ6V', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.1856', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836104273, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922042719, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922042780, 'E': 1743922042780, 'o': {'s': 'ALGOUSDT', 'c': 'electron_SIrKUcrzPu8zAD4c8v6U', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.1981', 'x': 'NEW', 'X': 'NEW', 'i': 12836229293, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922042780, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922092709, 'E': 1743922092710, 'o': {'s': 'ALGOUSDT', 'c': 'electron_SIrKUcrzPu8zAD4c8v6U', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.1981', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836229293, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922092709, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922092710, 'E': 1743922092710, 'o': {'s': 'ALGOUSDT', 'c': 'electron_uuW2Uepc9G0ryPs54knW', 'S': 'SELL', 'o': 'STOP_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.152', 'x': 'NEW', 'X': 'NEW', 'i': 12836232348, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922092710, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'STOP_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922092767, 'E': 1743922092767, 'o': {'s': 'ALGOUSDT', 'c': 'electron_VD7TqI1zv2I0pBM1kT91', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.2128', 'x': 'NEW', 'X': 'NEW', 'i': 12836232354, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922092767, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922142708, 'E': 1743922142708, 'o': {'s': 'ALGOUSDT', 'c': 'electron_9Vm610zQtWwmOZBmu8gH', 'S': 'BUY', 'o': 'STOP', 'f': 'GTC', 'q': '22.9', 'p': '0.2188', 'ap': '0', 'sp': '0.2122', 'x': 'NEW', 'X': 'NEW', 'i': 12836235228, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922142708, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'MARK_PRICE', 'ot': 'STOP', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922176599, 'E': 1743922176599, 'o': {'s': 'ALGOUSDT', 'c': 'electron_9Vm610zQtWwmOZBmu8gH', 'S': 'BUY', 'o': 'STOP', 'f': 'GTC', 'q': '22.9', 'p': '0.2188', 'ap': '0', 'sp': '0.2122', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836235228, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922176599, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'MARK_PRICE', 'ot': 'STOP', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922178972, 'E': 1743922178972, 'o': {'s': 'ALGOUSDT', 'c': 'electron_VD7TqI1zv2I0pBM1kT91', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.2128', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836232354, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922178972, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'MARK_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922187847, 'E': 1743922187847, 'o': {'s': 'BTCUSDT', 'c': 'electron_C5fQ9Tdc9uKGWXiEH7Cl', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '80343.9', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 648414889152, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922187847, 't': 0, 'b': '0', 'a': '180.3284', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922188770, 'E': 1743922188770, 'o': {'s': 'BTCUSDT', 'c': 'electron_DiPymqbLB8b2nuYTugC9', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '0.002', 'p': '90164.2', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 648415001368, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922188770, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922214152, 'E': 1743922214152, 'o': {'s': 'ALGOUSDT', 'c': 'electron_uuW2Uepc9G0ryPs54knW', 'S': 'SELL', 'o': 'STOP_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.152', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836232348, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922214152, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'STOP_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922249549, 'E': 1743922249549, 'o': {'s': 'ALGOUSDT', 'c': 'electron_QgossOsuYZR545hTl3fF', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.2', 'x': 'NEW', 'X': 'NEW', 'i': 12836240350, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922249549, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922268814, 'E': 1743922268814, 'o': {'s': 'ALGOUSDT', 'c': 'electron_QgossOsuYZR545hTl3fF', 'S': 'SELL', 'o': 'TAKE_PROFIT_MARKET', 'f': 'GTE_GTC', 'q': '0', 'p': '0', 'ap': '0', 'sp': '0.2', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836240350, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922268814, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'TAKE_PROFIT_MARKET', 'ps': 'BOTH', 'cp': True, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922287479, 'E': 1743922287480, 'o': {'s': 'ALGOUSDT', 'c': 'electron_k0zGNQxy9uXcJxxrZtmc', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '30', 'p': '0.2', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 12836243778, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922287479, 't': 0, 'b': '0', 'a': '6', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922321447, 'E': 1743922321448, 'o': {'s': 'ALGOUSDT', 'c': 'electron_k0zGNQxy9uXcJxxrZtmc', 'S': 'SELL', 'o': 'LIMIT', 'f': 'GTC', 'q': '30', 'p': '0.2', 'ap': '0', 'sp': '0', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836243778, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922321447, 't': 0, 'b': '0', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922369054, 'E': 1743922369055, 'o': {'s': 'ALGOUSDT', 'c': 'electron_m0smRPZ4kzZPHud71sOO', 'S': 'BUY', 'o': 'LIMIT', 'f': 'GTC', 'q': '30', 'p': '0.1773', 'ap': '0', 'sp': '0', 'x': 'NEW', 'X': 'NEW', 'i': 12836249401, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922369054, 't': 0, 'b': '5.319', 'a': '0', 'm': False, 'R': False, 'wt': 'CONTRACT_PRICE', 'ot': 'LIMIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': False, 'si': 0, 'ss': 0, 'V': 'EXPIRE_MAKER', 'pm': 'NONE', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922460940, 'E': 1743922460940, 'o': {'s': 'ALGOUSDT', 'c': 'electron_yk9krHA0EByuYkcPxjms', 'S': 'SELL', 'o': 'TAKE_PROFIT', 'f': 'GTE_GTC', 'q': '30', 'p': '0.1803', 'ap': '0', 'sp': '0.2006', 'x': 'NEW', 'X': 'NEW', 'i': 12836254755, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922460940, 't': 0, 'b': '5.319', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'TAKE_PROFIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'OPPONENT', 'gtd': 0}}
# {'e': 'ORDER_TRADE_UPDATE', 'T': 1743922479229, 'E': 1743922479229, 'o': {'s': 'ALGOUSDT', 'c': 'electron_yk9krHA0EByuYkcPxjms', 'S': 'SELL', 'o': 'TAKE_PROFIT', 'f': 'GTE_GTC', 'q': '30', 'p': '0.1803', 'ap': '0', 'sp': '0.2006', 'x': 'CANCELED', 'X': 'CANCELED', 'i': 12836254755, 'l': '0', 'z': '0', 'L': '0', 'n': '0', 'N': 'USDT', 'T': 1743922479229, 't': 0, 'b': '5.319', 'a': '0', 'm': False, 'R': True, 'wt': 'CONTRACT_PRICE', 'ot': 'TAKE_PROFIT', 'ps': 'BOTH', 'cp': False, 'rp': '0', 'pP': True, 'si': 0, 'ss': 0, 'V': 'NONE', 'pm': 'OPPONENT', 'gtd': 0}}
# """


# class ExecutionReceiverWebsocket:
#     def __init__(self):#o key에 조건이 붙음.
#         self.LIMIT = "지정가 주문"
#         self.TAKE_PROFIT_MARKET = "마켓가 손익 실현"
#         self.STOP = "조건부 진입"
#         self.STOP_MARKET = "스탑로스"
#         self.TAKE_PROFIT = "지정가 손익 실현"
        
import os, sys
home_path = os.path.expanduser("~")
sys.path.append(os.path.join(home_path, "github", "Thunder", "Binance"))

from Workspace.Repository.RepositoryOverwrite import RepositoryOverwrite
from Workspace.Repository.RepositoryAppend import RepositoryAppend

from SystemConfig import Streaming

symbols = Streaming.symbols
intervals = Streaming.intervals

# class PublicRestFetcher:
#     self.ticker_price = None    ##
#     self.book_tickers = None    ##
#     self.ticker_24hr = None     ##
#     self.kline_limit = None     ##interval값 반영
#     self.order_book = None      ##
#     self.recent_trades = None   ##
#     self.agg_trade = None       ##
#     self.server_time = None     ##
#     self.ping_binance = None    ##
#     self.exchange_info = None   ##
#     self.mark_price = None      ##
#     self.funding_rate = None    ##
#     self.open_interest = None   ##
    
# class PublicWebsocketHub:
#     self.route_message_ticker = None        #
#     self.route_message_tread = None         #
#     self.route_message_miniTicker = None    #
#     self.route_message_depth = None         #
#     self.route_message_aggTrade = None      #
#     self.route_message_kline = None         ## interval값 반영
        
# class PrivateRestFetch:
#     self.account_balance = None     ##
#     self.order_status = None        ##
#     self.leverage_brackets = None   ##
#     self.order_history = None       ##
#     self.trade_history = None       ##
#     self.order_details = None       ##

# class ExecutionReceiverWebsocket:
#     self.LIMIT = "지정가 주문"                  ##
#     self.TAKE_PROFIT_MARKET = "마켓가 손익 실현" ##
#     self.STOP = "조건부 진입"                   ##
#     self.STOP_MARKET = "스탑로스"               ##
#     self.TAKE_PROFIT = "지정가 손익 실현"        ##
    
overwrite_list = [
    #Public Data
    "fetch_ticker_price",
    "fetch_book_tickers",
    "fetch_ticker_24hr",
    *[f"fetch_kline_limit_{interval}" for interval in intervals],
    "fetch_order_book",
    "fetch_recent_trades",
    "fetch_agg_trade",
    "fetch_mark_price",
    "fetch_funding_rate",
    "fetch_open_interest",

    #exchange_metadata
    "fetch_ping_binance",
    "fetch_exchange_info",
    "fetch_server_time",
    
    #Public Websocket
    *[f"websocket_route_message_kline_{interval}" for interval in intervals],

    #Private Websocket
    "websocket_limit",
    "websocket_take_profit_market",
    "websocket_stop",
    "websocket_stop_market",
    "websocket_take_profit",
]

overwrite_list_ex = [
    #Private data
    "fetch_account_balance",
    "fetch_order_status",
    "fetch_leverage_brackets",
    "fetch_order_history",
    "fetch_trade_history",
    "fetch_order_details",
]

append_list = [
    #Public Websocket
    "websocket_ticker",
    "websocket_tread",
    "websocket_miniTicker",
    "websocket_depth",
    "websocket_aggTrade",
]
from pprint import pprint
pprint(overwrite_list)

class TradingOverwrite(RepositoryOverwrite):
    __slots__ = tuple(overwrite_list)
    def __init__(self, base_type):
        super().__init__(base_type=base_type)
    
class TradingAppend(RepositoryAppend):
    __slots__ = tuple(append_list)
    def __init__(self):
        super().__init__()
    
class SymolbTradingRepository:
    __slots__ = ("overwrite", "append")
    def __init__(self, base_type):
        self.overwrite = TradingOverwrite(base_type)
        self.append = TradingAppend()
        
class MargetData:
    __slots__ = tuple(symbols)
    def __init__(self, base_type):
        for attr in self.__slots__:
            setattr(self, attr, SymolbTradingRepository(base_type))
    
class ExchangeMestaOverwrite(RepositoryOverwrite):
    __slots__ = tuple(overwrite_list_ex)
    def __init__(self):
        super().__init__()
        
        
if __name__ == "__main__":
    dummy_repository = MargetData([])