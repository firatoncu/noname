"""
Example of integrating the comprehensive monitoring system with the trading bot.

This example shows how to:
- Initialize and configure the monitoring system
- Integrate health checks with existing components
- Set up performance monitoring for trading operations
- Configure alerting for system failures
- Start the monitoring dashboard
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import monitoring components
from src.monitoring import (
    SystemMonitor, MonitoringConfig, HealthChecker, PerformanceMonitor,
    AlertManager, MonitoringDashboard, NotificationConfig,
    AlertSeverity, AlertType, HealthStatus
)

# Import existing trading bot components (example imports)
# from src.async_main import AsyncTradingApplication
# from utils.client_manager import ClientManager
# from utils.async_binance_client import BinanceConfig

logger = logging.getLogger(__name__)


class MonitoredTradingBot:
    """Trading bot with integrated comprehensive monitoring."""
    
    def __init__(self):
        # Configure monitoring
        self.monitoring_config = MonitoringConfig(
            health_check_interval=30.0,
            metrics_collection_interval=5.0,
            cpu_warning_threshold=75.0,
            cpu_critical_threshold=90.0,
            memory_warning_threshold=80.0,
            memory_critical_threshold=95.0,
            notification_config=NotificationConfig(
                # Email configuration
                smtp_server="smtp.gmail.com",
                smtp_port=587,
                smtp_use_tls=True,
                smtp_username="your-email@gmail.com",
                smtp_password="your-app-password",
                email_from="your-email@gmail.com",
                email_to=["admin@yourcompany.com"],
                
                # Webhook configuration for external integrations
                webhook_urls=["https://your-webhook-url.com/alerts"],
                
                # File logging
                log_file="monitoring_alerts.log",
                
                # Slack integration (optional)
                slack_webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                slack_channel="#trading-alerts"
            )
        )
        
        # Initialize monitoring system
        self.system_monitor = SystemMonitor(self.monitoring_config)
        
        # Initialize monitoring dashboard
        self.dashboard = MonitoringDashboard(
            system_monitor=self.system_monitor,
            host="localhost",
            port=8001
        )
        
        # Trading bot components (would be your actual components)
        self.trading_app = None
        self.client_manager = None
        
        # Monitoring state
        self.running = False
    
    async def start(self):
        """Start the monitored trading bot."""
        if self.running:
            return
        
        self.running = True
        logger.info("Starting monitored trading bot...")
        
        try:
            # Start monitoring system first
            await self.system_monitor.start()
            logger.info("Monitoring system started")
            
            # Register custom health checks for trading components
            await self._register_custom_health_checks()
            
            # Start your trading bot components here
            # await self._start_trading_components()
            
            # Start monitoring dashboard
            dashboard_task = asyncio.create_task(self.dashboard.start())
            
            # Register performance monitoring hooks
            self._setup_performance_monitoring()
            
            # Create initial status alert
            await self.system_monitor.create_custom_alert(
                title="Trading Bot Started",
                message="Monitored trading bot has started successfully",
                severity=AlertSeverity.INFO,
                alert_type=AlertType.SYSTEM
            )
            
            logger.info("Monitored trading bot started successfully")
            logger.info("Monitoring dashboard available at: http://localhost:8001")
            
            # Keep running
            await dashboard_task
            
        except Exception as e:
            logger.error(f"Failed to start monitored trading bot: {e}")
            await self.stop()
            raise
    
    async def stop(self):
        """Stop the monitored trading bot."""
        if not self.running:
            return
        
        self.running = False
        logger.info("Stopping monitored trading bot...")
        
        try:
            # Create shutdown alert
            await self.system_monitor.create_custom_alert(
                title="Trading Bot Stopping",
                message="Monitored trading bot is shutting down",
                severity=AlertSeverity.INFO,
                alert_type=AlertType.SYSTEM
            )
            
            # Stop trading components
            # await self._stop_trading_components()
            
            # Stop monitoring dashboard
            await self.dashboard.stop()
            
            # Stop monitoring system
            await self.system_monitor.stop()
            
            logger.info("Monitored trading bot stopped")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
    
    async def _register_custom_health_checks(self):
        """Register custom health checks for trading-specific components."""
        
        # Example: Custom health check for trading engine
        async def check_trading_engine_health(component):
            """Custom health check for trading engine."""
            try:
                # Check if trading engine is responsive
                # This would check your actual trading engine
                
                # Example checks:
                # - Are trading loops running?
                # - Are positions being managed correctly?
                # - Is the strategy executing properly?
                
                # Simulate a health check
                is_healthy = True  # Replace with actual check
                
                if is_healthy:
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'Trading engine is operating normally',
                        'metrics': {
                            'active_positions': 5,  # Example metric
                            'last_trade_time': datetime.now().timestamp()
                        }
                    }
                else:
                    return {
                        'status': HealthStatus.CRITICAL,
                        'message': 'Trading engine is not responding'
                    }
            
            except Exception as e:
                return {
                    'status': HealthStatus.CRITICAL,
                    'message': f'Trading engine health check failed: {str(e)}'
                }
        
        # Register the custom health check
        self.system_monitor.health_checker.register_health_check(
            "trading_engine", check_trading_engine_health
        )
        
        # Example: Custom health check for strategy execution
        async def check_strategy_health(component):
            """Custom health check for trading strategy."""
            try:
                # Check strategy-specific metrics
                # - Signal generation working?
                # - Risk management active?
                # - Performance within acceptable ranges?
                
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Trading strategy is executing normally',
                    'metrics': {
                        'signals_generated_today': 15,
                        'win_rate_24h': 65.5,
                        'risk_exposure': 0.25
                    }
                }
            
            except Exception as e:
                return {
                    'status': HealthStatus.CRITICAL,
                    'message': f'Strategy health check failed: {str(e)}'
                }
        
        # Register strategy health check
        self.system_monitor.health_checker.register_health_check(
            "trading_strategy", check_strategy_health
        )
    
    def _setup_performance_monitoring(self):
        """Setup performance monitoring hooks for trading operations."""
        
        # Example: Monitor trade execution performance
        def monitor_trade_execution(symbol: str, side: str, quantity: float, 
                                  price: float, execution_time_ms: float):
            """Monitor trade execution performance."""
            self.system_monitor.record_trade_execution(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                execution_time=execution_time_ms
            )
        
        # Example: Monitor API call performance
        def monitor_api_call(endpoint: str, response_time_ms: float, 
                           status_code: int, error: str = None):
            """Monitor API call performance."""
            self.system_monitor.record_api_call(
                endpoint=endpoint,
                response_time=response_time_ms,
                status_code=status_code,
                error=error
            )
        
        # You would integrate these monitoring functions into your trading logic
        # For example, in your order execution code:
        # 
        # start_time = time.time()
        # try:
        #     result = await client.create_order(...)
        #     execution_time = (time.time() - start_time) * 1000
        #     monitor_trade_execution(symbol, side, quantity, price, execution_time)
        # except Exception as e:
        #     monitor_api_call("create_order", execution_time, 500, str(e))
    
    async def _start_trading_components(self):
        """Start trading bot components (placeholder)."""
        # This is where you would start your actual trading components
        # For example:
        # 
        # self.trading_app = AsyncTradingApplication()
        # await self.trading_app.initialize()
        # 
        # self.client_manager = ClientManager(binance_config, client_config)
        # await self.client_manager.start()
        
        logger.info("Trading components started (placeholder)")
    
    async def _stop_trading_components(self):
        """Stop trading bot components (placeholder)."""
        # This is where you would stop your actual trading components
        # For example:
        # 
        # if self.client_manager:
        #     await self.client_manager.stop()
        # 
        # if self.trading_app:
        #     await self.trading_app.cleanup()
        
        logger.info("Trading components stopped (placeholder)")
    
    # Example methods for manual monitoring operations
    async def force_health_check(self, component: str = None):
        """Force a health check on a specific component or all components."""
        await self.system_monitor.force_health_check(component)
    
    async def create_custom_alert(self, title: str, message: str, 
                                severity: AlertSeverity = AlertSeverity.INFO):
        """Create a custom alert."""
        return await self.system_monitor.create_custom_alert(title, message, severity)
    
    def get_system_status(self):
        """Get current system status."""
        return self.system_monitor.get_system_status()
    
    def get_performance_summary(self):
        """Get performance summary."""
        return self.system_monitor.get_performance_metrics()
    
    def get_active_alerts(self):
        """Get active alerts."""
        return self.system_monitor.get_active_alerts()


async def main():
    """Main function to run the monitored trading bot."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create and start monitored trading bot
    bot = MonitoredTradingBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await bot.stop()


