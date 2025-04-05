#v0.5 Fibonacci and MACD Strategy Implementation
import ta # type: ignore
from src.indicators.macd_fibonacci import last500_histogram_check, last500_fibo_check, first_wave_signal, last500_fibo_check, macd_crossover_check
from src.indicators.rsi_bollinger import rsi_momentum_check, bollinger_squeeze_check, price_breakout_check
from utils.globals import get_clean_buy_signal, get_clean_sell_signal, set_buyconda, set_buycondb, set_buycondc, set_sellconda, set_sellcondb, set_sellcondc, get_trend_signal, get_strategy_name
from utils.fetch_data import binance_fetch_data


# Alış koşulları
async def check_buy_conditions(lookback_period, symbol, client, logger):
    try:
        df, close_price = await binance_fetch_data(lookback_period, symbol, client)


        if get_strategy_name() == "Bollinger Bands & RSI":
        # RSI ve Bollinger Bands Check
            buyCondA = rsi_momentum_check(df['close'], "buy", symbol, logger)
            buyCondB = bollinger_squeeze_check(df['close'], logger)
            buyCondC = price_breakout_check(df['close'], "buy", logger)

        else:

            #MACD Crossover & Fibonacci Check

            macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            hist_line = macd.macd_diff()
            first_wave_signal(df['close'], df['high'], df['low'], "buy", symbol, logger)
            buyCondA = macd_crossover_check(macd_line, signal_line, "buy", logger)
            buyCondB = last500_fibo_check(df['close'], df['high'], df['low'], "buy", logger)
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



        if get_strategy_name() == "Bollinger Bands & RSI":
        # RSI ve Bollinger Bands Check
            sellCondA = rsi_momentum_check(df['close'], "sell", symbol, logger)
            sellCondB = bollinger_squeeze_check(df['close'], logger)
            sellCondC = price_breakout_check(df['close'], "sell", logger)
            
        else:
            macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            hist_line = macd.macd_diff()
            #MACD Crossover & Fibonacci Check

            first_wave_signal(df['close'], df['high'], df['low'], "sell", symbol, logger)
            sellCondA = macd_crossover_check(macd_line, signal_line, "sell", logger)
            sellCondB = last500_fibo_check(df['close'], df['high'], df['low'], "sell", logger)
            sellCondC = True if get_clean_sell_signal(symbol) == 2 else False

        set_sellconda(sellCondA, symbol)
        set_sellcondb(sellCondB, symbol)
        set_sellcondc(sellCondC, symbol)

        sellAll = sellCondA and sellCondB and sellCondC
        return sellAll 
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
