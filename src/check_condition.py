#v0.5 Fibonacci and MACD Strategy 

import ta # type: ignore
from src.indicators import no_crossing_last_10, last500_macd_check, last500_histogram_check, last500_fibo_check


# Alış koşulları
def check_buy_conditions(df, logger):
    try:
        
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        hist_line = macd.macd_diff()
        
        buyCondA = hist_line.iloc[-1] > 0
        buyCondB = last500_fibo_check(df['close'], "buy", logger)


        return buyCondA and buyCondB
    except Exception as e:
        logger.error(f"check_buy_conditions hatası: {e}")
        return False

# Satış koşulları
def check_sell_conditions(df, logger):
    try:
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        hist_line = macd.macd_diff()

        sellCondA = hist_line.iloc[-1] > 0
        sellCondB = last500_fibo_check(df['close'], "sell", logger)


        return sellCondA and sellCondB
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
