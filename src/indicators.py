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
    
def last500_histogram_check(histogram, lookback_period, logger):
    try:
        last10_avg = (histogram.tail(10).abs()).mean()
        histogram_last_lookback = histogram.tail(lookback_period)
        histogram_variance = histogram_last_lookback.max() + abs(histogram_last_lookback.min())
        histogram_threshold = histogram_variance * 0.3
        if abs(last10_avg) >= histogram_threshold:
            return True
        return False
    except Exception as e:
        logger.error(f"last500_histogram_check hatası: {e}")
        return False