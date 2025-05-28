"""
Unified system monitoring that integrates health checking, performance monitoring, and alerting.

This module provides:
- Centralized monitoring coordination
- Integration between health checker, performance monitor, and alert manager
- Automated alert generation based on health and performance data
- Monitoring dashboard data aggregation
- System status reporting
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json

from .health_checker import HealthChecker, HealthStatus, ComponentHealth
from .performance_monitor import PerformanceMonitor, MetricsCollector
from .alert_manager import AlertManager, AlertSeverity, AlertType, NotificationConfig

logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfig:
    """Configuration for the monitoring system."""
    # Health checking
    health_check_interval: float = 30.0
    
    # Performance monitoring
    metrics_collection_interval: float = 5.0
    
    # Alert thresholds
    cpu_warning_threshold: float = 75.0
    cpu_critical_threshold: float = 90.0
    memory_warning_threshold: float = 80.0
    memory_critical_threshold: float = 95.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0
    api_response_time_warning: float = 1000.0  # ms
    api_response_time_critical: float = 5000.0  # ms
    
    # Monitoring intervals
    alert_check_interval: float = 10.0
    status_update_interval: float = 60.0
    
    # Notification configuration
    notification_config: NotificationConfig = field(default_factory=NotificationConfig)


@dataclass
class SystemStatus:
    """Overall system status."""
    overall_health: HealthStatus
    component_health: Dict[str, HealthStatus]
    active_alerts: int
    critical_alerts: int
    warning_alerts: int
    system_uptime: float
    last_updated: datetime
    performance_summary: Dict[str, Any]
    health_summary: Dict[str, Any]
    alert_summary: Dict[str, Any]


class SystemMonitor:
    """Unified system monitoring coordinator."""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        
        # Initialize components
        self.health_checker = HealthChecker(self.config.health_check_interval)
        self.performance_monitor = PerformanceMonitor(self.config.metrics_collection_interval)
        self.alert_manager = AlertManager(self.config.notification_config)
        
        # Monitoring state
        self.running = False
        self.start_time: Optional[datetime] = None
        
        # Background tasks
        self.monitoring_tasks: List[asyncio.Task] = []
        
        # Status callbacks
        self.status_callbacks: List[Callable] = []
        
        # Current system status
        self.current_status: Optional[SystemStatus] = None
        
        # Setup alert integration
        self._setup_alert_integration()
    
    def _setup_alert_integration(self):
        """Setup integration between monitoring components and alerting."""
        # Register performance callback for alerting
        self.performance_monitor.register_performance_callback(
            self._handle_performance_event
        )
    
    async def start(self):
        """Start the unified monitoring system."""
        if self.running:
            return
        
        self.running = True
        self.start_time = datetime.now()
        
        logger.info("Starting unified monitoring system...")
        
        # Start all components
        await self.health_checker.start()
        await self.performance_monitor.start()
        await self.alert_manager.start()
        
        # Start monitoring tasks
        self.monitoring_tasks = [
            asyncio.create_task(self._alert_monitoring_loop()),
            asyncio.create_task(self._status_update_loop()),
            asyncio.create_task(self._health_alert_loop())
        ]
        
        logger.info("Unified monitoring system started")
    
    async def stop(self):
        """Stop the unified monitoring system."""
        self.running = False
        
        logger.info("Stopping unified monitoring system...")
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Stop all components
        await self.health_checker.stop()
        await self.performance_monitor.stop()
        await self.alert_manager.stop()
        
        logger.info("Unified monitoring system stopped")
    
    async def _alert_monitoring_loop(self):
        """Monitor performance metrics and generate alerts."""
        logger.info("Alert monitoring loop started")
        
        try:
            while self.running:
                await self._check_performance_alerts()
                await asyncio.sleep(self.config.alert_check_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in alert monitoring loop: {e}")
        finally:
            logger.info("Alert monitoring loop stopped")
    
    async def _health_alert_loop(self):
        """Monitor health status and generate alerts."""
        logger.info("Health alert monitoring started")
        
        try:
            while self.running:
                await self._check_health_alerts()
                await asyncio.sleep(self.config.alert_check_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in health alert loop: {e}")
        finally:
            logger.info("Health alert monitoring stopped")
    
    async def _status_update_loop(self):
        """Update system status periodically."""
        logger.info("Status update loop started")
        
        try:
            while self.running:
                await self._update_system_status()
                await asyncio.sleep(self.config.status_update_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in status update loop: {e}")
        finally:
            logger.info("Status update loop stopped")
    
    async def _check_performance_alerts(self):
        """Check performance metrics and generate alerts if needed."""
        try:
            # Get latest performance metrics
            metrics_1m = self.performance_monitor.metrics_collector.get_aggregated_metrics("60s")
            
            # Check CPU usage
            cpu_usage = metrics_1m.get('cpu_usage', {}).get('latest', 0)
            if cpu_usage >= self.config.cpu_critical_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_cpu_usage",
                    title="Critical CPU Usage",
                    message=f"CPU usage is critically high: {cpu_usage:.1f}%",
                    severity=AlertSeverity.CRITICAL,
                    alert_type=AlertType.SYSTEM,
                    metadata={'cpu_usage': cpu_usage}
                )
            elif cpu_usage >= self.config.cpu_warning_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_cpu_usage",
                    title="High CPU Usage",
                    message=f"CPU usage is elevated: {cpu_usage:.1f}%",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.SYSTEM,
                    metadata={'cpu_usage': cpu_usage}
                )
            
            # Check memory usage
            memory_usage = metrics_1m.get('memory_usage', {}).get('latest', 0)
            if memory_usage >= self.config.memory_critical_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_memory_usage",
                    title="Critical Memory Usage",
                    message=f"Memory usage is critically high: {memory_usage:.1f}%",
                    severity=AlertSeverity.CRITICAL,
                    alert_type=AlertType.SYSTEM,
                    metadata={'memory_usage': memory_usage}
                )
            elif memory_usage >= self.config.memory_warning_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_memory_usage",
                    title="High Memory Usage",
                    message=f"Memory usage is elevated: {memory_usage:.1f}%",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.SYSTEM,
                    metadata={'memory_usage': memory_usage}
                )
            
            # Check disk usage
            disk_usage = metrics_1m.get('disk_usage', {}).get('latest', 0)
            if disk_usage >= self.config.disk_critical_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_disk_usage",
                    title="Critical Disk Usage",
                    message=f"Disk usage is critically high: {disk_usage:.1f}%",
                    severity=AlertSeverity.CRITICAL,
                    alert_type=AlertType.SYSTEM,
                    metadata={'disk_usage': disk_usage}
                )
            elif disk_usage >= self.config.disk_warning_threshold:
                await self.alert_manager.create_alert(
                    rule_name="high_disk_usage",
                    title="High Disk Usage",
                    message=f"Disk usage is elevated: {disk_usage:.1f}%",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.SYSTEM,
                    metadata={'disk_usage': disk_usage}
                )
            
            # Check API response time
            api_response_time = metrics_1m.get('api_response_time', {}).get('avg', 0)
            if api_response_time >= self.config.api_response_time_critical:
                await self.alert_manager.create_alert(
                    rule_name="high_api_response_time",
                    title="Critical API Response Time",
                    message=f"API response time is critically high: {api_response_time:.0f}ms",
                    severity=AlertSeverity.CRITICAL,
                    alert_type=AlertType.API,
                    metadata={'api_response_time': api_response_time}
                )
            elif api_response_time >= self.config.api_response_time_warning:
                await self.alert_manager.create_alert(
                    rule_name="high_api_response_time",
                    title="High API Response Time",
                    message=f"API response time is elevated: {api_response_time:.0f}ms",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.API,
                    metadata={'api_response_time': api_response_time}
                )
            
            # Check API error rate
            api_error_rate = metrics_1m.get('api_errors', {}).get('rate', 0)
            if api_error_rate > 10:  # More than 10 errors per minute
                await self.alert_manager.create_alert(
                    rule_name="high_api_error_rate",
                    title="High API Error Rate",
                    message=f"API error rate is high: {api_error_rate:.1f} errors/min",
                    severity=AlertSeverity.WARNING,
                    alert_type=AlertType.API,
                    metadata={'api_error_rate': api_error_rate}
                )
        
        except Exception as e:
            logger.error(f"Error checking performance alerts: {e}")
    
    async def _check_health_alerts(self):
        """Check health status and generate alerts if needed."""
        try:
            all_health = self.health_checker.get_all_health()
            
            for component_name, component_health in all_health.items():
                if not component_health.enabled:
                    continue
                
                # Generate alerts for critical health issues
                if component_health.status == HealthStatus.CRITICAL:
                    alert_type = self._map_component_to_alert_type(component_health.component_type)
                    
                    await self.alert_manager.create_alert(
                        rule_name=f"{component_name}_health_critical",
                        title=f"{component_name.title()} Health Critical",
                        message=f"{component_name} health is critical: {component_health.message}",
                        severity=AlertSeverity.CRITICAL,
                        alert_type=alert_type,
                        metadata={
                            'component': component_name,
                            'health_status': component_health.status.value,
                            'response_time': component_health.metrics.response_time,
                            'error_count': component_health.metrics.error_count
                        }
                    )
                
                elif component_health.status == HealthStatus.WARNING:
                    alert_type = self._map_component_to_alert_type(component_health.component_type)
                    
                    await self.alert_manager.create_alert(
                        rule_name=f"{component_name}_health_warning",
                        title=f"{component_name.title()} Health Warning",
                        message=f"{component_name} health is degraded: {component_health.message}",
                        severity=AlertSeverity.WARNING,
                        alert_type=alert_type,
                        metadata={
                            'component': component_name,
                            'health_status': component_health.status.value,
                            'response_time': component_health.metrics.response_time,
                            'success_rate': component_health.metrics.success_rate
                        }
                    )
        
        except Exception as e:
            logger.error(f"Error checking health alerts: {e}")
    
    def _map_component_to_alert_type(self, component_type) -> AlertType:
        """Map component type to alert type."""
        mapping = {
            'api': AlertType.API,
            'database': AlertType.DATABASE,
            'web_ui': AlertType.SYSTEM,
            'trading_engine': AlertType.TRADING,
            'network': AlertType.NETWORK,
            'system': AlertType.SYSTEM,
            'websocket': AlertType.API
        }
        return mapping.get(component_type.value, AlertType.SYSTEM)
    
    async def _update_system_status(self):
        """Update the current system status."""
        try:
            # Get health summary
            health_summary = self.health_checker.get_health_summary()
            overall_health = self.health_checker.get_overall_health()
            
            # Get performance summary
            performance_summary = self.performance_monitor.get_performance_summary()
            
            # Get alert summary
            alert_summary = self.alert_manager.get_alert_summary()
            
            # Calculate uptime
            uptime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
            
            # Get component health status
            all_health = self.health_checker.get_all_health()
            component_health = {
                name: health.status for name, health in all_health.items()
            }
            
            # Create system status
            self.current_status = SystemStatus(
                overall_health=overall_health,
                component_health=component_health,
                active_alerts=alert_summary['total_active'],
                critical_alerts=alert_summary['severity_counts'].get('critical', 0),
                warning_alerts=alert_summary['severity_counts'].get('warning', 0),
                system_uptime=uptime,
                last_updated=datetime.now(),
                performance_summary=performance_summary,
                health_summary=health_summary,
                alert_summary=alert_summary
            )
            
            # Notify status callbacks
            for callback in self.status_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self.current_status)
                    else:
                        callback(self.current_status)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")
        
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def _handle_performance_event(self, event: Dict[str, Any]):
        """Handle performance events for alerting."""
        try:
            event_type = event.get('type')
            
            if event_type == 'trade_execution':
                execution_time = event.get('execution_time', 0)
                
                # Alert on slow execution
                if execution_time > 2000:  # 2 seconds
                    asyncio.create_task(
                        self.alert_manager.create_alert(
                            rule_name="trading_execution_slow",
                            title="Slow Trade Execution",
                            message=f"Trade execution took {execution_time:.0f}ms for {event.get('symbol')}",
                            severity=AlertSeverity.WARNING,
                            alert_type=AlertType.TRADING,
                            metadata=event
                        )
                    )
        
        except Exception as e:
            logger.error(f"Error handling performance event: {e}")
    
    # Public API methods
    def register_status_callback(self, callback: Callable):
        """Register a callback for status updates."""
        self.status_callbacks.append(callback)
    
    def get_system_status(self) -> Optional[SystemStatus]:
        """Get the current system status."""
        return self.current_status
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status for all components."""
        return self.health_checker.get_health_summary()
    
    def get_performance_metrics(self, interval: str = "60s") -> Dict[str, Any]:
        """Get performance metrics for a specific interval."""
        return self.performance_monitor.metrics_collector.get_aggregated_metrics(interval)
    
    def get_active_alerts(self) -> List:
        """Get all active alerts."""
        return self.alert_manager.get_active_alerts()
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "user") -> bool:
        """Acknowledge an alert."""
        return await self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        return await self.alert_manager.resolve_alert(alert_id)
    
    async def force_health_check(self, component_name: str = None):
        """Force a health check for a component or all components."""
        await self.health_checker.force_check(component_name)
    
    def record_trade_execution(self, symbol: str, side: str, quantity: float,
                             price: float, execution_time: float, slippage: float = 0.0):
        """Record a trade execution for monitoring."""
        self.performance_monitor.record_trade_execution(
            symbol, side, quantity, price, execution_time, slippage
        )
    
    def record_api_call(self, endpoint: str, response_time: float, 
                       status_code: int, error: str = None):
        """Record an API call for monitoring."""
        self.performance_monitor.record_api_call(
            endpoint, response_time, status_code, error
        )
    
    async def create_custom_alert(self, title: str, message: str, 
                                severity: AlertSeverity = AlertSeverity.INFO,
                                alert_type: AlertType = AlertType.CUSTOM,
                                metadata: Dict[str, Any] = None) -> str:
        """Create a custom alert."""
        return await self.alert_manager.create_alert(
            rule_name="custom_alert",
            title=title,
            message=message,
            severity=severity,
            alert_type=alert_type,
            metadata=metadata
        )
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for monitoring dashboard."""
        if not self.current_status:
            return {}
        
        return {
            'system_status': {
                'overall_health': self.current_status.overall_health.value,
                'uptime': self.current_status.system_uptime,
                'last_updated': self.current_status.last_updated.isoformat()
            },
            'component_health': {
                name: status.value 
                for name, status in self.current_status.component_health.items()
            },
            'alerts': {
                'active': self.current_status.active_alerts,
                'critical': self.current_status.critical_alerts,
                'warning': self.current_status.warning_alerts,
                'recent': [
                    {
                        'id': alert.id,
                        'title': alert.title,
                        'severity': alert.severity.value,
                        'type': alert.alert_type.value,
                        'created_at': alert.created_at.isoformat()
                    }
                    for alert in self.get_active_alerts()[-10:]  # Last 10 alerts
                ]
            },
            'performance': self.current_status.performance_summary,
            'health_details': self.current_status.health_summary
        } 