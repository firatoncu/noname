"""
RSI Bollinger Bands Trading Strategy

This module implements the RSI Bollinger Bands trading strategy as a concrete
implementation of the BaseStrategy class.
"""

import pandas_ta as ta
from typing import Dict, Any

from ..core.base_strategy import BaseStrategy, TradingSignal, SignalType, MarketData
from ..indicators.rsi_bollinger import (
    rsi_momentum_check, bollinger_squeeze_check, price_breakout_check
)
from utils.globals import (
    get_clean_buy_signal, get_clean_sell_signal,
    set_buyconda, set_buycondb, set_buycondc,
    set_sellconda, set_sellcondb, set_sellcondc
)


class RSIBollingerStrategy(BaseStrategy):
    """
    RSI Bollinger Bands trading strategy implementation.
    
    This strategy combines RSI momentum with Bollinger Band squeeze detection
    and breakout confirmation for trade entries.
    """
    
    def __init__(self, parameters: Dict[str, Any] = None):
        """
        Initialize RSI Bollinger strategy.
        
        Args:
            parameters: Strategy parameters
        """
        default_params = {
            'rsi_period': 14,
            'rsi_buy_threshold': 60,
            'rsi_sell_threshold': 40,
            'bb_period': 20,
            'bb_std_dev': 2,
            'squeeze_percentile': 20,
            'squeeze_lookback': 100,
            'breakout_percentile_high': 90,
            'breakout_percentile_low': 10,
            'breakout_lookback': 100
        }
        
        if parameters:
            default_params.update(parameters)
        
        super().__init__("RSI Bollinger Bands", default_params)
    
    def check_buy_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check buy conditions for RSI Bollinger strategy.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with buy signal information
        """
        try:
            # Check individual conditions
            cond_a = rsi_momentum_check(market_data.close_prices, "buy", symbol, logger)
            cond_b = bollinger_squeeze_check(market_data.close_prices, logger)
            cond_c = price_breakout_check(market_data.close_prices, "buy", logger)
            
            # Update global state (for compatibility)
            set_buyconda(cond_a, symbol)
            set_buycondb(cond_b, symbol)
            set_buycondc(cond_c, symbol)
            
            # Calculate additional indicators for metadata
            rsi = ta.rsi(market_data.close_prices, length=self.get_parameter('rsi_period'))
            sma = ta.sma(market_data.close_prices, length=self.get_parameter('bb_period'))
            std = ta.stdev(market_data.close_prices, length=self.get_parameter('bb_period'))
            upper_band = sma + self.get_parameter('bb_std_dev') * std
            lower_band = sma - self.get_parameter('bb_std_dev') * std
            
            # Calculate signal strength
            conditions = {'rsi_momentum': cond_a, 'bollinger_squeeze': cond_b, 'price_breakout': cond_c}
            signal_strength = sum(conditions.values()) / len(conditions)
            
            # Determine signal type
            signal_type = SignalType.BUY if all(conditions.values()) else SignalType.HOLD
            
            return TradingSignal(
                signal_type=signal_type,
                strength=signal_strength,
                conditions=conditions,
                metadata={
                    'rsi': rsi.iloc[-1] if len(rsi) > 0 else 0,
                    'upper_band': upper_band.iloc[-1] if len(upper_band) > 0 else 0,
                    'lower_band': lower_band.iloc[-1] if len(lower_band) > 0 else 0,
                    'sma': sma.iloc[-1] if len(sma) > 0 else 0,
                    'current_price': market_data.close_price,
                    'clean_signal_state': get_clean_buy_signal(symbol)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in RSI Bollinger buy conditions for {symbol}: {e}")
            return TradingSignal(
                signal_type=SignalType.HOLD,
                strength=0.0,
                conditions={'error': True}
            )
    
    def check_sell_conditions(self, market_data: MarketData, symbol: str, logger) -> TradingSignal:
        """
        Check sell conditions for RSI Bollinger strategy.
        
        Args:
            market_data: Market data for analysis
            symbol: Trading symbol
            logger: Logger instance
            
        Returns:
            TradingSignal with sell signal information
        """
        try:
            # Check individual conditions
            cond_a = rsi_momentum_check(market_data.close_prices, "sell", symbol, logger)
            cond_b = bollinger_squeeze_check(market_data.close_prices, logger)
            cond_c = price_breakout_check(market_data.close_prices, "sell", logger)
            
            # Update global state (for compatibility)
            set_sellconda(cond_a, symbol)
            set_sellcondb(cond_b, symbol)
            set_sellcondc(cond_c, symbol)
            
            # Calculate additional indicators for metadata
            rsi = ta.rsi(market_data.close_prices, length=self.get_parameter('rsi_period'))
            sma = ta.sma(market_data.close_prices, length=self.get_parameter('bb_period'))
            std = ta.stdev(market_data.close_prices, length=self.get_parameter('bb_period'))
            upper_band = sma + self.get_parameter('bb_std_dev') * std
            lower_band = sma - self.get_parameter('bb_std_dev') * std
            
            # Calculate signal strength
            conditions = {'rsi_momentum': cond_a, 'bollinger_squeeze': cond_b, 'price_breakout': cond_c}
            signal_strength = sum(conditions.values()) / len(conditions)
            
            # Determine signal type
            signal_type = SignalType.SELL if all(conditions.values()) else SignalType.HOLD
            
            return TradingSignal(
                signal_type=signal_type,
                strength=signal_strength,
                conditions=conditions,
                metadata={
                    'rsi': rsi.iloc[-1] if len(rsi) > 0 else 0,
                    'upper_band': upper_band.iloc[-1] if len(upper_band) > 0 else 0,
                    'lower_band': lower_band.iloc[-1] if len(lower_band) > 0 else 0,
                    'sma': sma.iloc[-1] if len(sma) > 0 else 0,
                    'current_price': market_data.close_price,
                    'clean_signal_state': get_clean_sell_signal(symbol)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in RSI Bollinger sell conditions for {symbol}: {e}")
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
            'description': 'RSI Bollinger Bands strategy combining RSI momentum with Bollinger Band squeeze and breakout',
            'parameters': self.parameters,
            'conditions': {
                'buy': ['RSI momentum above threshold', 'Bollinger Band squeeze detected', 'Price breakout above upper band'],
                'sell': ['RSI momentum below threshold', 'Bollinger Band squeeze detected', 'Price breakout below lower band']
            },
            'timeframe': 'Multiple (5m primary)',
            'indicators': ['RSI', 'Bollinger Bands', 'SMA'],
            'risk_management': 'Built-in TP/SL with momentum confirmation'
        } 