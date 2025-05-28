"""
Position Manager for Trading Operations

This module provides centralized position management functionality,
eliminating code duplication in position handling operations.
"""

import asyncio
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET
import ta

from .base_strategy import PositionSide, MarketData
from utils.position_opt import get_entry_price
from utils.globals import (
    set_error_counter, get_error_counter, get_notif_status, 
    set_order_status, get_order_status, set_limit_order, get_limit_order
)
from utils.send_notification import send_position_close_alert, send_position_open_alert
from src.indicators.macd_fibonacci import last500_histogram_check


@dataclass
class PositionConfig:
    """Configuration for position management"""
    tp_percentage_long: float = 0.003  # 0.3% TP for long
    sl_percentage_long: float = 0.01   # 1% SL for long
    hard_sl_percentage_long: float = 0.017  # 1.7% hard SL for long
    
    tp_percentage_short: float = 0.003  # 0.3% TP for short
    sl_percentage_short: float = 0.01   # 1% SL for short
    hard_sl_percentage_short: float = 0.017  # 1.7% hard SL for short


@dataclass
class Position:
    """Data class representing a trading position"""
    symbol: str
    side: PositionSide
    quantity: float
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    
    def calculate_pnl(self, current_price: float) -> float:
        """Calculate unrealized PnL"""
        if self.side == PositionSide.LONG:
            return (current_price - self.entry_price) * abs(self.quantity)
        elif self.side == PositionSide.SHORT:
            return (self.entry_price - current_price) * abs(self.quantity)
        return 0.0
    
    def calculate_pnl_percentage(self, current_price: float) -> float:
        """Calculate PnL as percentage"""
        if self.entry_price == 0:
            return 0.0
        pnl = self.calculate_pnl(current_price)
        return (pnl / (self.entry_price * abs(self.quantity))) * 100


