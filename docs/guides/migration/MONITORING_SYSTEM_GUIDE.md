# Comprehensive Monitoring System Guide

## Overview

The comprehensive monitoring system provides real-time health checks, performance monitoring, and alerting for your trading bot. It includes:

- **Health Checker**: Monitors all system components (API connections, database, web UI, system resources)
- **Performance Monitor**: Tracks trading operations, system metrics, and API performance
- **Alert Manager**: Multi-channel alerting with deduplication and escalation
- **Monitoring Dashboard**: Web-based real-time monitoring interface
- **System Monitor**: Unified coordinator that integrates all monitoring components

## Features

### Health Monitoring
- ✅ API connection health (Binance, other exchanges)
- ✅ Database connectivity (InfluxDB)
- ✅ Web UI component status
- ✅ System resource monitoring (CPU, memory, disk)
- ✅ Network connectivity checks
- ✅ Trading engine health
- ✅ Custom component health checks

### Performance Monitoring
- 📊 Trading performance metrics (P&L, win rate, execution times)
- 📊 System performance (CPU, memory, network I/O)
- 📊 API response times and error rates
- 📊 Real-time metrics collection and aggregation
- 📊 Historical performance data

### Alerting System
- 🚨 Multi-channel notifications (Email, Webhook, Console, File, Slack, Telegram)
- 🚨 Alert severity levels (Info, Warning, Critical, Emergency)
- 🚨 Alert deduplication and rate limiting
- 🚨 Automatic escalation
- 🚨 Alert acknowledgment and resolution

### Monitoring Dashboard
- 🖥️ Real-time web interface
- 🖥️ Interactive charts and graphs
- 🖥️ Component health overview
- 🖥️ Alert management
- 🖥️ Performance metrics visualization

## Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. The monitoring system requires these additional packages:
- `fastapi>=0.104.0` - Web framework for dashboard
- `uvicorn[standard]>=0.24.0` - ASGI server
- `websockets>=12.0` - Real-time updates
- `psutil>=5.9.0` - System monitoring
- `email-validator>=2.1.0` - Email validation

## Quick Start

### Basic Usage

```python
import asyncio
from src.monitoring import SystemMonitor, MonitoringConfig, NotificationConfig

# Configure monitoring
config = MonitoringConfig(
    health_check_interval=30.0,
    metrics_collection_interval=5.0,
    notification_config=NotificationConfig(
        email_from="bot@yourcompany.com",
        email_to=["admin@yourcompany.com"]
    )
)

# Initialize system monitor
system_monitor = SystemMonitor(config)

async def main():
    # Start monitoring
    await system_monitor.start()
    
    # Your application code here
    await asyncio.sleep(3600)  # Run for 1 hour
    
    # Stop monitoring
    await system_monitor.stop()

asyncio.run(main())
```

### With Dashboard

```python
from src.monitoring import SystemMonitor, MonitoringDashboard

# Initialize monitoring
system_monitor = SystemMonitor()
dashboard = MonitoringDashboard(system_monitor, port=8001)

async def main():
    await system_monitor.start()
    await dashboard.start()  # Dashboard at http://localhost:8001

asyncio.run(main())
```

## Configuration

### MonitoringConfig

```python
from src.monitoring import MonitoringConfig, NotificationConfig

config = MonitoringConfig(
    # Health checking
    health_check_interval=30.0,  # seconds
    
    # Performance monitoring
    metrics_collection_interval=5.0,  # seconds
    
    # Alert thresholds
    cpu_warning_threshold=75.0,      # %
    cpu_critical_threshold=90.0,     # %
    memory_warning_threshold=80.0,   # %
    memory_critical_threshold=95.0,  # %
    disk_warning_threshold=85.0,     # %
    disk_critical_threshold=95.0,    # %
    api_response_time_warning=1000.0,   # ms
    api_response_time_critical=5000.0,  # ms
    
    # Monitoring intervals
    alert_check_interval=10.0,       # seconds
    status_update_interval=60.0,     # seconds
    
    # Notification configuration
    notification_config=NotificationConfig(...)
)
```

### NotificationConfig

```python
from src.monitoring import NotificationConfig

notification_config = NotificationConfig(
    # Email configuration
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_use_tls=True,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",
    email_from="your-email@gmail.com",
    email_to=["admin@yourcompany.com", "ops@yourcompany.com"],
    
    # Webhook configuration
    webhook_urls=["https://your-webhook-url.com/alerts"],
    webhook_timeout=10.0,
    
    # File logging
    log_file="alerts.log",
    
    # Slack integration
    slack_webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    slack_channel="#trading-alerts",
    
    # Telegram integration
    telegram_bot_token="YOUR_BOT_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID"
)
```

