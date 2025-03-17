#v0.5 Fibonacci and MACD Strategy Implementation
import ta # type: ignore
from src.indicators import last500_histogram_check, last500_fibo_check, signal_cleaner
from utils.globals import get_clean_buy_signal, get_clean_sell_signal, set_buyconda, set_buycondb, set_buycondc, set_sellconda, set_sellcondb, set_sellcondc

# Alış koşulları
def check_buy_conditions(df, symbol, logger):
    try:
        
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        signal_cleaner(macd_line, "buy", symbol, logger)


        buyCondA = last500_histogram_check(hist_line, "buy", logger)
        buyCondB = last500_fibo_check(df['close'], "buy", logger)
        buyCondC = get_clean_buy_signal(symbol)

        set_buyconda(buyCondA, symbol)
        set_buycondb(buyCondB, symbol)
        set_buycondc(buyCondC, symbol)

        return buyCondA and buyCondB and buyCondC
    except Exception as e:
        logger.error(f"check_buy_conditions hatası: {e}")
        return False

# Satış koşulları
def check_sell_conditions(df, symbol, logger):
    try:
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        signal_cleaner(macd_line, "sell", symbol, logger)

        sellCondA = last500_histogram_check(hist_line, "sell", logger)
        sellCondB = last500_fibo_check(df['close'], "sell", logger)
        sellCondC = get_clean_sell_signal(symbol)

        set_sellconda(sellCondA, symbol)
        set_sellcondb(sellCondB, symbol)
        set_sellcondc(sellCondC, symbol)

        return sellCondA and sellCondB and sellCondC
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
