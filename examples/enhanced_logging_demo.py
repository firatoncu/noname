#!/usr/bin/env python3
"""
Enhanced Logging and Exception Handling Demo

This script demonstrates the capabilities of the new enhanced logging
and exception handling systems.
"""

import asyncio
import time
import random
from typing import List

# Import the enhanced logging and exception handling
from utils.enhanced_logging import (
    get_logger, 
    ErrorCategory, 
    LogSeverity,
    log_performance,
    log_exceptions
)
from utils.exceptions import (
    TradingBotException,
    NetworkException,
    APIException,
    DataValidationException,
    TradingException,
    RecoveryManager,
    handle_exceptions,
    create_error_context,
    validate_data,
    RetryConfig
)


class TradingDemo:
    """Demo class showing enhanced logging and exception handling"""
    
    def __init__(self):
        self.logger = get_logger("trading_demo")
        self.recovery_manager = RecoveryManager(self.logger)
    
    @log_performance()
    async def simulate_api_call(self, endpoint: str, success_rate: float = 0.8):
        """Simulate an API call with potential failures"""
        await asyncio.sleep(random.uniform(0.1, 0.5))  # Simulate network delay
        
        if random.random() > success_rate:
            if random.random() > 0.5:
                raise NetworkException(
                    "Connection timeout",
                    context=create_error_context(
                        component="api_client",
                        operation="simulate_api_call",
                        endpoint=endpoint
                    )
                )
            else:
                raise APIException(
                    "API rate limit exceeded",
                    api_endpoint=endpoint,
                    status_code=429,
                    context=create_error_context(
                        component="api_client",
                        operation="simulate_api_call",
                        endpoint=endpoint
                    )
                )
        
        return {"status": "success", "data": f"Response from {endpoint}"}
    
    @validate_data({
        'symbol': lambda x: isinstance(x, str) and len(x) > 0,
        'quantity': lambda x: isinstance(x, (int, float)) and x > 0,
        'price': lambda x: isinstance(x, (int, float)) and x > 0
    })
    def validate_order_data(self, symbol: str, quantity: float, price: float):
        """Demonstrate data validation"""
        return {"symbol": symbol, "quantity": quantity, "price": price}
    
    @handle_exceptions(fallback_value=None)
    async def risky_trading_operation(self, symbol: str):
        """Simulate a risky trading operation"""
        with self.logger.context(symbol=symbol, operation="risky_trading"):
            self.logger.info("Starting risky trading operation")
            
            # Simulate various types of errors
            error_type = random.choice(["network", "api", "trading", "data", "success"])
            
            if error_type == "network":
                raise NetworkException(
                    "Network connection lost",
                    context=create_error_context(
                        component="trading_engine",
                        operation="risky_trading_operation",
                        symbol=symbol
                    )
                )
            elif error_type == "api":
                raise APIException(
                    "API authentication failed",
                    api_endpoint="/api/v3/order",
                    status_code=401
                )
            elif error_type == "trading":
                raise TradingException(
                    "Insufficient balance for trade",
                    context=create_error_context(
                        component="position_manager",
                        operation="open_position",
                        symbol=symbol
                    )
                )
            elif error_type == "data":
                raise DataValidationException(
                    "Invalid price data received",
                    field_name="price",
                    expected_type="float",
                    actual_value="invalid"
                )
            else:
                self.logger.info("Trading operation completed successfully")
                return {"status": "success", "symbol": symbol}
    
    async def demonstrate_context_logging(self):
        """Demonstrate context-aware logging"""
        correlation_id = f"demo_{int(time.time())}"
        
        with self.logger.context(
            correlation_id=correlation_id,
            component="demo",
            operation="context_demo"
        ):
            self.logger.info("Starting context logging demonstration")
            
            # Nested context
            with self.logger.context(symbol="BTCUSDT", strategy="demo_strategy"):
                self.logger.info("Processing symbol with strategy")
                self.logger.warning("Low volume detected")
                
                # Even deeper nesting
                with self.logger.context(action="place_order"):
                    self.logger.info("Placing order")
                    self.logger.error(
                        "Order placement failed",
                        category=ErrorCategory.TRADING,
                        severity=LogSeverity.HIGH
                    )
            
            self.logger.info("Context logging demonstration completed")
    
    async def demonstrate_performance_logging(self):
        """Demonstrate performance logging"""
        self.logger.info("Starting performance logging demonstration")
        
        # Manual performance logging
        start_time = time.time()
        await asyncio.sleep(0.2)  # Simulate work
        duration = time.time() - start_time
        
        self.logger.performance(
            "manual_operation",
            duration,
            records_processed=100,
            cache_hits=85,
            cache_misses=15
        )
        
        # Using decorator (already demonstrated in simulate_api_call)
        await self.simulate_api_call("/api/v3/ticker", success_rate=1.0)
        
        self.logger.info("Performance logging demonstration completed")
    
    async def demonstrate_error_categorization(self):
        """Demonstrate error categorization and severity levels"""
        self.logger.info("Starting error categorization demonstration")
        
        # Different error categories and severities
        error_scenarios = [
            (ErrorCategory.NETWORK, LogSeverity.HIGH, "Network timeout occurred"),
            (ErrorCategory.API, LogSeverity.MEDIUM, "API rate limit warning"),
            (ErrorCategory.TRADING, LogSeverity.CRITICAL, "Risk management violation"),
            (ErrorCategory.DATA, LogSeverity.LOW, "Minor data inconsistency"),
            (ErrorCategory.SYSTEM, LogSeverity.CRITICAL, "System resource exhausted"),
        ]
        
        for category, severity, message in error_scenarios:
            self.logger.error(
                message,
                category=category,
                severity=severity,
                extra={"scenario": "demonstration"}
            )
        
        self.logger.info("Error categorization demonstration completed")
    
    async def demonstrate_exception_recovery(self):
        """Demonstrate exception handling and recovery"""
        self.logger.info("Starting exception recovery demonstration")
        
        symbols = ["BTCUSDT", "ETHUSDT", "ADAUSDT"]
        
        for symbol in symbols:
            try:
                result = await self.risky_trading_operation(symbol)
                if result:
                    self.logger.info(f"Operation succeeded for {symbol}")
                else:
                    self.logger.warning(f"Operation returned fallback value for {symbol}")
            except Exception as e:
                self.logger.exception(
                    f"Unhandled exception for {symbol}",
                    category=ErrorCategory.SYSTEM,
                    severity=LogSeverity.HIGH
                )
        
        self.logger.info("Exception recovery demonstration completed")
    
    async def demonstrate_data_validation(self):
        """Demonstrate data validation"""
        self.logger.info("Starting data validation demonstration")
        
        # Valid data
        try:
            result = self.validate_order_data("BTCUSDT", 0.001, 50000.0)
            self.logger.info("Valid data processed successfully", extra=result)
        except Exception as e:
            self.logger.error("Unexpected validation error", extra={"error": str(e)})
        
        # Invalid data
        invalid_scenarios = [
            ("", 0.001, 50000.0),  # Empty symbol
            ("BTCUSDT", -0.001, 50000.0),  # Negative quantity
            ("BTCUSDT", 0.001, -50000.0),  # Negative price
        ]
        
        for symbol, quantity, price in invalid_scenarios:
            try:
                result = self.validate_order_data(symbol, quantity, price)
                self.logger.warning("Validation should have failed", extra={
                    "symbol": symbol, "quantity": quantity, "price": price
                })
            except DataValidationException as e:
                self.logger.info(
                    "Data validation correctly caught invalid data",
                    extra=e.to_dict()
                )
        
        self.logger.info("Data validation demonstration completed")
    
    async def demonstrate_audit_logging(self):
        """Demonstrate audit logging"""
        self.logger.info("Starting audit logging demonstration")
        
        # Audit events
        self.logger.audit("User login successful", extra={"user_id": "demo_user"})
        self.logger.audit("Trading strategy changed", extra={
            "old_strategy": "MACD",
            "new_strategy": "Bollinger Bands",
            "changed_by": "demo_user"
        })
        self.logger.audit("Position opened", extra={
            "symbol": "BTCUSDT",
            "side": "LONG",
            "quantity": 0.001,
            "price": 50000.0
        })
        self.logger.audit("System configuration updated", extra={
            "config_key": "max_positions",
            "old_value": 5,
            "new_value": 10
        })
        
        self.logger.info("Audit logging demonstration completed")
    
    def demonstrate_metrics(self):
        """Demonstrate logging metrics"""
        self.logger.info("Starting metrics demonstration")
        
        # Get current metrics
        metrics = self.logger.get_metrics()
        
        self.logger.info("Current logging metrics", extra={
            "total_logs": metrics['total_logs'],
            "error_count": metrics['error_count'],
            "warning_count": metrics['warning_count'],
            "critical_count": metrics['critical_count'],
            "errors_by_category": metrics['errors_by_category']
        })
        
        self.logger.info("Metrics demonstration completed")
    
    async def run_all_demonstrations(self):
        """Run all demonstrations"""
        self.logger.info("Starting enhanced logging and exception handling demo")
        
        demonstrations = [
            self.demonstrate_context_logging,
            self.demonstrate_performance_logging,
            self.demonstrate_error_categorization,
            self.demonstrate_exception_recovery,
            self.demonstrate_data_validation,
            self.demonstrate_audit_logging,
        ]
        
        for demo in demonstrations:
            try:
                await demo()
                await asyncio.sleep(0.5)  # Small delay between demos
            except Exception as e:
                self.logger.exception(
                    f"Error in demonstration: {demo.__name__}",
                    category=ErrorCategory.SYSTEM,
                    severity=LogSeverity.HIGH
                )
        
        # Show final metrics
        self.demonstrate_metrics()
        
        self.logger.info("All demonstrations completed")
        self.logger.audit("Demo session completed successfully")


async def main():
    """Main demo function"""
    print("Enhanced Logging and Exception Handling Demo")
    print("=" * 50)
    print("This demo will show various logging and exception handling features.")
    print("Check the 'logs' directory for generated log files.")
    print("=" * 50)
    
    demo = TradingDemo()
    await demo.run_all_demonstrations()
    
    print("\nDemo completed! Check the following log files:")
    print("- logs/all.log - All log messages")
    print("- logs/error.log - Error messages only")
    print("- logs/warning.log - Warning messages and above")
    print("- logs/audit.log - Audit trail events")
    print("- logs/performance.log - Performance metrics")


if __name__ == "__main__":
    asyncio.run(main()) 