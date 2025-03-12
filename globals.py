clean_sell_signal = {}
clean_buy_signal = {}

def set_clean_sell_signal(value: bool, symbol: str):
    global clean_sell_signal
    clean_sell_signal[symbol] = value

def set_clean_buy_signal(value: bool, symbol: str):
    global clean_buy_signal
    clean_buy_signal[symbol] = value