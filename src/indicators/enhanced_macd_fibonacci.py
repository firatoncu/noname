"""
Enhanced MACD Fibonacci Indicator with SignalManager Integration

This is an enhanced version of the original MACD Fibonacci indicator that demonstrates
how to integrate the new SignalManager system while maintaining backward compatibility.
"""

from utils.signal_globals import (
    set_clean_sell_signal, set_clean_buy_signal, 
    get_clean_buy_signal, get_clean_sell_signal,
    set_buycondc, set_sellcondc, set_strategy_name,
    create_enhanced_buy_signal, create_enhanced_sell_signal,
    create_wave_signal
)
from utils.signal_manager import get_signal_manager, SignalType
import logging

logger = logging.getLogger(__name__)


def enhanced_histogram_check(histogram, side, logger, quantile=1, histogram_lookback=500):
    """
    Enhanced histogram check with confidence calculation.
    
    Returns both the signal result and confidence level.
    """
    try:
        histogram_history = histogram.tail(histogram_lookback)
        confidence = 0.5  # Base confidence
        
        if side == 'buy':
            histogram_pos_lookback = histogram_history[histogram_history > 0]
            if len(histogram_pos_lookback) == 0:
                return False, 0.0
                
            last_max = histogram_pos_lookback.quantile(quantile)
            current_value = histogram.iloc[-1]
            
            if current_value > last_max:
                # Calculate confidence based on how much above the threshold
                excess_ratio = (current_value - last_max) / last_max if last_max != 0 else 0
                confidence = min(0.9, 0.6 + excess_ratio * 0.3)
                return True, confidence
                
        elif side == 'sell':
            histogram_neg_lookback = abs(histogram_history[histogram_history < 0])
            if len(histogram_neg_lookback) == 0:
                return False, 0.0
                
            last_max = histogram_neg_lookback.quantile(quantile)
            current_value = histogram.iloc[-1]
            
            if current_value < -last_max:
                # Calculate confidence based on how much below the threshold
                excess_ratio = abs(current_value + last_max) / last_max if last_max != 0 else 0
                confidence = min(0.9, 0.6 + excess_ratio * 0.3)
                return True, confidence
                
        return False, 0.0
        
    except Exception as e:
        logger.error(f"Enhanced Histogram Checker Error: {e}")
        return False, 0.0


def enhanced_macd_crossover_check(macd_line, signal_line, side, logger):
    """
    Enhanced MACD crossover check with confidence and strength calculation.
    """
    try:
        set_strategy_name("Enhanced MACD Crossover & Fibonacci")
        
        macd_variance = macd_line.max() + abs(macd_line.min())
        macd_threshold = macd_variance * 0.2
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2]
        prev_signal = signal_line.iloc[-2]
        
        # Check for crossover
        crossover_occurred = False
        confidence = 0.5
        strength = 0.0
        conditions_met = []
        
        if side == "buy" and current_macd > current_signal and prev_macd < prev_signal:
            crossover_occurred = True
            conditions_met.append("bullish_crossover")
            
            # Calculate confidence based on MACD strength
            if abs(current_macd) >= macd_threshold:
                conditions_met.append("strong_macd_signal")
                
                # Calculate strength based on distance from signal line
                distance = abs(current_macd - current_signal)
                strength = min(1.0, distance / (macd_variance * 0.1))
                
                # Calculate confidence based on momentum
                momentum = (current_macd - prev_macd) / abs(prev_macd) if prev_macd != 0 else 0
                confidence = min(0.95, 0.7 + abs(momentum) * 0.25)
                
                return True, confidence, strength, conditions_met
                
        elif side == "sell" and current_macd < current_signal and prev_macd > prev_signal:
            crossover_occurred = True
            conditions_met.append("bearish_crossover")
            
            # Calculate confidence based on MACD strength
            if abs(current_macd) >= macd_threshold:
                conditions_met.append("strong_macd_signal")
                
                # Calculate strength based on distance from signal line
                distance = abs(current_macd - current_signal)
                strength = min(1.0, distance / (macd_variance * 0.1))
                
                # Calculate confidence based on momentum
                momentum = (current_macd - prev_macd) / abs(prev_macd) if prev_macd != 0 else 0
                confidence = min(0.95, 0.7 + abs(momentum) * 0.25)
                
                return True, confidence, strength, conditions_met
        
        return False, 0.0, 0.0, []
        
    except Exception as e:
        logger.error(f"Enhanced MACD Crossover Error: {e}")
        return False, 0.0, 0.0, []


