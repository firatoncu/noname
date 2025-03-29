from utils.globals import set_clean_sell_signal, set_clean_buy_signal, get_clean_buy_signal, get_clean_sell_signal, set_buycondc, set_sellcondc

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
    

#-|-|-|-|-|-|-|-|-|-|-|-|-v0.5 indicators-|-|-|-|-|-|-|-|-|-|-|-|-

def last500_histogram_check(histogram, side, logger, quantile=1, histogram_lookback=500):
    try:
        histogram_history = histogram.tail(histogram_lookback)
        if side == 'buy':
            histogram_pos_lookback = histogram_history[histogram_history > 0]
            last10_max = histogram_pos_lookback.quantile(quantile)
            if histogram.iloc[-1] > last10_max:
                return True
        if side == 'sell':
            histogram_neg_lookback = abs(histogram_history[histogram_history < 0])
            last10_max = histogram_neg_lookback.quantile(quantile)
            if histogram.iloc[-1] < -last10_max:
                return True
        return False
    except Exception as e:
        logger.error(f"Histogram Checker Error: {e}")
        return False

def last500_fibo_check(close_prices_str, high_prices_str, low_prices_str, side, logger):
    try:
        close_prices = (close_prices_str.astype(float))
        high_prices = (high_prices_str.astype(float))
        low_prices = (low_prices_str.astype(float))

        max_price = max(high_prices)
        min_price = min(low_prices)

        fibo_levels = [0.047, 0.236, 0.382, 0.5, 0.618, 0.786, 0.953]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - (max_price - min_price) * level

        if (side == 'buy' 
            and close_prices.iloc[-4] < fibo_values[0.786]
            and close_prices.iloc[-3] < fibo_values[0.786] 
            and close_prices.iloc[-2] > fibo_values[0.786] 
            and close_prices.iloc[-1] > fibo_values[0.786]
            and (fibo_values[0.618] - fibo_values[0.786])/fibo_values[0.618] > 0.004):
            return True
        
        if (side == 'sell' 
            and close_prices.iloc[-4] > fibo_values[0.236]
            and close_prices.iloc[-3] > fibo_values[0.236]
            and close_prices.iloc[-2] < fibo_values[0.236] 
            and close_prices.iloc[-1] < fibo_values[0.236] 
            and (fibo_values[0.236] - fibo_values[0.382])/fibo_values[0.236] > 0.004):
            return True
        
        return False
    except Exception as e:
        logger.error(f"Fibonacci Checker Error: {e}")
        return False
    

"""def signal_cleaner(macd_line, side, symbol, logger):
    try:
        if side == "buy" and macd_line.iloc[-1] < 0 and macd_line.iloc[-2] > 0:
            set_clean_buy_signal(True, symbol)
        if side == "sell" and macd_line.iloc[-1] > 0 and macd_line.iloc[-2] < 0:
            set_clean_sell_signal(True, symbol)
    except Exception as e:
        logger.error(f"Signal Cleaner Error: {e}")"""
        

def trending_macd_crossover_check(macd_line, signal_line, side, logger):
    try:
        if side == "buy" and macd_line.iloc[-1] > signal_line.iloc[-1] and macd_line.iloc[-2] < signal_line.iloc[-2]:
            return True
        elif side == "sell" and macd_line.iloc[-1] < signal_line.iloc[-1] and macd_line.iloc[-2] > signal_line.iloc[-2]:
            return True
        else:
            return False
        
    except Exception as e:
        logger.error(f"Signal Cleaner Error: {e}")


def trending_last500_fibo_check(close_prices_str, high_prices_str, low_prices_str, side, logger):
    try:
        close_prices = (close_prices_str.astype(float))
        high_prices = (high_prices_str.astype(float))
        low_prices = (low_prices_str.astype(float))

        max_price = max(high_prices)
        min_price = min(low_prices)

        fibo_levels = [0, 0.047, 0.236, 0.382, 0.618, 0.786, 0.953, 1]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - (max_price - min_price) * level

        if (side == 'buy' 
            and (low_prices.iloc[-1] <= fibo_values[1] or low_prices.iloc[-2] <= fibo_values[1])
            and close_prices.iloc[-1] > fibo_values[0.953]
            and (fibo_values[0.618] - fibo_values[0.786])/fibo_values[0.618] > 0.004):
            return True
        
        if (side == 'sell' 
            and (high_prices.iloc[-1] >= fibo_values[0] or high_prices.iloc[-2] >= fibo_values[0])
            and close_prices.iloc[-1] < fibo_values[0.047]
            and (fibo_values[0.236] - fibo_values[0.382])/fibo_values[0.236] > 0.004):
            return True
        
        return False
    except Exception as e:
        logger.error(f"Fibonacci Checker Error: {e}")
        return False

def first_wave_signal(close_prices_str, high_prices_str, low_prices_str, side, symbol, logger):
    try:
        close_prices = (close_prices_str.astype(float))
        high_prices = (high_prices_str.astype(float))
        low_prices = (low_prices_str.astype(float))

        max_price = max(high_prices)
        min_price = min(low_prices)

        fibo_levels = [0, 0.382, 0.618, 1]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - (max_price - min_price) * level

        if (side == 'buy' 
            and close_prices.iloc[-1] > fibo_values[0.618]
            and close_prices.iloc[-2] < fibo_values[0.618]):
            set_clean_buy_signal(1, symbol)
            set_buycondc(False, symbol)

        if (side == 'buy' 
            and (close_prices.iloc[-2] <= fibo_values[1] or close_prices.iloc[-1] <= fibo_values[1])
            and get_clean_buy_signal(symbol) == 1):
            set_clean_buy_signal(2, symbol)
            set_buycondc(True, symbol)

        if (side == 'sell'
            and close_prices.iloc[-1] < fibo_values[0.382]
            and close_prices.iloc[-2] > fibo_values[0.382]):
            set_clean_sell_signal(1, symbol)
            set_sellcondc(False, symbol)

        if (side == 'sell'
            and (close_prices.iloc[-2] >= fibo_values[0] or close_prices.iloc[-1] >= fibo_values[0])
            and get_clean_sell_signal(symbol) == 1):
            set_clean_sell_signal(2, symbol)
            set_sellcondc(True, symbol)
            

    except Exception as e:
        logger.error(f"First Wave Error: {e}")
        return False