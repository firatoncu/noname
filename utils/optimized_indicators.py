"""
Optimized Technical Indicators Module

This module provides:
- Cached technical indicator calculations
- Vectorized operations for better performance
- CPU-optimized calculations using numpy
- Memory-efficient indicator computation
- Batch processing capabilities
"""

import numpy as np
import pandas as pd
import ta
import functools
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
import time

from .performance_optimizer import (
    cached, profiled, optimized_cpu, get_cpu_optimizer
)
from .optimized_fetch_data import cached_indicator

logger = logging.getLogger(__name__)


@dataclass
class IndicatorConfig:
    """Configuration for technical indicators."""
    cache_ttl: int = 300  # 5 minutes cache
    enable_vectorization: bool = True
    use_cpu_optimization: bool = True
    batch_size: int = 50


class OptimizedIndicators:
    """Optimized technical indicators with caching and performance improvements."""
    
    def __init__(self, config: IndicatorConfig = None):
        self.config = config or IndicatorConfig()
        self._cpu_optimizer = get_cpu_optimizer()
    
    @cached_indicator("macd", ttl_seconds=300)
    @profiled
    def calculate_macd(
        self,
        close_prices: Union[pd.Series, np.ndarray],
        symbol: str = None,
        window_slow: int = 26,
        window_fast: int = 12,
        window_sign: int = 9
    ) -> Dict[str, np.ndarray]:
        """
        Calculate MACD with optimization.
        
        Returns:
            Dictionary with 'macd', 'signal', and 'histogram' arrays
        """
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.values
        
        # Vectorized MACD calculation
        if self.config.enable_vectorization:
            return self._vectorized_macd(close_prices, window_slow, window_fast, window_sign)
        else:
            # Fallback to ta library
            macd = ta.trend.MACD(
                pd.Series(close_prices),
                window_slow=window_slow,
                window_fast=window_fast,
                window_sign=window_sign
            )
            return {
                'macd': macd.macd().values,
                'signal': macd.macd_signal().values,
                'histogram': macd.macd_diff().values
            }
    
    def _vectorized_macd(
        self,
        close_prices: np.ndarray,
        window_slow: int,
        window_fast: int,
        window_sign: int
    ) -> Dict[str, np.ndarray]:
        """Vectorized MACD calculation using numpy."""
        # Calculate EMAs
        ema_fast = self._calculate_ema(close_prices, window_fast)
        ema_slow = self._calculate_ema(close_prices, window_slow)
        
        # MACD line
        macd_line = ema_fast - ema_slow
        
        # Signal line (EMA of MACD)
        signal_line = self._calculate_ema(macd_line, window_sign)
        
        # Histogram
        histogram = macd_line - signal_line
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }
    
    @cached_indicator("ema", ttl_seconds=300)
    def _calculate_ema(self, data: np.ndarray, window: int) -> np.ndarray:
        """Calculate Exponential Moving Average using vectorized operations."""
        alpha = 2.0 / (window + 1.0)
        ema = np.zeros_like(data)
        ema[0] = data[0]
        
        for i in range(1, len(data)):
            ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
        
        return ema
    
    @cached_indicator("rsi", ttl_seconds=300)
    @profiled
    def calculate_rsi(
        self,
        close_prices: Union[pd.Series, np.ndarray],
        symbol: str = None,
        window: int = 14
    ) -> np.ndarray:
        """Calculate RSI with optimization."""
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.values
        
        if self.config.enable_vectorization:
            return self._vectorized_rsi(close_prices, window)
        else:
            # Fallback to ta library
            return ta.momentum.RSIIndicator(pd.Series(close_prices), window=window).rsi().values
    
    def _vectorized_rsi(self, close_prices: np.ndarray, window: int) -> np.ndarray:
        """Vectorized RSI calculation."""
        deltas = np.diff(close_prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        # Calculate average gains and losses
        avg_gains = np.zeros(len(close_prices))
        avg_losses = np.zeros(len(close_prices))
        
        # Initial averages
        avg_gains[window] = np.mean(gains[:window])
        avg_losses[window] = np.mean(losses[:window])
        
        # Smoothed averages
        for i in range(window + 1, len(close_prices)):
            avg_gains[i] = (avg_gains[i-1] * (window - 1) + gains[i-1]) / window
            avg_losses[i] = (avg_losses[i-1] * (window - 1) + losses[i-1]) / window
        
        # Calculate RSI
        rs = np.divide(avg_gains, avg_losses, out=np.zeros_like(avg_gains), where=avg_losses!=0)
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @cached_indicator("bollinger", ttl_seconds=300)
    @profiled
    def calculate_bollinger_bands(
        self,
        close_prices: Union[pd.Series, np.ndarray],
        symbol: str = None,
        window: int = 20,
        std_dev: float = 2.0
    ) -> Dict[str, np.ndarray]:
        """Calculate Bollinger Bands with optimization."""
        if isinstance(close_prices, pd.Series):
            close_prices = close_prices.values
        
        if self.config.enable_vectorization:
            return self._vectorized_bollinger(close_prices, window, std_dev)
        else:
            # Fallback to ta library
            bb = ta.volatility.BollingerBands(pd.Series(close_prices), window=window, window_dev=std_dev)
            return {
                'upper': bb.bollinger_hband().values,
                'middle': bb.bollinger_mavg().values,
                'lower': bb.bollinger_lband().values
            }
    
    def _vectorized_bollinger(
        self,
        close_prices: np.ndarray,
        window: int,
        std_dev: float
    ) -> Dict[str, np.ndarray]:
        """Vectorized Bollinger Bands calculation."""
        # Calculate rolling mean and std
        rolling_mean = np.convolve(close_prices, np.ones(window)/window, mode='same')
        
        # Calculate rolling standard deviation
        rolling_std = np.zeros_like(close_prices)
        for i in range(window-1, len(close_prices)):
            rolling_std[i] = np.std(close_prices[i-window+1:i+1])
        
        # Calculate bands
        upper_band = rolling_mean + (rolling_std * std_dev)
        lower_band = rolling_mean - (rolling_std * std_dev)
        
        return {
            'upper': upper_band,
            'middle': rolling_mean,
            'lower': lower_band
        }
    
    @cached_indicator("fibonacci", ttl_seconds=300)
    @profiled
    def calculate_fibonacci_levels(
        self,
        high_prices: Union[pd.Series, np.ndarray],
        low_prices: Union[pd.Series, np.ndarray],
        symbol: str = None,
        lookback: int = 500
    ) -> Dict[str, float]:
        """Calculate Fibonacci retracement levels."""
        if isinstance(high_prices, pd.Series):
            high_prices = high_prices.values
        if isinstance(low_prices, pd.Series):
            low_prices = low_prices.values
        
        # Find swing high and low
        recent_high = np.max(high_prices[-lookback:])
        recent_low = np.min(low_prices[-lookback:])
        
        diff = recent_high - recent_low
        
        # Fibonacci levels
        levels = {
            'high': recent_high,
            'low': recent_low,
            'fib_23.6': recent_high - (diff * 0.236),
            'fib_38.2': recent_high - (diff * 0.382),
            'fib_50.0': recent_high - (diff * 0.500),
            'fib_61.8': recent_high - (diff * 0.618),
            'fib_78.6': recent_high - (diff * 0.786)
        }
        
        return levels
    
    @optimized_cpu(use_process_pool=False)
    @profiled
    def batch_calculate_indicators(
        self,
        data_dict: Dict[str, pd.DataFrame],
        indicators: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Calculate multiple indicators for multiple symbols in batch.
        
        Args:
            data_dict: Dictionary mapping symbol to DataFrame
            indicators: List of indicator names to calculate
        
        Returns:
            Dictionary mapping symbol to indicator results
        """
        results = {}
        
        for symbol, df in data_dict.items():
            symbol_results = {}
            
            for indicator in indicators:
                try:
                    if indicator == 'macd':
                        symbol_results['macd'] = self.calculate_macd(df['close'], symbol)
                    elif indicator == 'rsi':
                        symbol_results['rsi'] = self.calculate_rsi(df['close'], symbol)
                    elif indicator == 'bollinger':
                        symbol_results['bollinger'] = self.calculate_bollinger_bands(df['close'], symbol)
                    elif indicator == 'fibonacci':
                        symbol_results['fibonacci'] = self.calculate_fibonacci_levels(
                            df['high'], df['low'], symbol
                        )
                    
                except Exception as e:
                    logger.error(f"Error calculating {indicator} for {symbol}: {e}")
                    symbol_results[indicator] = None
            
            results[symbol] = symbol_results
        
        return results


# Global instance
_indicators: Optional[OptimizedIndicators] = None


def get_indicators() -> OptimizedIndicators:
    """Get global optimized indicators instance."""
    global _indicators
    if _indicators is None:
        _indicators = OptimizedIndicators()
    return _indicators


# Optimized indicator functions for backward compatibility
@profiled
def optimized_macd_check(
    macd_line: Union[pd.Series, np.ndarray],
    signal_line: Union[pd.Series, np.ndarray],
    direction: str,
    symbol: str = None
) -> bool:
    """
    Optimized MACD crossover check.
    
    Args:
        macd_line: MACD line values
        signal_line: Signal line values
        direction: 'buy' or 'sell'
        symbol: Trading symbol for logging
    
    Returns:
        Boolean indicating crossover condition
    """
    if isinstance(macd_line, pd.Series):
        macd_line = macd_line.values
    if isinstance(signal_line, pd.Series):
        signal_line = signal_line.values
    
    if len(macd_line) < 2 or len(signal_line) < 2:
        return False
    
    # Check for crossover
    current_diff = macd_line[-1] - signal_line[-1]
    previous_diff = macd_line[-2] - signal_line[-2]
    
    if direction == "buy":
        # Bullish crossover: MACD crosses above signal
        crossover = previous_diff <= 0 and current_diff > 0
    else:
        # Bearish crossover: MACD crosses below signal
        crossover = previous_diff >= 0 and current_diff < 0
    
    if crossover and symbol:
        logger.debug(f"MACD {direction} crossover detected for {symbol}")
    
    return crossover


@profiled
def optimized_rsi_momentum_check(
    close_prices: Union[pd.Series, np.ndarray],
    direction: str,
    symbol: str = None,
    rsi_period: int = 14,
    oversold_threshold: float = 30,
    overbought_threshold: float = 70
) -> bool:
    """
    Optimized RSI momentum check.
    
    Args:
        close_prices: Close price values
        direction: 'buy' or 'sell'
        symbol: Trading symbol for logging
        rsi_period: RSI calculation period
        oversold_threshold: RSI oversold level
        overbought_threshold: RSI overbought level
    
    Returns:
        Boolean indicating RSI condition
    """
    indicators = get_indicators()
    rsi_values = indicators.calculate_rsi(close_prices, symbol, rsi_period)
    
    if len(rsi_values) < 2:
        return False
    
    current_rsi = rsi_values[-1]
    
    if direction == "buy":
        # Buy when RSI is oversold and starting to recover
        condition = current_rsi < oversold_threshold and current_rsi > rsi_values[-2]
    else:
        # Sell when RSI is overbought and starting to decline
        condition = current_rsi > overbought_threshold and current_rsi < rsi_values[-2]
    
    if condition and symbol:
        logger.debug(f"RSI {direction} condition met for {symbol} (RSI: {current_rsi:.2f})")
    
    return condition


@profiled
def optimized_bollinger_squeeze_check(
    close_prices: Union[pd.Series, np.ndarray],
    symbol: str = None,
    window: int = 20,
    std_dev: float = 2.0
) -> bool:
    """
    Optimized Bollinger Bands squeeze check.
    
    Args:
        close_prices: Close price values
        symbol: Trading symbol for logging
        window: Bollinger Bands period
        std_dev: Standard deviation multiplier
    
    Returns:
        Boolean indicating squeeze condition
    """
    indicators = get_indicators()
    bb_data = indicators.calculate_bollinger_bands(close_prices, symbol, window, std_dev)
    
    if len(bb_data['upper']) < window:
        return False
    
    # Calculate band width (normalized)
    band_width = (bb_data['upper'] - bb_data['lower']) / bb_data['middle']
    
    # Check if current band width is in the lower 20th percentile (squeeze)
    recent_widths = band_width[-50:]  # Last 50 periods
    current_width = band_width[-1]
    
    squeeze_threshold = np.percentile(recent_widths, 20)
    is_squeeze = current_width <= squeeze_threshold
    
    if is_squeeze and symbol:
        logger.debug(f"Bollinger squeeze detected for {symbol}")
    
    return is_squeeze


@profiled
def optimized_price_breakout_check(
    close_prices: Union[pd.Series, np.ndarray],
    direction: str,
    symbol: str = None,
    window: int = 20,
    std_dev: float = 2.0
) -> bool:
    """
    Optimized price breakout check using Bollinger Bands.
    
    Args:
        close_prices: Close price values
        direction: 'buy' or 'sell'
        symbol: Trading symbol for logging
        window: Bollinger Bands period
        std_dev: Standard deviation multiplier
    
    Returns:
        Boolean indicating breakout condition
    """
    indicators = get_indicators()
    bb_data = indicators.calculate_bollinger_bands(close_prices, symbol, window, std_dev)
    
    if len(bb_data['upper']) < 2:
        return False
    
    current_price = close_prices[-1] if isinstance(close_prices, np.ndarray) else close_prices.iloc[-1]
    previous_price = close_prices[-2] if isinstance(close_prices, np.ndarray) else close_prices.iloc[-2]
    
    if direction == "buy":
        # Bullish breakout: price breaks above upper band
        breakout = (previous_price <= bb_data['upper'][-2] and 
                   current_price > bb_data['upper'][-1])
    else:
        # Bearish breakout: price breaks below lower band
        breakout = (previous_price >= bb_data['lower'][-2] and 
                   current_price < bb_data['lower'][-1])
    
    if breakout and symbol:
        logger.debug(f"Price {direction} breakout detected for {symbol}")
    
    return breakout


@profiled
def optimized_fibonacci_check(
    high_prices: Union[pd.Series, np.ndarray],
    low_prices: Union[pd.Series, np.ndarray],
    close_prices: Union[pd.Series, np.ndarray],
    direction: str,
    symbol: str = None,
    lookback: int = 500
) -> bool:
    """
    Optimized Fibonacci retracement level check.
    
    Args:
        high_prices: High price values
        low_prices: Low price values
        close_prices: Close price values
        direction: 'buy' or 'sell'
        symbol: Trading symbol for logging
        lookback: Lookback period for swing high/low
    
    Returns:
        Boolean indicating Fibonacci level condition
    """
    indicators = get_indicators()
    fib_levels = indicators.calculate_fibonacci_levels(high_prices, low_prices, symbol, lookback)
    
    current_price = close_prices[-1] if isinstance(close_prices, np.ndarray) else close_prices.iloc[-1]
    
    # Define tolerance for level touch (0.1%)
    tolerance = 0.001
    
    if direction == "buy":
        # Check if price is near key support levels
        support_levels = [fib_levels['fib_61.8'], fib_levels['fib_50.0'], fib_levels['low']]
        for level in support_levels:
            if abs(current_price - level) / level <= tolerance:
                if symbol:
                    logger.debug(f"Fibonacci buy level hit for {symbol} at {level:.4f}")
                return True
    else:
        # Check if price is near key resistance levels
        resistance_levels = [fib_levels['fib_38.2'], fib_levels['fib_23.6'], fib_levels['high']]
        for level in resistance_levels:
            if abs(current_price - level) / level <= tolerance:
                if symbol:
                    logger.debug(f"Fibonacci sell level hit for {symbol} at {level:.4f}")
                return True
    
    return False


# Performance monitoring for indicators
class IndicatorPerformanceMonitor:
    """Monitor performance of indicator calculations."""
    
    def __init__(self):
        self._calculation_times = {}
        self._cache_stats = {}
    
    def record_calculation_time(self, indicator: str, duration: float):
        """Record calculation time for an indicator."""
        if indicator not in self._calculation_times:
            self._calculation_times[indicator] = []
        self._calculation_times[indicator].append(duration)
        
        # Keep only last 100 measurements
        if len(self._calculation_times[indicator]) > 100:
            self._calculation_times[indicator] = self._calculation_times[indicator][-100:]
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Get performance report for indicators."""
        report = {}
        
        for indicator, times in self._calculation_times.items():
            if times:
                report[indicator] = {
                    'avg_time': np.mean(times),
                    'max_time': np.max(times),
                    'min_time': np.min(times),
                    'total_calculations': len(times)
                }
        
        return report


# Global performance monitor
_performance_monitor = IndicatorPerformanceMonitor()


def get_indicator_performance_monitor() -> IndicatorPerformanceMonitor:
    """Get global indicator performance monitor."""
    return _performance_monitor 