#v0.5 Fibonacci and MACD Strategy 

import ta # type: ignore
from src.indicators import no_crossing_last_10, last500_macd_check, last500_histogram_check, last500_fibo_check, signal_cleaner


# Alış koşulları
def check_buy_conditions(df, symbol, logger):
    try:
        
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        signal_cleaner(macd_line, "buy", symbol, logger)
        from globals import clean_buy_signal

        buyCondA = hist_line.iloc[-1] > 0
        buyCondB = last500_fibo_check(df['close'], "buy", logger)
        buyCondC = clean_buy_signal[0]


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
        from globals import clean_sell_signal

        sellCondA = hist_line.iloc[-1] < 0
        sellCondB = last500_fibo_check(df['close'], "sell", logger)
        sellCondC = clean_sell_signal[0]


        return sellCondA and sellCondB and sellCondC
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
