"""
MACD Fibonacci Trading Strategy

This module implements the MACD Fibonacci trading strategy as a concrete
implementation of the BaseStrategy class.
"""

import ta
from typing import Dict, Any

from ..core.base_strategy import BaseStrategy, TradingSignal, SignalType, MarketData
from ..indicators.macd_fibonacci import (
    macd_crossover_check, last500_fibo_check, first_wave_signal,
    last500_histogram_check
)
from utils.globals import (
    get_clean_buy_signal, get_clean_sell_signal,
    set_buyconda, set_buycondb, set_buycondc,
    set_sellconda, set_sellcondb, set_sellcondc
)


class MACDFibonacciStrategy(BaseStrategy):
    """
    MACD Fibonacci trading strategy implementation.
    
    This strategy combines MACD crossover signals with Fibonacci retracement levels
    and implements a multi-step signal confirmation process.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize MACD Fibonacci strategy.
        
        Args:
            parameters: Strategy parameters
        """
        default_params = {
            'macd_fast': 12,
            'macd_slow': 26,
            'macd_signal': 9,
            'macd_threshold_factor': 0.2,
            'fibo_min_range': 0.004,  # Minimum range for fibonacci levels
            'histogram_quantile': 0.7,
            'histogram_lookback': 200
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("MACD Fibonacci", default_params)
    
    def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check buy conditions for MACD Fibonacci strategy.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with buy signal information
        """
        try:
            # Calculate MACD
            macd = ta.trend.MACD(
                market_data.close_prices,
                window_slow=self.get_parameter('macd_slow'),
                window_fast=self.get_parameter('macd_fast'),
                window_sign=self.get_parameter('macd_signal')
            )
            
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            
            # Check individual conditions
            first_wave_signal(
                market_data.close_prices, 
                market_data.high_prices, 
                market_data.low_prices, 
                "buy", symbol, logger
            )
            
            cond_a = macd_crossover_check(macd_line, signal_line, "buy", logger)
            cond_b = last500_fibo_check(
                market_data.close_prices,
                market_data.high_prices,
                market_data.low_prices,
                "buy", logger
            )
            cond_c = get_clean_buy_signal(symbol) == 2
            
            # Update global state (for compatibility)
            set_buyconda(cond_a, symbol)
            set_buycondb(cond_b, symbol)
            set_buycondc(cond_c, symbol)
            
            # Calculate signal strength
            conditions = {'macd_crossover': cond_a, 'fibonacci': cond_b, 'wave_signal': cond_c}
            signal_strength = sum(conditions.values()) / len(conditions)
            
            # Determine signal type
            signal_type = SignalType.BUY if all(conditions.values()) else SignalType.HOLD
            
            return TradingSignal(
                signal_type=signal_type,
                strength=signal_strength,
                conditions=conditions,
                metadata={
                    'macd_line': macd_line.iloc[-1],
                    'signal_line': signal_line.iloc[-1],
                    'clean_signal_state': get_clean_buy_signal(symbol)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in MACD Fibonacci buy conditions for {symbol}: {e}")
            return TradingSignal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                conditions={'error': True}
            )
    
    def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check sell conditions for MACD Fibonacci strategy.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with sell signal information
        """
        try:
            # Calculate MACD
            macd = ta.trend.MACD(
                market_data.close_prices,
                window_slow=self.get_parameter('macd_slow'),
                window_fast=self.get_parameter('macd_fast'),
                window_sign=self.get_parameter('macd_signal')
            )
            
            macd_line = macd.macd()
            signal_line = macd.macd_signal()
            
            # Check individual conditions
            first_wave_signal(
                market_data.close_prices,
                market_data.high_prices,
                market_data.low_prices,
                "sell", symbol, logger
            )
            
            cond_a = macd_crossover_check(macd_line, signal_line, "sell", logger)
            cond_b = last500_fibo_check(
                market_data.close_prices,
                market_data.high_prices,
                market_data.low_prices,
                "sell", logger
            )
            cond_c = get_clean_sell_signal(symbol) == 2
            
            # Update global state (for compatibility)
            set_sellconda(cond_a, symbol)
            set_sellcondb(cond_b, symbol)
            set_sellcondc(cond_c, symbol)
            
            # Calculate signal strength
            conditions = {'macd_crossover': cond_a, 'fibonacci': cond_b, 'wave_signal': cond_c}
            signal_strength = sum(conditions.values()) / len(conditions)
            
            # Determine signal type
            signal_type = SignalType.SELL if all(conditions.values()) else SignalType.HOLD
            
            return TradingSignal(
                signal_type=signal_type,
                strength=signal_strength,
                conditions=conditions,
                metadata={
                    'macd_line': macd_line.iloc[-1],
                    'signal_line': signal_line.iloc[-1],
                    'clean_signal_state': get_clean_sell_signal(symbol)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in MACD Fibonacci sell conditions for {symbol}: {e}")
            return TradingSignal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                conditions={'error': True}
            )
    
    def get_strategy_info(self) -> Dict[str, Any]:
        """
        Get strategy information and parameters.
        
        Returns:
            Dictionary with strategy information
        """
        return {
            'name': self.name,
            'description': 'MACD Fibonacci strategy combining MACD crossover with Fibonacci retracements',
            'parameters': self.parameters,
            'conditions': {
                'buy': ['MACD crossover above signal', 'Fibonacci retracement level', 'Wave signal confirmation'],
                'sell': ['MACD crossover below signal', 'Fibonacci extension level', 'Wave signal confirmation']
            },
            'timeframe': 'Multiple (5m primary)',
            'indicators': ['MACD', 'Fibonacci Retracements'],
            'risk_management': 'Built-in TP/SL with histogram confirmation'
        } 