def enhanced_fibonacci_check(close_prices_str, high_prices_str, low_prices_str, side, logger):
    """
    Enhanced Fibonacci check with confidence calculation.
    """
    try:
        close_prices = close_prices_str.astype(float)
        high_prices = high_prices_str.astype(float)
        low_prices = low_prices_str.astype(float)

        max_price = max(high_prices)
        min_price = min(low_prices)
        price_range = max_price - min_price

        fibo_levels = [0, 0.047, 0.236, 0.382, 0.618, 0.786, 0.953, 1]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - price_range * level

        confidence = 0.5
        conditions_met = []
        
        # Check range validity
        range_threshold = (fibo_values[0.618] - fibo_values[0.786]) / fibo_values[0.618]
        if range_threshold <= 0.004:
            return False, 0.0, []

        if side == 'buy':
            current_low = low_prices.iloc[-1]
            prev_low = low_prices.iloc[-2]
            current_close = close_prices.iloc[-1]
            
            # Check if price touched lower Fibonacci levels
            touched_support = (current_low <= fibo_values[1] or prev_low <= fibo_values[1])
            above_resistance = current_close > fibo_values[0.953]
            
            if touched_support and above_resistance:
                conditions_met.extend(["fibonacci_support_touch", "above_resistance"])
                
                # Calculate confidence based on how close to ideal levels
                support_distance = abs(min(current_low, prev_low) - fibo_values[1])
                resistance_distance = current_close - fibo_values[0.953]
                
                # Higher confidence for closer touches and stronger breakouts
                support_score = max(0, 1 - (support_distance / (price_range * 0.05)))
                resistance_score = min(1, resistance_distance / (price_range * 0.02))
                
                confidence = min(0.9, 0.6 + (support_score + resistance_score) * 0.15)
                return True, confidence, conditions_met
        
        elif side == 'sell':
            current_high = high_prices.iloc[-1]
            prev_high = high_prices.iloc[-2]
            current_close = close_prices.iloc[-1]
            
            # Check if price touched upper Fibonacci levels
            touched_resistance = (current_high >= fibo_values[0] or prev_high >= fibo_values[0])
            below_support = current_close < fibo_values[0.047]
            
            if touched_resistance and below_support:
                conditions_met.extend(["fibonacci_resistance_touch", "below_support"])
                
                # Calculate confidence based on how close to ideal levels
                resistance_distance = abs(max(current_high, prev_high) - fibo_values[0])
                support_distance = fibo_values[0.047] - current_close
                
                # Higher confidence for closer touches and stronger breakdowns
                resistance_score = max(0, 1 - (resistance_distance / (price_range * 0.05)))
                support_score = min(1, support_distance / (price_range * 0.02))
                
                confidence = min(0.9, 0.6 + (resistance_score + support_score) * 0.15)
                return True, confidence, conditions_met
        
        return False, 0.0, []
        
    except Exception as e:
        logger.error(f"Enhanced Fibonacci Checker Error: {e}")
        return False, 0.0, []