# Example of how to integrate monitoring into existing trading functions
class TradingOperationMonitor:
    """Helper class to monitor trading operations."""
    
    def __init__(self, system_monitor: SystemMonitor):
        self.system_monitor = system_monitor
    
    async def monitored_order_execution(self, symbol: str, side: str, 
                                      quantity: float, price: float):
        """Example of monitored order execution."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Simulate order execution
            await asyncio.sleep(0.1)  # Simulate API call
            
            # Calculate execution time
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            # Record successful execution
            self.system_monitor.record_trade_execution(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                execution_time=execution_time
            )
            
            # Record API call
            self.system_monitor.record_api_call(
                endpoint="create_order",
                response_time=execution_time,
                status_code=200
            )
            
            logger.info(f"Order executed: {side} {quantity} {symbol} @ {price}")
            
        except Exception as e:
            # Record failed execution
            execution_time = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.system_monitor.record_api_call(
                endpoint="create_order",
                response_time=execution_time,
                status_code=500,
                error=str(e)
            )
            
            # Create alert for failed order
            await self.system_monitor.create_custom_alert(
                title="Order Execution Failed",
                message=f"Failed to execute {side} order for {symbol}: {str(e)}",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.TRADING
            )
            
            raise


if __name__ == "__main__":
    asyncio.run(main()) 