## Usage Examples

### Custom Health Checks

```python
from src.monitoring import HealthChecker, HealthStatus

health_checker = HealthChecker()

async def check_custom_component(component):
    """Custom health check function."""
    try:
        # Your health check logic here
        is_healthy = await check_component_status()
        
        if is_healthy:
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Component is operating normally',
                'metrics': {'response_time': 150}
            }
        else:
            return {
                'status': HealthStatus.CRITICAL,
                'message': 'Component is not responding'
            }
    except Exception as e:
        return {
            'status': HealthStatus.CRITICAL,
            'message': f'Health check failed: {str(e)}'
        }

# Register custom health check
health_checker.register_health_check("my_component", check_custom_component)
```

### Performance Monitoring

```python
from src.monitoring import SystemMonitor

system_monitor = SystemMonitor()

# Record trade execution
system_monitor.record_trade_execution(
    symbol="BTCUSDT",
    side="BUY",
    quantity=0.001,
    price=45000.0,
    execution_time=250.0  # milliseconds
)

# Record API call
system_monitor.record_api_call(
    endpoint="get_account_info",
    response_time=150.0,  # milliseconds
    status_code=200
)
```

### Custom Alerts

```python
from src.monitoring import AlertSeverity, AlertType

# Create custom alert
alert_id = await system_monitor.create_custom_alert(
    title="Custom Trading Alert",
    message="Something important happened in your trading strategy",
    severity=AlertSeverity.WARNING,
    alert_type=AlertType.TRADING
)

# Acknowledge alert
await system_monitor.acknowledge_alert(alert_id, "trader_john")

# Resolve alert
await system_monitor.resolve_alert(alert_id)
```

### Integration with Trading Operations

```python
import time
from src.monitoring import SystemMonitor

class MonitoredTradingBot:
    def __init__(self):
        self.system_monitor = SystemMonitor()
    
    async def execute_trade(self, symbol, side, quantity, price):
        """Execute trade with monitoring."""
        start_time = time.time()
        
        try:
            # Execute the trade
            result = await self.binance_client.create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity
            )
            
            # Record successful execution
            execution_time = (time.time() - start_time) * 1000
            self.system_monitor.record_trade_execution(
                symbol, side, quantity, price, execution_time
            )
            
            return result
            
        except Exception as e:
            # Record failed execution and create alert
            execution_time = (time.time() - start_time) * 1000
            
            await self.system_monitor.create_custom_alert(
                title="Trade Execution Failed",
                message=f"Failed to execute {side} order for {symbol}: {str(e)}",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.TRADING
            )
            
            raise
```

## Dashboard Usage

### Accessing the Dashboard

1. Start the monitoring dashboard:
```python
dashboard = MonitoringDashboard(system_monitor, port=8001)
await dashboard.start()
```

2. Open your browser and navigate to: `http://localhost:8001`

### Dashboard Features

- **System Status**: Overall health indicator and uptime
- **Component Health**: Status of all monitored components
- **Performance Metrics**: Real-time system and trading metrics
- **Alert Summary**: Active alerts count by severity
- **Recent Alerts**: Latest alerts with timestamps
- **Performance Charts**: Visual representation of system metrics
- **Actions**: Force health checks and refresh data

### API Endpoints

The dashboard provides REST API endpoints:

- `GET /api/status` - System status
- `GET /api/health` - Health details
- `GET /api/performance` - Performance metrics
- `GET /api/alerts` - Active alerts
- `POST /api/alerts/{alert_id}/acknowledge` - Acknowledge alert
- `POST /api/alerts/{alert_id}/resolve` - Resolve alert
- `POST /api/health/check` - Force health check
- `GET /api/dashboard` - Complete dashboard data

## Alert Rules

### Default Alert Rules

The system comes with predefined alert rules:

1. **High CPU Usage**
   - Warning: >75%
   - Critical: >90%
   - Cooldown: 5 minutes

2. **High Memory Usage**
   - Warning: >80%
   - Critical: >95%
   - Cooldown: 5 minutes

3. **API Connection Failed**
   - Critical: API health check fails
   - Cooldown: 2 minutes

4. **Database Connection Failed**
   - Critical: Database health check fails
   - Cooldown: 2 minutes

5. **Trading Execution Slow**
   - Warning: >2000ms execution time
   - Cooldown: 10 minutes

6. **High API Error Rate**
   - Warning: >10 errors per minute
   - Cooldown: 5 minutes

### Custom Alert Rules