def enhanced_wave_signal(close_prices_str, high_prices_str, low_prices_str, side, symbol, logger):
    """
    Enhanced wave signal with proper SignalManager integration.
    """
    try:
        close_prices = close_prices_str.astype(float)
        high_prices = high_prices_str.astype(float)
        low_prices = low_prices_str.astype(float)

        max_price = max(high_prices)
        min_price = min(low_prices)
        price_range = max_price - min_price

        fibo_levels = [0, 0.382, 0.618, 1]
        fibo_values = {}
        for level in fibo_levels:
            fibo_values[level] = max_price - price_range * level

        current_close = close_prices.iloc[-1]
        prev_close = close_prices.iloc[-2]
        
        # Get current wave signal state
        current_wave_signal = get_clean_buy_signal(symbol) if side == 'buy' else get_clean_sell_signal(symbol)

        if side == 'buy':
            # Stage 1: Initial wave detection
            if (current_close > fibo_values[0.618] and prev_close < fibo_values[0.618]):
                confidence = 0.7
                conditions_met = ["fibonacci_618_breakout"]
                
                # Create enhanced wave signal
                create_wave_signal(
                    symbol=symbol,
                    value=1,
                    confidence=confidence,
                    strategy_name="Enhanced Fibonacci Wave",
                    source_indicator="fibonacci_wave_enhanced",
                    wave_stage=1,
                    conditions_met=conditions_met,
                    expires_in_minutes=120
                )
                
                # Maintain backward compatibility
                set_clean_buy_signal(1, symbol)
                set_buycondc(False, symbol)
                
                logger.info(f"Enhanced buy wave stage 1 detected for {symbol} with confidence {confidence}")

            # Stage 2: Wave confirmation
            elif ((prev_close <= fibo_values[1] or current_close <= fibo_values[1]) and 
                  current_wave_signal == 1):
                
                confidence = 0.9
                conditions_met = ["fibonacci_retracement", "wave_confirmation"]
                
                # Calculate additional confidence factors
                retracement_depth = abs(min(current_close, prev_close) - fibo_values[1])
                if retracement_depth < price_range * 0.02:  # Close to ideal retracement
                    confidence = min(0.95, confidence + 0.05)
                    conditions_met.append("precise_retracement")
                
                # Create enhanced wave signal
                create_wave_signal(
                    symbol=symbol,
                    value=2,
                    confidence=confidence,
                    strategy_name="Enhanced Fibonacci Wave",
                    source_indicator="fibonacci_wave_enhanced",
                    wave_stage=2,
                    conditions_met=conditions_met,
                    expires_in_minutes=60
                )
                
                # Maintain backward compatibility
                set_clean_buy_signal(2, symbol)
                set_buycondc(True, symbol)
                
                logger.info(f"Enhanced buy wave stage 2 confirmed for {symbol} with confidence {confidence}")

        elif side == 'sell':
            # Stage 1: Initial wave detection
            if (current_close < fibo_values[0.382] and prev_close > fibo_values[0.382]):
                confidence = 0.7
                conditions_met = ["fibonacci_382_breakdown"]
                
                # Create enhanced wave signal
                create_wave_signal(
                    symbol=symbol,
                    value=1,
                    confidence=confidence,
                    strategy_name="Enhanced Fibonacci Wave",
                    source_indicator="fibonacci_wave_enhanced",
                    wave_stage=1,
                    conditions_met=conditions_met,
                    expires_in_minutes=120
                )
                
                # Maintain backward compatibility
                set_clean_sell_signal(1, symbol)
                set_sellcondc(False, symbol)
                
                logger.info(f"Enhanced sell wave stage 1 detected for {symbol} with confidence {confidence}")

            # Stage 2: Wave confirmation
            elif ((prev_close >= fibo_values[0] or current_close >= fibo_values[0]) and 
                  current_wave_signal == 1):
                
                confidence = 0.9
                conditions_met = ["fibonacci_resistance_test", "wave_confirmation"]
                
                # Calculate additional confidence factors
                resistance_test = abs(max(current_close, prev_close) - fibo_values[0])
                if resistance_test < price_range * 0.02:  # Close to resistance
                    confidence = min(0.95, confidence + 0.05)
                    conditions_met.append("precise_resistance_test")
                
                # Create enhanced wave signal
                create_wave_signal(
                    symbol=symbol,
                    value=2,
                    confidence=confidence,
                    strategy_name="Enhanced Fibonacci Wave",
                    source_indicator="fibonacci_wave_enhanced",
                    wave_stage=2,
                    conditions_met=conditions_met,
                    expires_in_minutes=60
                )
                
                # Maintain backward compatibility
                set_clean_sell_signal(2, symbol)
                set_sellcondc(True, symbol)
                
                logger.info(f"Enhanced sell wave stage 2 confirmed for {symbol} with confidence {confidence}")

    except Exception as e:
        logger.error(f"Enhanced Wave Signal Error: {e}")


