from globals import set_clean_sell_signal, set_clean_buy_signal

# Son 10 mumda çaprazlama kontrolü
def no_crossing_last_10(macd_line, signal_line, logger):
    try:
        for i in range(3, 12):
            if (macd_line.iloc[-i] > signal_line.iloc[-i] and macd_line.iloc[-i-1] <= signal_line.iloc[-i-1]) or \
               (macd_line.iloc[-i] < signal_line.iloc[-i] and macd_line.iloc[-i-1] >= signal_line.iloc[-i-1]):
                return False
        return True
    except Exception as e:
        logger.error(f"no_crossing_last_10 hatası: {e}")
        return False


# Son 500 mumda MACD kontrolü
def last500_macd_check(macd_line, lookback_period, logger):
    try:
        macd_last_500 = macd_line.tail(lookback_period)
        macd_variance = macd_last_500.max() + abs(macd_last_500.min())
        macd_threshold = macd_variance * 0.2
        if abs(macd_line.iloc[-1]) >= macd_threshold:
            return True
        return False
    except Exception as e:
        logger.error(f"last500_macd_check hatası: {e}")
        return False
    
# Son 500 mumda Histogram kontrolü
def last500_histogram_check(histogram, lookback_period, logger):
    try:
        last10_max = max(histogram.tail(10).max(), abs(histogram.tail(10).min()))
        histogram_last_lookback = histogram.tail(lookback_period)
        histogram_variance = histogram_last_lookback.max() + abs(histogram_last_lookback.min())
        histogram_threshold = histogram_variance * 0.15
        if last10_max >= histogram_threshold:
            return True
        return False
    except Exception as e:
        logger.error(f"last500_histogram_check hatası: {e}")
        return False
    
#-|-|-|-|-|-|-|-|-|-|-|-|-v0.5 indicators-|-|-|-|-|-|-|-|-|-|-|-|-

# Son 500 mumda Fibonacci kontrolü
def last500_fibo_check(close_prices_str, side, logger):
    try:
        close_prices = (close_prices_str.astype(float))

        max_price = max(close_prices)
        min_price = min(close_prices)

        fibo_levels = [0.382, 0.5, 0.618]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - (max_price - min_price) * level

        if (side == 'buy' 
            and close_prices.iloc[-5] < fibo_values[0.618] 
            and close_prices.iloc[-4] < fibo_values[0.618] 
            and close_prices.iloc[-3] < fibo_values[0.618] 
            and close_prices.iloc[-2] < fibo_values[0.618] 
            and close_prices.iloc[-1] > fibo_values[0.618] 
            and (fibo_values[0.5] - fibo_values[0.618])/fibo_values[0.618] > 0.006):
            return True
        
        if (side == 'sell' 
            and close_prices.iloc[-5] > fibo_values[0.382] 
            and close_prices.iloc[-4] > fibo_values[0.382] 
            and close_prices.iloc[-3] > fibo_values[0.382] 
            and close_prices.iloc[-2] > fibo_values[0.382] 
            and close_prices.iloc[-1] < fibo_values[0.382] 
            and (fibo_values[0.382] - fibo_values[0.5])/fibo_values[0.5] > 0.006):
            return True
        
        return False
    except Exception as e:
        logger.error(f"last500_fibo_check hatası: {e}")
        return False

# MACD sinyal temizleyici
def signal_cleaner(macd_line, side, symbol, logger):
    try:
        if side == "buy" and macd_line.iloc[-1] < 0 and macd_line.iloc[-2] > 0:
            set_clean_buy_signal(True, symbol)

        if side == "sell" and macd_line.iloc[-1] > 0 and macd_line.iloc[-2] < 0:
            set_clean_sell_signal(True, symbol)
    except Exception as e:
        logger.error(f"last500_fibo_check hatası: {e}")
        