
from src.indicators import last500_fibo_check, last500_histogram_check
import pandas as pd
import ta
from utils.globals import set_clean_buy_signal, set_clean_sell_signal

async def initial_data_constructor(client, symbol):
            # Get last 1000 candles
        klines = await client.futures_klines(symbol=symbol, interval='1m', limit=500)
        df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
        df['close'] = pd.to_numeric(df['close'])
        
        close_prices_str = df['close']
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        hist_line = macd.macd_diff()

        return close_prices_str, hist_line, macd_line

async def signal_initializer(client, symbol, logger):
    try:
        # Verileri al (kapanış fiyatları, histogram ve MACD çizgisi)
        close_prices_str, hist_line, macd_line = await initial_data_constructor(client, symbol)

        # MACD'nin mevcut durumunu kontrol et
        close_prices = close_prices_str.astype(float)
        min_index = close_prices.index(min(close_prices))
        max_index = close_prices.index(max(close_prices))


        fibo_values = {}
        fibo_values[0.236] = max(close_prices) - ( (max(close_prices) - min(close_prices))) * 0.236
        fibo_values[0.786] = max(close_prices) - ( (max(close_prices) - min(close_prices))) * 0.786
        
        for i in range(min_index, len(close_prices)):
            if close_prices[i] >= fibo_values[0.786]:
                set_clean_buy_signal(0, symbol)
                break
            set_clean_buy_signal(2, symbol)

        for i in range(max_index, len(close_prices)):
            if close_prices[i] <= fibo_values[0.236]:
                set_clean_sell_signal(0, symbol)
                break
            set_clean_sell_signal(2, symbol)

                
    except Exception as e:
        logger.error(f"Signal Initializer Error: {e}")
        return False