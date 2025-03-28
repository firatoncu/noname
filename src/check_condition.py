#v0.5 Fibonacci and MACD Strategy Implementation
import ta # type: ignore
from src.indicators import last500_histogram_check, last500_fibo_check, first_wave_signal, trending_last500_fibo_check, trending_macd_crossover_check
from utils.globals import get_clean_buy_signal, get_clean_sell_signal, set_buyconda, set_buycondb, set_buycondc, set_sellconda, set_sellcondb, set_sellcondc, get_trend_signal
from utils.fetch_data import binance_fetch_data


# Alış koşulları
async def check_buy_conditions(lookback_period, symbol, client, logger):
    try:
        df, close_price = await binance_fetch_data(lookback_period, symbol, client)
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        hist_line = macd.macd_diff()

        first_wave_signal(df['close'], df['high'], df['low'], "buy", symbol, logger)
        # Trend Signal Check
        if get_trend_signal(symbol) == False:
            buyCondA = last500_histogram_check(hist_line, "buy", logger)
            buyCondB = last500_fibo_check(df['close'], df['high'], df['low'], "buy", logger)
        else:
            buyCondA = trending_macd_crossover_check(macd_line, signal_line, "buy", logger)
            buyCondB = trending_last500_fibo_check(df['close'], df['high'], df['low'], "buy", logger)
        buyCondC = True if get_clean_buy_signal(symbol) == 2 else False

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
        signal_line = macd.macd_signal()
        hist_line = macd.macd_diff()

        first_wave_signal(df['close'], df['high'], df['low'], "sell", symbol, logger)
        # Trend Signal Check
        if get_trend_signal(symbol) == False:
            sellCondA = last500_histogram_check(hist_line, "sell", logger)
            sellCondB = last500_fibo_check(df['close'], df['high'], df['low'], "sell", logger)
        else:
            sellCondA = trending_macd_crossover_check(macd_line, signal_line, "buy", logger)
            sellCondB = trending_last500_fibo_check(df['close'], df['high'], df['low'], "sell", logger)
        sellCondC = True if get_clean_sell_signal(symbol) == 2 else False

        set_sellconda(sellCondA, symbol)
        set_sellcondb(sellCondB, symbol)
        set_sellcondc(sellCondC, symbol)

        sellAll = sellCondA and sellCondB and sellCondC
        return sellAll 
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
