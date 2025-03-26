#v0.5 Fibonacci and MACD Strategy Implementation
import ta # type: ignore
from src.indicators import last500_histogram_check, last500_fibo_check, signal_cleaner
from utils.globals import get_clean_buy_signal, get_clean_sell_signal, set_buyconda, set_buycondb, set_buycondc, set_sellconda, set_sellcondb, set_sellcondc
from utils.fetch_data import binance_fetch_data


# Alış koşulları
async def check_buy_conditions(lookback_period, symbol, client, logger):
    try:
        df, close_price = await binance_fetch_data(lookback_period, symbol, client)
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        signal_cleaner(macd_line, "buy", symbol, logger)

        buyCondA = last500_histogram_check(hist_line, "buy", logger)
        buyCondB = last500_fibo_check(df['close'], df['high'], df['low'], "buy", logger)
        buyCondC = get_clean_buy_signal(symbol)

        set_buyconda(buyCondA, symbol)
        set_buycondb(buyCondB, symbol)
        set_buycondc(buyCondC, symbol)

        buyAll = buyCondA and buyCondB and buyCondC
        return buyAll
    
    except Exception as e:
        logger.error(f"check_buy_conditions hatası: {e}")
        return False

# Satış koşulları
async def check_sell_conditions(lookback_period, symbol, client, logger):
    try:
        df, close_price = await binance_fetch_data(lookback_period, symbol, client)
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        signal_cleaner(macd_line, "sell", symbol, logger)

        sellCondA = last500_histogram_check(hist_line, "sell", logger)
        sellCondB = last500_fibo_check(df['close'], df['high'], df['low'], "sell", logger)
        sellCondC = get_clean_sell_signal(symbol)

        set_sellconda(sellCondA, symbol)
        set_sellcondb(sellCondB, symbol)
        set_sellcondc(sellCondC, symbol)

        sellAll = sellCondA and sellCondB and sellCondC
        return sellAll 
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