def create_comprehensive_trading_signal(
    macd_line, signal_line, histogram, 
    close_prices, high_prices, low_prices, 
    side, symbol, logger
):
    """
    Create a comprehensive trading signal that combines all indicators with enhanced features.
    """
    try:
        # Get individual signal components with confidence
        macd_result, macd_confidence, macd_strength, macd_conditions = enhanced_macd_crossover_check(
            macd_line, signal_line, side, logger
        )
        
        fibo_result, fibo_confidence, fibo_conditions = enhanced_fibonacci_check(
            close_prices, high_prices, low_prices, side, logger
        )
        
        histogram_result, histogram_confidence = enhanced_histogram_check(
            histogram, side, logger
        )
        
        # Calculate overall confidence and strength
        signal_components = []
        if macd_result:
            signal_components.append(("macd", macd_confidence, macd_strength))
        if fibo_result:
            signal_components.append(("fibonacci", fibo_confidence, 0.8))
        if histogram_result:
            signal_components.append(("histogram", histogram_confidence, 0.6))
        
        if not signal_components:
            return False, 0.0, 0.0, []
        
        # Calculate weighted confidence and strength
        total_weight = sum(comp[1] * comp[2] for comp in signal_components)
        total_confidence = sum(comp[1] for comp in signal_components) / len(signal_components)
        total_strength = total_weight / len(signal_components)
        
        # Combine all conditions
        all_conditions = []
        if macd_result:
            all_conditions.extend(macd_conditions)
        if fibo_result:
            all_conditions.extend(fibo_conditions)
        if histogram_result:
            all_conditions.append("histogram_confirmation")
        
        # Create comprehensive signal
        signal_type = SignalType.BUY if side == "buy" else SignalType.SELL
        
        if side == "buy":
            signal = create_enhanced_buy_signal(
                symbol=symbol,
                value=True,
                confidence=total_confidence,
                strength=total_strength,
                strategy_name="Enhanced MACD Crossover & Fibonacci",
                source_indicator="comprehensive_analysis",
                conditions_met=all_conditions,
                expires_in_minutes=90
            )
        else:
            signal = create_enhanced_sell_signal(
                symbol=symbol,
                value=True,
                confidence=total_confidence,
                strength=total_strength,
                strategy_name="Enhanced MACD Crossover & Fibonacci",
                source_indicator="comprehensive_analysis",
                conditions_met=all_conditions,
                expires_in_minutes=90
            )
        
        logger.info(f"Comprehensive {side} signal created for {symbol}: "
                   f"confidence={total_confidence:.2f}, strength={total_strength:.2f}, "
                   f"conditions={all_conditions}")
        
        return True, total_confidence, total_strength, all_conditions
        
    except Exception as e:
        logger.error(f"Comprehensive Signal Creation Error: {e}")
        return False, 0.0, 0.0, []


# Backward compatibility functions that maintain the original interface
def last500_histogram_check(histogram, side, logger, quantile=1, histogram_lookback=500):
    """Backward compatible histogram check."""
    result, confidence = enhanced_histogram_check(histogram, side, logger, quantile, histogram_lookback)
    return result


def macd_crossover_check(macd_line, signal_line, side, logger):
    """Backward compatible MACD crossover check."""
    result, confidence, strength, conditions = enhanced_macd_crossover_check(macd_line, signal_line, side, logger)
    return result


def last500_fibo_check(close_prices_str, high_prices_str, low_prices_str, side, logger):
    """Backward compatible Fibonacci check."""
    result, confidence, conditions = enhanced_fibonacci_check(close_prices_str, high_prices_str, low_prices_str, side, logger)
    return result


def first_wave_signal(close_prices_str, high_prices_str, low_prices_str, side, symbol, logger):
    """Backward compatible wave signal."""
    enhanced_wave_signal(close_prices_str, high_prices_str, low_prices_str, side, symbol, logger) 