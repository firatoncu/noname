
from src.indicators import last500_fibo_check, last500_histogram_check
import pandas as pd
import ta
from utils.globals import set_clean_buy_signal, set_clean_sell_signal

async def initial_data_constructor(client, symbol):
            # Get last 1000 candles
        klines = await client.futures_klines(symbol=symbol, interval='1m', limit=1000)
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
        if macd_line.iloc[-1] < 0:
            # En yakın pozitif MACD noktasını bul
            closest_positive_index = None
            for i in range(2, len(macd_line)):
                if macd_line.iloc[-i] > 0:
                    closest_positive_index = len(macd_line) - i
                    break
            
            if closest_positive_index is None:
                # Hiç pozitif nokta yoksa sinyal True
                set_clean_buy_signal(True, symbol)
            else:
                # Pozitif noktadan günümüze kadar her mum için kontrol
                buy_signal_clean = True
                for current_index in range(closest_positive_index, len(macd_line)):
                    # O mumdan geriye doğru son 500 mum (veya mevcut veri kadar)
                    start_index = max(0, current_index - 500)
                    segment_close = close_prices_str[start_index:current_index]
                    segment_hist = hist_line[start_index:current_index]
                    
                    # Alım koşullarını kontrol et
                    buyCondA = last500_fibo_check(segment_close, "buy", logger)
                    buyCondB = last500_histogram_check(segment_hist, "buy", logger, histogram_lookback=500)
                    
                    if buyCondA and buyCondB:
                        buy_signal_clean = False
                        break
                
                set_clean_buy_signal(buy_signal_clean, symbol)
                set_clean_sell_signal(True, symbol)
        
        elif macd_line.iloc[-1] > 0:
            # En yakın negatif MACD noktasını bul
            closest_negative_index = None
            for i in range(2, len(macd_line)):
                if macd_line.iloc[-i] < 0:
                    closest_negative_index = len(macd_line) - i
                    break
            
            if closest_negative_index is None:
                # Hiç negatif nokta yoksa sinyal True
                set_clean_sell_signal(True, symbol)
            else:
                # Negatif noktadan günümüze kadar her mum için kontrol
                sell_signal_clean = True
                for current_index in range(closest_negative_index, len(macd_line)):
                    # O mumdan geriye doğru son 500 mum (veya mevcut veri kadar)
                    start_index = max(0, current_index - 500)
                    segment_close = close_prices_str[start_index:current_index]
                    segment_hist = hist_line[start_index:current_index]
                    
                    # Satım koşullarını kontrol et
                    sellCondA = last500_fibo_check(segment_close, "sell", logger)
                    sellCondB = last500_histogram_check(segment_hist, "sell", logger, histogram_lookback=500)
                    
                    if sellCondA and sellCondB:
                        sell_signal_clean = False
                        break
                
                set_clean_sell_signal(sell_signal_clean, symbol)
                set_clean_buy_signal(True, symbol)
        
        else:
            # MACD sıfırsa her iki sinyal de True
            set_clean_buy_signal(True, symbol)
            set_clean_sell_signal(True, symbol)
                
    except Exception as e:
        logger.error(f"Signal Initializer Error: {e}")
        return False