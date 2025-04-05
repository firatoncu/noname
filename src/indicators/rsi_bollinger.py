import pandas as pd
import numpy as np
import pandas_ta as ta
from utils.globals import set_clean_buy_signal, set_clean_sell_signal, get_clean_buy_signal, get_clean_sell_signal, set_buycondc, set_sellcondc, set_strategy_name

# 1. Bollinger Band Squeeze Check
def bollinger_squeeze_check(close_prices_str, logger):
    """
    Checks if the previous bar indicates a Bollinger Band squeeze (low volatility).
    A squeeze is detected when the band width is below the 20th percentile of the last 100 periods.
    """
    try:
        set_strategy_name("Bollinger Bands & RSI")
        close_prices = close_prices_str.astype(float)
        # Calculate Bollinger Bands
        sma = ta.sma(close_prices, length=20)
        std = ta.stdev(close_prices, length=20)
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std
        band_width = upper_band - lower_band

        # Calculate threshold (20th percentile of last 100 band widths)
        N = 100
        if len(band_width) >= N:
            threshold = np.percentile(band_width.iloc[-N:], 20)
        else:
            threshold = np.percentile(band_width, 20)

        # Check if the previous bar's band width is below the threshold
        if band_width.iloc[-2] < threshold:
            return True
        return False

    except Exception as e:
        logger.error(f"Bollinger Squeeze Check Error: {e}")
        return False

# 2. Price Breakout Check
def price_breakout_check(close_prices_str, side, logger):
    """
    Confirms a breakout by checking if the current price crosses the upper (buy)
    or lower (sell) Bollinger Band.
    """
    try:
        close_prices = close_prices_str.astype(float)
        # Calculate Bollinger Bands
        sma = ta.sma(close_prices, length=20)
        std = ta.stdev(close_prices, length=20)
        upper_band = sma + 2 * std
        lower_band = sma - 2 * std

        if side == "buy" and close_prices.iloc[-1] > upper_band.iloc[-1]:
            return True
        elif side == "sell" and close_prices.iloc[-1] < lower_band.iloc[-1]:
            return True
        return False

    except Exception as e:
        logger.error(f"Price Breakout Check Error: {e}")
        return False

# 3. RSI Momentum Check with Wave State
def rsi_momentum_check(close_prices_str, side, symbol, logger):
    """
    Checks RSI for momentum confirmation and tracks a simple wave-like state.
    RSI > 50 for buy, RSI < 50 for sell, with a state transition similar to first_wave_signal.
    """
    try:
        close_prices = close_prices_str.astype(float)
        # Calculate RSI (14-period, common default)
        rsi = ta.rsi(close_prices, length=14)

        # Simple state tracking (mimicking first_wave_signal)
        # State 0: No wave, State 1: Wave started, State 2: Wave confirmed
        # These functions (get_clean_buy_signal, set_clean_buy_signal, etc.) are assumed to exist
        sma = ta.sma(close_prices, length=20)  # Middle band for trend context

        if side == "buy":
            # Wave start: Price crosses above SMA and RSI > 50
            if (close_prices.iloc[-1] > sma.iloc[-1] and 
                close_prices.iloc[-2] <= sma.iloc[-2] and 
                rsi.iloc[-1] > 50):
                set_clean_buy_signal(1, symbol)
                set_buycondc(False, symbol)
                return False

            # Wave confirmation: RSI remains above 50
            if rsi.iloc[-1] > 50 and get_clean_buy_signal(symbol) == 1:
                set_clean_buy_signal(2, symbol)
                set_buycondc(True, symbol)
                return True

            # Reset state if price falls below SMA
            if (close_prices.iloc[-1] < sma.iloc[-1] and 
                get_clean_buy_signal(symbol) == 2):
                set_clean_buy_signal(0, symbol)
                set_buycondc(False, symbol)
                return False

            # Return True only if wave is confirmed
            if get_clean_buy_signal(symbol) == 2 and rsi.iloc[-1] > 50:
                return True
            return False

        elif side == "sell":
            # Wave start: Price crosses below SMA and RSI < 50
            if (close_prices.iloc[-1] < sma.iloc[-1] and 
                close_prices.iloc[-2] >= sma.iloc[-2] and 
                rsi.iloc[-1] < 50):
                set_clean_sell_signal(1, symbol)
                set_sellcondc(False, symbol)
                return False

            # Wave confirmation: RSI remains below 50
            if rsi.iloc[-1] < 50 and get_clean_sell_signal(symbol) == 1:
                set_clean_sell_signal(2, symbol)
                set_sellcondc(True, symbol)
                return True

            # Reset state if price rises above SMA
            if (close_prices.iloc[-1] > sma.iloc[-1] and 
                get_clean_sell_signal(symbol) == 2):
                set_clean_sell_signal(0, symbol)
                set_sellcondc(False, symbol)
                return False

            # Return True only if wave is confirmed
            if get_clean_sell_signal(symbol) == 2 and rsi.iloc[-1] < 50:
                return True
            return False

        return False

    except Exception as e:
        logger.error(f"RSI Momentum Check Error: {e}")
        return False
