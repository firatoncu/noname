import ta # type: ignore
from src.indicators import no_crossing_last_10, last500_macd_check, last500_histogram_check


# Alış koşulları
def check_buy_conditions(df, logger):
    try:
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        hist_line = macd.macd_diff()

        slope_macd = macd_line.iloc[-1] - macd_line.iloc[-2]
        slope_signal = signal_line.iloc[-1] - signal_line.iloc[-2]

        std_macd = macd_line.iloc[-21:-1].std()
        threshold = 0.3 * std_macd ** 2

        buyCondA = macd_line[-8:].min() <= macd_line[-20:].min()
        buyCondB = slope_macd ** 2 > slope_signal ** 2 + threshold
        buyCondC = (macd_line.iloc[-1] > signal_line.iloc[-1]) and (macd_line.iloc[-2] <= signal_line.iloc[-2])
        buyCondD = no_crossing_last_10(macd_line, signal_line, logger)
        buyCondE = last500_macd_check(macd_line, 500, logger)
        buyCondF = last500_histogram_check(hist_line, 300, logger)

        return buyCondA and buyCondB and buyCondC and buyCondD and buyCondE and buyCondF
    except Exception as e:
        logger.error(f"check_buy_conditions hatası: {e}")
        return False

# Satış koşulları
def check_sell_conditions(df, logger):
    try:
        macd = ta.trend.MACD(df['close'], window_slow=26, window_fast=12, window_sign=9)
        macd_line = macd.macd()
        signal_line = macd.macd_signal()
        hist_line = macd.macd_diff()

        slope_macd = macd_line.iloc[-1] - macd_line.iloc[-2]
        slope_signal = signal_line.iloc[-1] - signal_line.iloc[-2]

        std_macd = macd_line.iloc[-21:-1].std()
        threshold = 0.3 * std_macd ** 2

        sellCondA = macd_line[-8:].max() >= macd_line[-20:].max()
        sellCondB = -(slope_macd ** 2) < -(slope_signal ** 2) - threshold
        sellCondC = (macd_line.iloc[-1] < signal_line.iloc[-1]) and (macd_line.iloc[-2] >= signal_line.iloc[-2])
        sellCondD = no_crossing_last_10(macd_line, signal_line, logger)
        sellCondE = last500_macd_check(macd_line, 500, logger)
        sellCondF = last500_histogram_check(hist_line, 300, logger)

        return sellCondA and sellCondB and sellCondC and sellCondD and sellCondE and sellCondF
    
    except Exception as e:
        logger.error(f"check_sell_conditions hatası: {e}")
        return False
