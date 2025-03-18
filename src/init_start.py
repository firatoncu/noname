
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
        close_prices_str, hist_line, macd_line = await initial_data_constructor(client, symbol)

        if macd_line.iloc[-1] < 0: #buy condition

            for i in range(2, 500):

                if macd_line.iloc[-i] > 0:
                    
                    new_macd_line = macd_line.iloc[-i-500:-i]
                    new_close_prices_str = close_prices_str[-500-i:-i]
                    new_hist_line = hist_line[-500-i:-i]

                    buyCondA = last500_fibo_check(new_close_prices_str, "buy", logger)
                    buyCondB = last500_histogram_check(new_hist_line, "buy", logger, histogram_lookback=500)

                    if buyCondA and buyCondB:
                        set_clean_buy_signal(False, symbol)
                    else:
                        set_clean_buy_signal(True, symbol)

                    for i_ in range (2, 500):
                        if new_macd_line.iloc[-i_] < 0:

                            new_macd_line = macd_line.iloc[-500-i_:-i_]
                            new_close_prices_str = close_prices_str[-500-i_:-i_]
                            new_hist_line = hist_line[-500-i_:-i_]
                            
                            sellCondA = last500_fibo_check(new_close_prices_str, "sell", logger)
                            sellCondB = last500_histogram_check(new_hist_line, "sell", logger, histogram_lookback=500)

                            if sellCondA and sellCondB:
                                set_clean_sell_signal(False, symbol)
                                break
                            else:
                                set_clean_sell_signal(True, symbol)
                                break
                        else:
                            set_clean_sell_signal(False, symbol)
                            break

                else:
                    set_clean_sell_signal(False, symbol)
                    set_clean_buy_signal(False, symbol)


        elif macd_line.iloc[-1] > 0:
            for i in range(2, 500):
                if macd_line.iloc[-i] < 0:

                    new_macd_line = macd_line.iloc[-i-500:-i]
                    new_close_prices_str = close_prices_str[-500-i:-i]
                    new_hist_line = hist_line[-500-i:-i]

                    sellCondA = last500_fibo_check(new_close_prices_str, "sell", logger)
                    sellCondB = last500_histogram_check(new_hist_line, "sell", logger, histogram_lookback=500)

                    if sellCondA and sellCondB:
                        set_clean_sell_signal(False, symbol)
                    else:
                        set_clean_sell_signal(True, symbol)

                    for i_ in range (2, 500):
                        if new_macd_line.iloc[-i_] > 0:

                            new_macd_line = macd_line.iloc[-500-i_:-i_]
                            new_close_prices_str = close_prices_str[-500-i_:-i_]
                            new_hist_line = hist_line[-500-i_:-i_]

                            buyCondA = last500_fibo_check(new_close_prices_str, "buy", logger)
                            buyCondB = last500_histogram_check(new_hist_line, "buy", logger, histogram_lookback=500)

                            if buyCondA and buyCondB:
                                set_clean_buy_signal(False, symbol)
                                break
                            else:
                                set_clean_buy_signal(True, symbol)
                                break
                        else:
                            set_clean_buy_signal(False, symbol)
                            break

                else:
                    set_clean_sell_signal(False, symbol)
                    set_clean_buy_signal(False, symbol)
        
        else:
            set_clean_sell_signal(False, symbol)
            set_clean_buy_signal(False, symbol)
                
    except Exception as e:
        logger.error(f"Signal Initializer Error: {e}")
        return False