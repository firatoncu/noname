"""
Condition Utilities for Trading Operations

This module provides reusable utility functions for common condition checking
operations, eliminating code duplication across strategies.
"""

import pandas as pd
import numpy as np
from typing import Tuple, Optional, Dict, Any
import ta


def calculate_fibonacci_levels(high_prices: pd.Series, low_prices: pd.Series) -> Dict[float, float]:
    """
    Calculate Fibonacci retracement levels.
    
    Args:
        high_prices: Series of high prices
        low_prices: Series of low prices
        
    Returns:
        Dictionary mapping Fibonacci ratios to price levels
    """
    max_price = high_prices.max()
    min_price = low_prices.min()
    
    fibo_levels = [0, 0.047, 0.236, 0.382, 0.618, 0.786, 0.953, 1]
    fibo_values = {}
    
    for level in fibo_levels:
        fibo_values[level] = max_price - (max_price - min_price) * level
    
    return fibo_values


def check_fibonacci_condition(
    close_prices: pd.Series,
    high_prices: pd.Series,
    low_prices: pd.Series,
    side: str,
    min_range_percentage: float = 0.004
) -> bool:
    """
    Check if Fibonacci retracement conditions are met.
    
    Args:
        close_prices: Series of close prices
        high_prices: Series of high prices
        low_prices: Series of low prices
        side: 'buy' or 'sell'
        min_range_percentage: Minimum range percentage for valid signal
        
    Returns:
        True if conditions are met, False otherwise
    """
    try:
        fibo_values = calculate_fibonacci_levels(high_prices, low_prices)
        
        if side == 'buy':
            return (
                (low_prices.iloc[-1] <= fibo_values[1] or low_prices.iloc[-2] <= fibo_values[1]) and
                close_prices.iloc[-1] > fibo_values[0.953] and
                (fibo_values[0.618] - fibo_values[0.786]) / fibo_values[0.618] > min_range_percentage
            )
        elif side == 'sell':
            return (
                (high_prices.iloc[-1] >= fibo_values[0] or high_prices.iloc[-2] >= fibo_values[0]) and
                close_prices.iloc[-1] < fibo_values[0.047] and
                (fibo_values[0.236] - fibo_values[0.382]) / fibo_values[0.236] > min_range_percentage
            )
        
        return False
        
    except Exception:
        return False


def check_macd_crossover(
    macd_line: pd.Series,
    signal_line: pd.Series,
    side: str,
    threshold_factor: float = 0.2
) -> bool:
    """
    Check if MACD crossover conditions are met.
    
    Args:
        macd_line: MACD line values
        signal_line: MACD signal line values
        side: 'buy' or 'sell'
        threshold_factor: Minimum threshold factor for signal strength
        
    Returns:
        True if crossover conditions are met, False otherwise
    """
    try:
        if len(macd_line) < 2 or len(signal_line) < 2:
            return False
        
        macd_variance = macd_line.max() + abs(macd_line.min())
        macd_threshold = macd_variance * threshold_factor
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        
        if side == "buy":
            return (
                current_macd > current_signal and
                prev_macd < prev_signal and
                abs(current_macd) >= macd_threshold
            )
        elif side == "sell":
            return (
                current_macd < current_signal and
                prev_macd > prev_signal and
                abs(current_macd) >= macd_threshold
            )
        
        return False
        
    except Exception:
        return False


def check_rsi_condition(
    close_prices: pd.Series,
    side: str,
    rsi_period: int = 14,
    buy_threshold: float = 60,
    sell_threshold: float = 40
) -> bool:
    """
    Check if RSI conditions are met.
    
    Args:
        close_prices: Series of close prices
        side: 'buy' or 'sell'
        rsi_period: RSI calculation period
        buy_threshold: RSI threshold for buy signals
        sell_threshold: RSI threshold for sell signals
        
    Returns:
        True if RSI conditions are met, False otherwise
    """
    try:
        rsi = ta.momentum.RSIIndicator(close_prices, window=rsi_period).rsi()
        
        if len(rsi) == 0:
            return False
        
        current_rsi = rsi.iloc[-1]
        
        if side == "buy":
            return current_rsi > buy_threshold
        elif side == "sell":
            return current_rsi < sell_threshold
        
        return False
        
    except Exception:
        return False


def check_bollinger_squeeze(
    close_prices: pd.Series,
    period: int = 20,
    std_dev: float = 2,
    squeeze_percentile: float = 20,
    lookback_periods: int = 100
) -> bool:
    """
    Check if Bollinger Band squeeze conditions are met.
    
    Args:
        close_prices: Series of close prices
        period: Bollinger Band period
        std_dev: Standard deviation multiplier
        squeeze_percentile: Percentile threshold for squeeze detection
        lookback_periods: Number of periods to look back for threshold calculation
        
    Returns:
        True if squeeze conditions are met, False otherwise
    """
    try:
        # Calculate Bollinger Bands
        sma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        band_width = (sma + std_dev * std) - (sma - std_dev * std)
        
        # Calculate threshold
        if len(band_width) >= lookback_periods:
            threshold = np.percentile(band_width.iloc[-lookback_periods:], squeeze_percentile)
        else:
            threshold = np.percentile(band_width.dropna(), squeeze_percentile)
        
        # Check if previous bar indicates squeeze
        return len(band_width) >= 2 and band_width.iloc[-2] < threshold
        
    except Exception:
        return False


