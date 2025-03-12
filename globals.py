def set_clean_sell_signal(value: bool, symbol: str):
    global clean_sell_signal
    clean_sell_signal = value, symbol

def set_clean_buy_signal(value: bool, symbol: str):
    global clean_buy_signal
    clean_buy_signal = value, symbol