```python
from src.monitoring import AlertRule, AlertSeverity, AlertType, NotificationChannel

custom_rule = AlertRule(
    name="custom_trading_rule",
    condition="win_rate < 50",
    severity=AlertSeverity.WARNING,
    alert_type=AlertType.TRADING,
    description="Trading win rate is below 50%",
    cooldown_minutes=30,
    escalation_minutes=60,
    channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK]
)

alert_manager.register_rule(custom_rule)
```

## Notification Channels

### Email Notifications

Configure SMTP settings in `NotificationConfig`:

```python
notification_config = NotificationConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    smtp_use_tls=True,
    smtp_username="your-email@gmail.com",
    smtp_password="your-app-password",  # Use app password for Gmail
    email_from="trading-bot@yourcompany.com",
    email_to=["admin@yourcompany.com"]
)
```

### Slack Notifications

1. Create a Slack webhook URL in your Slack workspace
2. Configure in `NotificationConfig`:

```python
notification_config = NotificationConfig(
    slack_webhook_url="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
    slack_channel="#trading-alerts"
)
```

### Telegram Notifications

1. Create a Telegram bot and get the bot token
2. Get your chat ID
3. Configure in `NotificationConfig`:

```python
notification_config = NotificationConfig(
    telegram_bot_token="YOUR_BOT_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID"
)
```

### Webhook Notifications

Configure webhook URLs for external integrations:

```python
notification_config = NotificationConfig(
    webhook_urls=[
        "https://your-monitoring-system.com/webhooks/alerts",
        "https://your-pagerduty-integration.com/webhook"
    ]
)
```

## Best Practices

### 1. Health Check Configuration

- Set appropriate intervals based on component criticality
- Use shorter intervals for critical components (API, database)
- Use longer intervals for less critical components (system resources)

### 2. Alert Thresholds

- Set warning thresholds to catch issues early
- Set critical thresholds for immediate action
- Adjust thresholds based on your system's normal operating ranges

### 3. Alert Management

- Acknowledge alerts when investigating
- Resolve alerts when issues are fixed
- Use appropriate cooldown periods to avoid spam

### 4. Performance Monitoring

- Monitor key trading metrics (execution time, slippage)
- Track API performance and error rates
- Set up alerts for performance degradation

### 5. Dashboard Usage

- Use the dashboard for real-time monitoring
- Set up multiple notification channels for redundancy
- Regularly review alert history for patterns

## Troubleshooting

### Common Issues

1. **Dashboard not accessible**
   - Check if the port is available
   - Verify firewall settings
   - Check server logs for errors

2. **Email notifications not working**
   - Verify SMTP settings
   - Check email credentials
   - Test with a simple email client

3. **Health checks failing**
   - Check component availability
   - Verify network connectivity
   - Review health check timeouts

4. **High resource usage**
   - Adjust monitoring intervals
   - Reduce metric collection frequency
   - Check for memory leaks

### Debugging

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check system status:

```python
status = system_monitor.get_system_status()
print(f"Overall health: {status.overall_health}")
print(f"Active alerts: {status.active_alerts}")
```

## Advanced Configuration

### Custom Metrics

```python
from src.monitoring import Metric, MetricType, MetricCategory

# Define custom metric
custom_metric = Metric(
    name="custom_trading_metric",
    metric_type=MetricType.GAUGE,
    category=MetricCategory.TRADING,
    description="Custom trading performance metric",
    unit="percentage"
)

# Register metric
performance_monitor.metrics_collector.register_metric(custom_metric)

# Record metric value
performance_monitor.metrics_collector.record_metric(
    "custom_trading_metric",
    value=85.5,
    tags={"strategy": "bollinger_rsi"}
)
```

### Custom Alert Conditions

```python
# Custom alert condition function
def check_custom_condition(metrics):
    """Custom alert condition logic."""
    win_rate = metrics.get('win_rate', 0)
    total_trades = metrics.get('total_trades', 0)
    
    if total_trades > 10 and win_rate < 40:
        return True  # Trigger alert
    return False

# Use in monitoring logic
if check_custom_condition(current_metrics):
    await system_monitor.create_custom_alert(
        title="Low Win Rate Alert",
        message=f"Win rate dropped to {win_rate}% over {total_trades} trades",
        severity=AlertSeverity.WARNING
    )
```

## Integration Examples

See `examples/monitoring_integration_example.py` for a complete example of integrating the monitoring system with your trading bot.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the example code
3. Check system logs for error messages
4. Verify configuration settings

The monitoring system is designed to be robust and self-healing, but proper configuration is essential for optimal performance. 