def check_price_breakout(
    close_prices: pd.Series,
    side: str,
    period: int = 20,
    std_dev: float = 2,
    percentile_lookback: int = 100
) -> bool:
    """
    Check if price breakout conditions are met.
    
    Args:
        close_prices: Series of close prices
        side: 'buy' or 'sell'
        period: Bollinger Band period
        std_dev: Standard deviation multiplier
        percentile_lookback: Lookback period for percentile calculation
        
    Returns:
        True if breakout conditions are met, False otherwise
    """
    try:
        # Calculate Bollinger Bands
        sma = close_prices.rolling(window=period).mean()
        std = close_prices.rolling(window=period).std()
        upper_band = sma + std_dev * std
        lower_band = sma - std_dev * std
        
        # Calculate percentile levels
        recent_prices = close_prices.iloc[-percentile_lookback:]
        max_price = recent_prices.max()
        min_price = recent_prices.min()
        percentile90 = max_price - (max_price - min_price) * 0.1
        percentile10 = max_price - (max_price - min_price) * 0.9
        
        current_price = close_prices.iloc[-1]
        
        if side == "buy":
            return (
                current_price > upper_band.iloc[-1] and
                current_price > percentile90
            )
        elif side == "sell":
            return (
                current_price < lower_band.iloc[-1] and
                current_price < percentile10
            )
        
        return False
        
    except Exception:
        return False


def check_histogram_condition(
    histogram: pd.Series,
    side: str,
    quantile: float = 0.7,
    lookback_periods: int = 500
) -> bool:
    """
    Check if MACD histogram conditions are met.
    
    Args:
        histogram: MACD histogram values
        side: 'buy' or 'sell'
        quantile: Quantile threshold for signal strength
        lookback_periods: Number of periods to look back
        
    Returns:
        True if histogram conditions are met, False otherwise
    """
    try:
        if len(histogram) < lookback_periods:
            return False
        
        histogram_history = histogram.tail(lookback_periods)
        current_histogram = histogram.iloc[-1]
        
        if side == 'buy':
            histogram_pos = histogram_history[histogram_history > 0]
            if len(histogram_pos) == 0:
                return False
            threshold = histogram_pos.quantile(quantile)
            return current_histogram > threshold
            
        elif side == 'sell':
            histogram_neg = abs(histogram_history[histogram_history < 0])
            if len(histogram_neg) == 0:
                return False
            threshold = histogram_neg.quantile(quantile)
            return current_histogram < -threshold
        
        return False
        
    except Exception:
        return False


def check_trend_strength(
    close_prices: pd.Series,
    high_prices: pd.Series,
    low_prices: pd.Series,
    adx_period: int = 14,
    adx_threshold: float = 25,
    slope_periods: int = 5
) -> Tuple[bool, float]:
    """
    Check trend strength using ADX indicator.
    
    Args:
        close_prices: Series of close prices
        high_prices: Series of high prices
        low_prices: Series of low prices
        adx_period: ADX calculation period
        adx_threshold: Minimum ADX value for strong trend
        slope_periods: Periods for slope calculation
        
    Returns:
        Tuple of (is_trending, adx_value)
    """
    try:
        # Calculate ADX manually
        tr1 = high_prices - low_prices
        tr2 = abs(high_prices - close_prices.shift(1))
        tr3 = abs(low_prices - close_prices.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        up_move = high_prices - high_prices.shift(1)
        down_move = low_prices.shift(1) - low_prices
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        tr_smooth = tr.rolling(window=adx_period, min_periods=1).mean()
        plus_dm_smooth = pd.Series(plus_dm).rolling(window=adx_period, min_periods=1).mean()
        minus_dm_smooth = pd.Series(minus_dm).rolling(window=adx_period, min_periods=1).mean()
        
        plus_di = 100 * (plus_dm_smooth / tr_smooth)
        minus_di = 100 * (minus_dm_smooth / tr_smooth)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(window=adx_period, min_periods=1).mean()
        
        if len(adx) == 0:
            return False, 0.0
        
        latest_adx = adx.iloc[-1]
        
        # Check trend strength
        if latest_adx >= adx_threshold:
            return True, latest_adx
        elif latest_adx >= 22:  # Moderate trend, check slope
            if len(adx) >= slope_periods:
                adx_slope = (adx.iloc[-1] - adx.iloc[-slope_periods]) / slope_periods
                return adx_slope > 0, latest_adx
        
        return False, latest_adx
        
    except Exception:
        return False, 0.0


def validate_signal_conditions(conditions: Dict[str, bool], required_conditions: Optional[list] = None) -> bool:
    """
    Validate that all required signal conditions are met.
    
    Args:
        conditions: Dictionary of condition names and their boolean values
        required_conditions: List of required condition names (if None, all must be True)
        
    Returns:
        True if all required conditions are met, False otherwise
    """
    if required_conditions is None:
        return all(conditions.values())
    
    return all(conditions.get(cond, False) for cond in required_conditions)


def calculate_signal_strength(conditions: Dict[str, bool], weights: Optional[Dict[str, float]] = None) -> float:
    """
    Calculate signal strength based on condition weights.
    
    Args:
        conditions: Dictionary of condition names and their boolean values
        weights: Dictionary of condition weights (if None, equal weights)
        
    Returns:
        Signal strength as float between 0.0 and 1.0
    """
    if not conditions:
        return 0.0
    
    if weights is None:
        # Equal weights
        return sum(conditions.values()) / len(conditions)
    
    # Weighted calculation
    total_weight = sum(weights.get(cond, 1.0) for cond in conditions.keys())
    weighted_sum = sum(
        weights.get(cond, 1.0) * (1.0 if value else 0.0)
        for cond, value in conditions.items()
    )
    
    return weighted_sum / total_weight if total_weight > 0 else 0.0 