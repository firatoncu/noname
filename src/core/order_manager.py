"""
Order Manager for Trading Operations

This module provides centralized order management functionality,
handling order creation, validation, and execution with proper error handling.
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from binance.enums import SIDE_BUY, SIDE_SELL, ORDER_TYPE_MARKET, ORDER_TYPE_LIMIT

from .base_strategy import PositionSide, TradingSignal, SignalType
from utils.calculate_quantity import calculate_quantity
from utils.position_opt import funding_fee_controller
from utils.globals import set_clean_buy_signal, set_clean_sell_signal


@dataclass
class OrderConfig:
    """Configuration for order management"""
    max_retries: int = 3
    retry_delay: float = 1.0
    validate_funding_fee: bool = True
    min_order_value: float = 10.0  # Minimum order value in USDT


@dataclass
class OrderRequest:
    """Data class for order requests"""
    symbol: str
    side: PositionSide
    quantity: float
    order_type: str = ORDER_TYPE_MARKET
    price: Optional[float] = None
    signal: Optional[TradingSignal] = None


@dataclass
class OrderResult:
    """Data class for order results"""
    success: bool
    order_id: Optional[str] = None
    error_message: Optional[str] = None
    executed_quantity: float = 0.0
    executed_price: float = 0.0


class OrderManager:
    """
    Centralized order management class.
    
    Handles order validation, execution, and tracking with proper
    error handling and retry logic.
    """
    
    def __init__(self, config: OrderConfig = None):
        """
        Initialize order manager.
        
        Args:
            config: Order configuration parameters
        """
        self.config = config or OrderConfig()
        self._pending_orders: Dict[str, OrderRequest] = {}
        self._order_history: List[OrderResult] = []
    
    async def create_market_order(
        self,
        symbol: str,
        side: PositionSide,
        quantity: float,
        client,
        logger,
        signal: Optional[TradingSignal] = None
    ) -> OrderResult:
        """
        Create a market order.
        
        Args:
            symbol: Trading symbol
            side: Order side (LONG/SHORT)
            quantity: Order quantity
            client: Binance client
            logger: Logger instance
            signal: Trading signal that triggered the order
            
        Returns:
            OrderResult with execution details
        """
        order_request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=ORDER_TYPE_MARKET,
            signal=signal
        )
        
        return await self._execute_order(order_request, client, logger)
    
    async def create_limit_order(
        self,
        symbol: str,
        side: PositionSide,
        quantity: float,
        price: float,
        client,
        logger,
        signal: Optional[TradingSignal] = None
    ) -> OrderResult:
        """
        Create a limit order.
        
        Args:
            symbol: Trading symbol
            side: Order side (LONG/SHORT)
            quantity: Order quantity
            price: Limit price
            client: Binance client
            logger: Logger instance
            signal: Trading signal that triggered the order
            
        Returns:
            OrderResult with execution details
        """
        order_request = OrderRequest(
            symbol=symbol,
            side=side,
            quantity=quantity,
            order_type=ORDER_TYPE_LIMIT,
            price=price,
            signal=signal
        )
        
        return await self._execute_order(order_request, client, logger)
    
    async def validate_order(
        self,
        order_request: OrderRequest,
        client,
        logger,
        step_sizes: Dict[str, float],
        quantity_precisions: Dict[str, int]
    ) -> tuple[bool, str]:
        """
        Validate an order before execution.
        
        Args:
            order_request: Order to validate
            client: Binance client
            logger: Logger instance
            step_sizes: Symbol step sizes
            quantity_precisions: Symbol quantity precisions
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            symbol = order_request.symbol
            
            # Check funding fee if enabled
            if self.config.validate_funding_fee:
                funding_fee_ok = await funding_fee_controller(symbol, client, logger)
                if not funding_fee_ok:
                    return False, "Funding fee validation failed"
            
            # Validate quantity precision
            if symbol in step_sizes:
                step_size = step_sizes[symbol]
                if order_request.quantity % step_size != 0:
                    return False, f"Quantity {order_request.quantity} doesn't match step size {step_size}"
            
            # Validate minimum order value
            if order_request.price:
                order_value = order_request.quantity * order_request.price
                if order_value < self.config.min_order_value:
                    return False, f"Order value {order_value} below minimum {self.config.min_order_value}"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Error validating order for {order_request.symbol}: {e}")
            return False, str(e)
    
    async def _execute_order(
        self,
        order_request: OrderRequest,
        client,
        logger
    ) -> OrderResult:
        """
        Execute an order with retry logic.
        
        Args:
            order_request: Order to execute
            client: Binance client
            logger: Logger instance
            
        Returns:
            OrderResult with execution details
        """
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                # Convert to Binance side
                binance_side = SIDE_BUY if order_request.side == PositionSide.LONG else SIDE_SELL
                
                # Prepare order parameters
                order_params = {
                    'symbol': order_request.symbol,
                    'side': binance_side,
                    'type': order_request.order_type,
                    'quantity': order_request.quantity
                }
                
                # Add price for limit orders
                if order_request.order_type == ORDER_TYPE_LIMIT and order_request.price:
                    order_params['price'] = order_request.price
                
                # Execute order
                response = await client.futures_create_order(**order_params)
                
                # Create successful result
                result = OrderResult(
                    success=True,
                    order_id=response.get('orderId'),
                    executed_quantity=float(response.get('executedQty', order_request.quantity)),
                    executed_price=float(response.get('price', order_request.price or 0))
                )
                
                # Update signal state
                self._update_signal_state(order_request)
                
                # Log success
                logger.info(
                    f"Order executed: {order_request.symbol} {order_request.side.value} "
                    f"{order_request.quantity} @ {result.executed_price}"
                )
                
                # Store in history
                self._order_history.append(result)
                
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"Order execution attempt {attempt + 1} failed for {order_request.symbol}: {e}"
                )
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        # All attempts failed
        result = OrderResult(
            success=False,
            error_message=f"Order failed after {self.config.max_retries} attempts: {last_error}"
        )
        
        logger.error(result.error_message)
        self._order_history.append(result)
        
        return result
    
    def _update_signal_state(self, order_request: OrderRequest):
        """Update signal state after order execution"""
        symbol = order_request.symbol
        
        if order_request.side == PositionSide.LONG:
            set_clean_buy_signal(0, symbol)
        else:
            set_clean_sell_signal(0, symbol)
    
    async def cancel_order(self, symbol: str, order_id: str, client, logger) -> bool:
        """
        Cancel an existing order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to cancel
            client: Binance client
            logger: Logger instance
            
        Returns:
            True if cancelled successfully, False otherwise
        """
        try:
            await client.futures_cancel_order(symbol=symbol, orderId=order_id)
            logger.info(f"Cancelled order {order_id} for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id} for {symbol}: {e}")
            return False
    
    async def get_order_status(self, symbol: str, order_id: str, client, logger) -> Optional[Dict[str, Any]]:
        """
        Get the status of an order.
        
        Args:
            symbol: Trading symbol
            order_id: Order ID to check
            client: Binance client
            logger: Logger instance
            
        Returns:
            Order status dictionary or None if error
        """
        try:
            response = await client.futures_get_order(symbol=symbol, orderId=order_id)
            return response
            
        except Exception as e:
            logger.error(f"Error getting order status for {order_id}: {e}")
            return None
    
    def get_order_history(self, limit: Optional[int] = None) -> List[OrderResult]:
        """
        Get order execution history.
        
        Args:
            limit: Maximum number of orders to return
            
        Returns:
            List of OrderResult objects
        """
        if limit:
            return self._order_history[-limit:]
        return self._order_history.copy()
    
    def get_success_rate(self) -> float:
        """
        Calculate order success rate.
        
        Returns:
            Success rate as percentage (0.0 to 100.0)
        """
        if not self._order_history:
            return 0.0
        
        successful_orders = sum(1 for order in self._order_history if order.success)
        return (successful_orders / len(self._order_history)) * 100
    
    def clear_history(self):
        """Clear order history"""
        self._order_history.clear()
    
    def update_config(self, new_config: OrderConfig):
        """Update order configuration"""
        self.config = new_config
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get order execution statistics.
        
        Returns:
            Dictionary with order statistics
        """
        total_orders = len(self._order_history)
        successful_orders = sum(1 for order in self._order_history if order.success)
        failed_orders = total_orders - successful_orders
        
        return {
            "total_orders": total_orders,
            "successful_orders": successful_orders,
            "failed_orders": failed_orders,
            "success_rate": self.get_success_rate(),
            "config": {
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
                "validate_funding_fee": self.config.validate_funding_fee,
                "min_order_value": self.config.min_order_value
            }
        } 