class PositionManager:
    """
    Centralized position management class.
    
    Handles position opening, closing, monitoring, and risk management
    with configurable parameters and reusable logic.
    """
    
    def __init__(self, config: PositionConfig = None):
        """
        Initialize position manager.
        
        Args:
            config: Position configuration parameters
        """
        self.config = config or PositionConfig()
        self._positions: Dict[str, Position] = {}
    
    async def open_position(
        self, 
        symbol: str, 
        side: PositionSide, 
        quantity: float, 
        client, 
        logger
    ) -> bool:
        """
        Open a new position.
        
        Args:
            symbol: Trading symbol
            side: Position side (LONG/SHORT)
            quantity: Position quantity
            client: Binance client
            logger: Logger instance
            
        Returns:
            True if position opened successfully, False otherwise
        """
        try:
            binance_side = SIDE_BUY if side == PositionSide.LONG else SIDE_SELL
            
            # Create market order
            await client.futures_create_order(
                symbol=symbol, 
                side=binance_side, 
                type=ORDER_TYPE_MARKET, 
                quantity=quantity
            )
            
            # Get entry price and create position record
            entry_price = await get_entry_price(symbol, client, logger)
            position = Position(
                symbol=symbol,
                side=side,
                quantity=quantity,
                entry_price=entry_price
            )
            
            self._positions[symbol] = position
            
            # Send notification
            if get_notif_status():
                await send_position_open_alert(symbol, side.value.upper())
            
            logger.info(f"Opened {side.value} position for {symbol}: {quantity} @ {entry_price}")
            return True
            
        except Exception as e:
            logger.error(f"Error opening position for {symbol}: {e}")
            return False
    
    async def close_position(
        self, 
        symbol: str, 
        client, 
        logger, 
        reason: str = "Manual"
    ) -> bool:
        """
        Close an existing position.
        
        Args:
            symbol: Trading symbol
            client: Binance client
            logger: Logger instance
            reason: Reason for closing (TP, SL, Manual, etc.)
            
        Returns:
            True if position closed successfully, False otherwise
        """
        try:
            if symbol not in self._positions:
                logger.warning(f"No position found for {symbol}")
                return False
            
            position = self._positions[symbol]
            
            # Determine closing side
            binance_side = SIDE_SELL if position.side == PositionSide.LONG else SIDE_BUY
            
            # Create market order to close
            await client.futures_create_order(
                symbol=symbol,
                side=binance_side,
                type=ORDER_TYPE_MARKET,
                quantity=abs(position.quantity)
            )
            
            # Cancel any existing limit orders
            try:
                limit_order = get_limit_order(symbol)
                if limit_order and limit_order != "False":
                    await client.futures_cancel_order(symbol=symbol, orderId=limit_order['orderId'])
            except Exception as e:
                logger.warning(f"Could not cancel limit order for {symbol}: {e}")
            
            # Calculate final PnL
            current_price = position.current_price
            final_pnl = position.calculate_pnl(current_price)
            
            # Update error counter and send notification
            if reason == "TP":
                set_error_counter(0)
                if get_notif_status():
                    await send_position_close_alert(True, symbol, position.side.value.upper(), abs(final_pnl))
            else:
                set_error_counter(get_error_counter() + 1)
                if get_notif_status():
                    await send_position_close_alert(False, symbol, position.side.value.upper(), abs(final_pnl))
            
            # Remove position from tracking
            del self._positions[symbol]
            
            logger.info(f"Closed {position.side.value} position for {symbol}: PnL = {final_pnl:.2f} ({reason})")
            return True
            
        except Exception as e:
            logger.error(f"Error closing position for {symbol}: {e}")
            return False
    
    async def monitor_position(
        self, 
        symbol: str, 
        market_data: MarketData, 
        client, 
        logger,
        price_precisions: Dict[str, int]
    ) -> bool:
        """
        Monitor an existing position for TP/SL conditions.
        
        Args:
            symbol: Trading symbol
            market_data: Current market data
            client: Binance client
            logger: Logger instance
            price_precisions: Price precision mapping
            
        Returns:
            True if position was closed, False if still open
        """
        try:
            if symbol not in self._positions:
                return False
            
            position = self._positions[symbol]
            current_price = market_data.close_price
            position.current_price = current_price
            
            # Calculate TP/SL levels
            tp_price, sl_price, hard_sl_price = self._calculate_tp_sl_levels(
                position, price_precisions.get(symbol, 8)
            )
            
            # Check histogram conditions for SL
            histogram_check = await self._check_histogram_conditions(
                market_data, position.side, logger
            )
            
            # Check exit conditions
            should_close, reason = self._should_close_position(
                position, current_price, tp_price, sl_price, hard_sl_price, histogram_check
            )
            
            if should_close:
                await self.close_position(symbol, client, logger, reason)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error monitoring position for {symbol}: {e}")
            return False
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a symbol"""
        return self._positions.get(symbol)
    
    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position for a symbol"""
        return symbol in self._positions
    
    def get_all_positions(self) -> Dict[str, Position]:
        """Get all open positions"""
        return self._positions.copy()
    
    def _calculate_tp_sl_levels(self, position: Position, price_precision: int) -> Tuple[float, float, float]:
        """Calculate TP, SL, and hard SL levels for a position"""
        entry_price = position.entry_price
        
        if position.side == PositionSide.LONG:
            tp_price = round(entry_price * (1 + self.config.tp_percentage_long), price_precision)
            sl_price = round(entry_price * (1 - self.config.sl_percentage_long), price_precision)
            hard_sl_price = round(entry_price * (1 - self.config.hard_sl_percentage_long), price_precision)
        else:  # SHORT
            tp_price = round(entry_price * (1 - self.config.tp_percentage_short), price_precision)
            sl_price = round(entry_price * (1 + self.config.sl_percentage_short), price_precision)
            hard_sl_price = round(entry_price * (1 + self.config.hard_sl_percentage_short), price_precision)
        
        return tp_price, sl_price, hard_sl_price
    
    async def _check_histogram_conditions(self, market_data: MarketData, position_side: PositionSide, logger) -> bool:
        """Check MACD histogram conditions for position exit"""
        try:
            macd = ta.trend.MACD(market_data.close_prices, window_slow=26, window_fast=12, window_sign=9)
            histogram = macd.macd_diff()
            
            if position_side == PositionSide.LONG:
                return last500_histogram_check(histogram, "sell", logger, quantile=0.7, histogram_lookback=200)
            else:  # SHORT
                return last500_histogram_check(histogram, "buy", logger, quantile=0.7, histogram_lookback=200)
                
        except Exception as e:
            logger.error(f"Error checking histogram conditions: {e}")
            return False
    
    def _should_close_position(
        self, 
        position: Position, 
        current_price: float, 
        tp_price: float, 
        sl_price: float, 
        hard_sl_price: float, 
        histogram_check: bool
    ) -> Tuple[bool, str]:
        """Determine if position should be closed and why"""
        
        if position.side == PositionSide.LONG:
            if current_price >= tp_price:
                return True, "TP"
            elif current_price <= hard_sl_price:
                return True, "Hard SL"
            elif current_price <= sl_price and histogram_check:
                return True, "SL + Histogram"
        else:  # SHORT
            if current_price <= tp_price:
                return True, "TP"
            elif current_price >= hard_sl_price:
                return True, "Hard SL"
            elif current_price >= sl_price and histogram_check:
                return True, "SL + Histogram"
        
        return False, ""
    
    def update_config(self, new_config: PositionConfig):
        """Update position configuration"""
        self.config = new_config
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get summary of all positions"""
        summary = {
            "total_positions": len(self._positions),
            "long_positions": sum(1 for p in self._positions.values() if p.side == PositionSide.LONG),
            "short_positions": sum(1 for p in self._positions.values() if p.side == PositionSide.SHORT),
            "positions": {}
        }
        
        for symbol, position in self._positions.items():
            summary["positions"][symbol] = {
                "side": position.side.value,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "current_price": position.current_price,
                "unrealized_pnl": position.calculate_pnl(position.current_price),
                "pnl_percentage": position.calculate_pnl_percentage(position.current_price)
            }
        
        return summary 