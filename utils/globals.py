clean_sell_signal = {}
clean_buy_signal = {}

sl_price = {}
last_timestamp = {}

buyconda = {}
buycondb = {}
buycondc = {}

sellconda = {}
sellcondb = {}
sellcondc = {}

error_counter = 0

db_status = False

user_time_zone = "UTC"

def set_user_time_zone(value: str):
    global user_time_zone
    user_time_zone = value

def get_user_time_zone():
    global user_time_zone
    return user_time_zone

def set_clean_sell_signal(value: bool, symbol: str):
    global clean_sell_signal
    clean_sell_signal[symbol] = value

def set_clean_buy_signal(value: bool, symbol: str):
    global clean_buy_signal
    clean_buy_signal[symbol] = value

def set_buyconda(value: bool, symbol: str):
    global buyconda
    buyconda[symbol] = value

def set_buycondb(value: bool, symbol: str):
    global buycondb
    buycondb[symbol] = value

def set_buycondc(value: bool, symbol: str):
    global buycondc
    buycondc[symbol] = value

def get_buyconda(symbol: str):
    global buyconda
    return buyconda[symbol]

def get_buycondb(symbol: str):
    global buycondb
    return buycondb[symbol]

def get_buycondc(symbol: str):
    global buycondc
    return buycondc[symbol]

def set_sellconda(value: bool, symbol: str):
    global sellconda
    sellconda[symbol] = value

def set_sellcondb(value: bool, symbol: str):
    global sellcondb
    sellcondb[symbol] = value

def set_sellcondc(value: bool, symbol: str):
    global sellcondc
    sellcondc[symbol] = value

def get_sellconda(symbol: str):
    global sellconda
    return sellconda[symbol]

def get_sellcondb(symbol: str):
    global sellcondb
    return sellcondb[symbol]

def get_sellcondc(symbol: str):
    global sellcondc
    return sellcondc[symbol]

def set_capital_tbu(value: float):
    global capital_tbu
    capital_tbu = value

def get_capital_tbu():
    global capital_tbu
    return capital_tbu

def get_clean_sell_signal(symbol: str):
    global clean_sell_signal
    return clean_sell_signal[symbol]

def get_clean_buy_signal(symbol: str):
    global clean_buy_signal
    return clean_buy_signal[symbol]

def set_sl_price(value: float, symbol: str):
    global sl_price
    sl_price[symbol] = value

def get_sl_price(symbol: str):
    global sl_price
    return sl_price[symbol]

def set_last_timestamp(value: int, symbol: str):
    global last_timestamp
    last_timestamp[symbol] = value

def get_last_timestamp(symbol: str):
    global last_timestamp
    return last_timestamp[symbol]

def set_db_status(value: bool):
    global db_status
    db_status = value

def get_db_status():
    global db_status
    return db_status

def set_error_counter(value: int):
    global error_counter
    error_counter = value

def get_error_counter():
    global error_counter
    return error_counter