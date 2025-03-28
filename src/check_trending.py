from utils.fetch_data import binance_fetch_data
from utils.globals import set_trend_signal
import asyncio
import pandas as pd
import numpy as np

def calculate_adx(high, low, close, period=14):
    """
    Calculate ADX manually using pandas and numpy.
    
    Args:
        high: Series of high prices
        low: Series of low prices
        close: Series of close prices
        period: Lookback period for ADX (default 14)
    
    Returns:
        Series of ADX values
    """
    # Calculate True Range (TR)
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    # Calculate Directional Movement (DM)
    up_move = high - high.shift(1)
    down_move = low.shift(1) - low
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
    
    # Smooth the TR and DM with Wilder's method
    tr_smooth = tr.rolling(window=period, min_periods=1).mean()
    plus_dm_smooth = pd.Series(plus_dm).rolling(window=period, min_periods=1).mean()
    minus_dm_smooth = pd.Series(minus_dm).rolling(window=period, min_periods=1).mean()
    
    # Calculate Directional Indicators (DI)
    plus_di = 100 * (plus_dm_smooth / tr_smooth)
    minus_di = 100 * (minus_dm_smooth / tr_smooth)
    
    # Calculate DX and ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period, min_periods=1).mean()
    
    return adx

# Alış koşulları
async def trend_checker(symbol, client, logger, slope_periods=5):
    try:
        df, close_price = await binance_fetch_data(100, symbol, client, "15m")
        adx = calculate_adx(df['high'].astype(float), df['low'].astype(float), df['close'].astype(float))
        latest_adx = adx.iloc[-1]

        if latest_adx >= 22 and latest_adx < 25:
            adx_slope = (adx.iloc[-1] - adx.iloc[-slope_periods]) / slope_periods
            if adx_slope > 0:
                set_trend_signal(True, symbol)
            else:
                set_trend_signal(False, symbol)
        elif latest_adx >= 25:
            set_trend_signal(True, symbol)
        else:
            set_trend_signal(False, symbol)

    except Exception as e:
        logger.error(f"Check Trend Error: {e}")
        

# Main async function
async def check_trend(symbols, logger, client):
    while True:
        try:
            # Create a list of tasks for each symbol
            tasks = [
                trend_checker(
                    symbol, client, logger
                )
                for symbol in symbols
            ]

            # Run all tasks concurrently
            await asyncio.gather(*tasks)
            await asyncio.sleep(300)

        except Exception as e:
            logger.error(f"Ana döngüde hata: {e}")
            await asyncio.sleep(2)