clean_sell_signal = {}
clean_buy_signal = {}
last_position_qty = {}
tp_price = {}
sl_price = {}
side_info = {}

def set_clean_sell_signal(value: bool, symbol: str):
    global clean_sell_signal
    clean_sell_signal[symbol] = value

def set_clean_buy_signal(value: bool, symbol: str):
    global clean_buy_signal
    clean_buy_signal[symbol] = value

def set_last_position_qty(value: float, symbol: str):
    global last_position_qty
    last_position_qty[symbol] = value

def set_tp_price(value: float, symbol: str):
    global tp_price
    tp_price[symbol] = value

def set_sl_price(value: float, symbol: str):
    global sl_price
    sl_price[symbol] = value

def set_side_info(value: str, symbol: str):
    global side_info
    side_info[symbol] = value

def get_clean_sell_signal(symbol: str):
    global clean_sell_signal
    return clean_sell_signal[symbol]

def get_clean_buy_signal(symbol: str):
    global clean_buy_signal
    return clean_buy_signal[symbol]

def get_last_position_qty(symbol: str):
    global last_position_qty
    return last_position_qty[symbol]

def get_tp_price(symbol: str):
    global tp_price
    return tp_price[symbol]

def get_sl_price(symbol: str):
    global sl_price
    return sl_price[symbol]

def get_side_info(symbol: str):
    global side_info
    return side_info[symbol]