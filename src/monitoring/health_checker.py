"""
Health checker for monitoring all system components.

This module provides comprehensive health checking for:
- API connections (Binance, other exchanges)
- Database connections (InfluxDB)
- Web UI components
- Trading engine components
- Network connectivity
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import psutil
import socket

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"
    MAINTENANCE = "maintenance"


class ComponentType(Enum):
    """Types of system components."""
    API = "api"
    DATABASE = "database"
    WEB_UI = "web_ui"
    TRADING_ENGINE = "trading_engine"
    NETWORK = "network"
    SYSTEM = "system"
    WEBSOCKET = "websocket"


@dataclass
class HealthMetrics:
    """Health metrics for a component."""
    response_time: float = 0.0
    success_rate: float = 100.0
    error_count: int = 0
    last_error: Optional[str] = None
    last_check: Optional[datetime] = None
    uptime: float = 0.0
    memory_usage: float = 0.0
    cpu_usage: float = 0.0
    custom_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentHealth:
    """Health information for a system component."""
    name: str
    component_type: ComponentType
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    metrics: HealthMetrics = field(default_factory=HealthMetrics)
    dependencies: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    check_interval: float = 30.0
    timeout: float = 10.0
    enabled: bool = True


class HealthChecker:
    """Comprehensive health checker for all system components."""
    
    def __init__(self, check_interval: float = 30.0):
        self.check_interval = check_interval
        self.components: Dict[str, ComponentHealth] = {}
        self.health_checks: Dict[str, Callable] = {}
        self.running = False
        self.check_task: Optional[asyncio.Task] = None
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Health check history for trend analysis
        self.health_history: Dict[str, List[Dict]] = {}
        self.max_history_size = 100
        
        # Register default health checks
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks for common components."""
        self.register_health_check("binance_api", self._check_binance_api)
        self.register_health_check("influxdb", self._check_influxdb)
        self.register_health_check("web_ui", self._check_web_ui)
        self.register_health_check("system_resources", self._check_system_resources)
        self.register_health_check("network_connectivity", self._check_network_connectivity)
        self.register_health_check("trading_engine", self._check_trading_engine)
    
    def register_component(self, component: ComponentHealth):
        """Register a component for health monitoring."""
        self.components[component.name] = component
        self.health_history[component.name] = []
        logger.info(f"Registered component for health monitoring: {component.name}")
    
    def register_health_check(self, component_name: str, check_function: Callable):
        """Register a health check function for a component."""
        self.health_checks[component_name] = check_function
        logger.info(f"Registered health check function for: {component_name}")
    
    async def start(self):
        """Start the health monitoring system."""
        if self.running:
            return
        
        self.running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        
        # Register default components
        await self._register_default_components()
        
        # Start health check loop
        self.check_task = asyncio.create_task(self._health_check_loop())
        
        logger.info("Health checker started")
    
    async def stop(self):
        """Stop the health monitoring system."""
        self.running = False
        
        if self.check_task:
            self.check_task.cancel()
            try:
                await self.check_task
            except asyncio.CancelledError:
                pass
        
        if self.session:
            await self.session.close()
        
        logger.info("Health checker stopped")
    
    async def _register_default_components(self):
        """Register default system components."""
        components = [
            ComponentHealth(
                name="binance_api",
                component_type=ComponentType.API,
                check_interval=30.0,
                timeout=10.0
            ),
            ComponentHealth(
                name="influxdb",
                component_type=ComponentType.DATABASE,
                check_interval=60.0,
                timeout=15.0
            ),
            ComponentHealth(
                name="web_ui",
                component_type=ComponentType.WEB_UI,
                check_interval=45.0,
                timeout=10.0
            ),
            ComponentHealth(
                name="system_resources",
                component_type=ComponentType.SYSTEM,
                check_interval=20.0,
                timeout=5.0
            ),
            ComponentHealth(
                name="network_connectivity",
                component_type=ComponentType.NETWORK,
                check_interval=60.0,
                timeout=10.0
            ),
            ComponentHealth(
                name="trading_engine",
                component_type=ComponentType.TRADING_ENGINE,
                check_interval=30.0,
                timeout=5.0
            )
        ]
        
        for component in components:
            self.register_component(component)
    
    async def _health_check_loop(self):
        """Main health check loop."""
        logger.info("Health check loop started")
        
        try:
            while self.running:
                await self._perform_health_checks()
                await asyncio.sleep(self.check_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in health check loop: {e}")
        finally:
            logger.info("Health check loop stopped")
    
    async def _perform_health_checks(self):
        """Perform health checks on all registered components."""
        current_time = datetime.now()
        
        # Determine which components need checking
        components_to_check = []
        for name, component in self.components.items():
            if not component.enabled:
                continue
            
            time_since_last_check = (current_time - component.last_updated).total_seconds()
            if time_since_last_check >= component.check_interval:
                components_to_check.append((name, component))
        
        if not components_to_check:
            return
        
        # Perform checks concurrently
        tasks = [
            self._check_component_health(name, component)
            for name, component in components_to_check
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                component_name = components_to_check[i][0]
                logger.error(f"Health check failed for {component_name}: {result}")
    
    async def _check_component_health(self, name: str, component: ComponentHealth):
        """Check health of a specific component."""
        start_time = time.time()
        
        try:
            # Get the health check function
            check_function = self.health_checks.get(name)
            if not check_function:
                component.status = HealthStatus.UNKNOWN
                component.message = "No health check function registered"
                return
            
            # Perform the health check with timeout
            result = await asyncio.wait_for(
                check_function(component),
                timeout=component.timeout
            )
            
            # Update component health based on result
            if isinstance(result, dict):
                component.status = result.get('status', HealthStatus.UNKNOWN)
                component.message = result.get('message', '')
                
                # Update metrics
                if 'metrics' in result:
                    for key, value in result['metrics'].items():
                        setattr(component.metrics, key, value)
            else:
                component.status = HealthStatus.HEALTHY if result else HealthStatus.CRITICAL
                component.message = "Health check completed"
            
            # Calculate response time
            response_time = time.time() - start_time
            component.metrics.response_time = response_time
            component.metrics.last_check = datetime.now()
            
            # Update success rate
            self._update_success_rate(component, True)
            
        except asyncio.TimeoutError:
            component.status = HealthStatus.CRITICAL
            component.message = f"Health check timed out after {component.timeout}s"
            component.metrics.error_count += 1
            component.metrics.last_error = "Timeout"
            self._update_success_rate(component, False)
            
        except Exception as e:
            component.status = HealthStatus.CRITICAL
            component.message = f"Health check failed: {str(e)}"
            component.metrics.error_count += 1
            component.metrics.last_error = str(e)
            self._update_success_rate(component, False)
        
        finally:
            component.last_updated = datetime.now()
            self._record_health_history(name, component)
    
    def _update_success_rate(self, component: ComponentHealth, success: bool):
        """Update success rate for a component."""
        # Simple moving average over last 100 checks
        history = self.health_history.get(component.name, [])
        if len(history) >= 100:
            history.pop(0)
        
        history.append({'success': success, 'timestamp': datetime.now()})
        
        if history:
            successful_checks = sum(1 for h in history if h['success'])
            component.metrics.success_rate = (successful_checks / len(history)) * 100
    
    def _record_health_history(self, name: str, component: ComponentHealth):
        """Record health check result in history."""
        if name not in self.health_history:
            self.health_history[name] = []
        
        history_entry = {
            'timestamp': datetime.now(),
            'status': component.status.value,
            'response_time': component.metrics.response_time,
            'message': component.message
        }
        
        self.health_history[name].append(history_entry)
        
        # Limit history size
        if len(self.health_history[name]) > self.max_history_size:
            self.health_history[name].pop(0)
    
    # Health check implementations
    async def _check_binance_api(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check Binance API health."""
        try:
            # Try to get server time from Binance
            url = "https://fapi.binance.com/fapi/v1/time"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    server_time = data.get('serverTime', 0)
                    
                    # Check if server time is reasonable (within 5 minutes of local time)
                    local_time = int(time.time() * 1000)
                    time_diff = abs(server_time - local_time)
                    
                    if time_diff > 300000:  # 5 minutes in milliseconds
                        return {
                            'status': HealthStatus.WARNING,
                            'message': f'Server time drift: {time_diff}ms',
                            'metrics': {'time_drift': time_diff}
                        }
                    
                    return {
                        'status': HealthStatus.HEALTHY,
                        'message': 'Binance API is responsive',
                        'metrics': {'server_time': server_time, 'time_drift': time_diff}
                    }
                else:
                    return {
                        'status': HealthStatus.CRITICAL,
                        'message': f'Binance API returned status {response.status}'
                    }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to connect to Binance API: {str(e)}'
            }
    
    async def _check_influxdb(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check InfluxDB health."""
        try:
            # Check if InfluxDB is running on default port
            url = "http://localhost:8086/ping"
            
            async with self.session.get(url) as response:
                if response.status == 204:
                    # Check database connectivity
                    db_url = "http://localhost:8086/query"
                    params = {"q": "SHOW DATABASES"}
                    
                    async with self.session.get(db_url, params=params) as db_response:
                        if db_response.status == 200:
                            return {
                                'status': HealthStatus.HEALTHY,
                                'message': 'InfluxDB is running and accessible'
                            }
                        else:
                            return {
                                'status': HealthStatus.WARNING,
                                'message': 'InfluxDB ping successful but query failed'
                            }
                else:
                    return {
                        'status': HealthStatus.CRITICAL,
                        'message': f'InfluxDB ping failed with status {response.status}'
                    }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to connect to InfluxDB: {str(e)}'
            }
    
    async def _check_web_ui(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check Web UI health."""
        try:
            # Check if web UI is accessible
            urls_to_check = [
                "http://localhost:3000",  # Frontend
                "http://localhost:8000",  # Backend API
            ]
            
            results = []
            for url in urls_to_check:
                try:
                    async with self.session.get(url) as response:
                        results.append({
                            'url': url,
                            'status': response.status,
                            'accessible': response.status < 400
                        })
                except Exception as e:
                    results.append({
                        'url': url,
                        'status': 0,
                        'accessible': False,
                        'error': str(e)
                    })
            
            accessible_count = sum(1 for r in results if r['accessible'])
            
            if accessible_count == len(urls_to_check):
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'All Web UI components are accessible',
                    'metrics': {'accessible_endpoints': accessible_count}
                }
            elif accessible_count > 0:
                return {
                    'status': HealthStatus.WARNING,
                    'message': f'Only {accessible_count}/{len(urls_to_check)} Web UI components accessible',
                    'metrics': {'accessible_endpoints': accessible_count}
                }
            else:
                return {
                    'status': HealthStatus.CRITICAL,
                    'message': 'No Web UI components are accessible',
                    'metrics': {'accessible_endpoints': 0}
                }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to check Web UI: {str(e)}'
            }
    
    async def _check_system_resources(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check system resource usage."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine status based on resource usage
            status = HealthStatus.HEALTHY
            messages = []
            
            if cpu_percent > 90:
                status = HealthStatus.CRITICAL
                messages.append(f"High CPU usage: {cpu_percent:.1f}%")
            elif cpu_percent > 75:
                status = HealthStatus.WARNING
                messages.append(f"Elevated CPU usage: {cpu_percent:.1f}%")
            
            if memory.percent > 90:
                status = HealthStatus.CRITICAL
                messages.append(f"High memory usage: {memory.percent:.1f}%")
            elif memory.percent > 75:
                status = HealthStatus.WARNING
                messages.append(f"Elevated memory usage: {memory.percent:.1f}%")
            
            if disk.percent > 95:
                status = HealthStatus.CRITICAL
                messages.append(f"High disk usage: {disk.percent:.1f}%")
            elif disk.percent > 85:
                status = HealthStatus.WARNING
                messages.append(f"Elevated disk usage: {disk.percent:.1f}%")
            
            message = "; ".join(messages) if messages else "System resources are healthy"
            
            return {
                'status': status,
                'message': message,
                'metrics': {
                    'cpu_usage': cpu_percent,
                    'memory_usage': memory.percent,
                    'disk_usage': disk.percent,
                    'memory_available': memory.available,
                    'disk_free': disk.free
                }
            }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to check system resources: {str(e)}'
            }
    
    async def _check_network_connectivity(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check network connectivity."""
        try:
            # Test connectivity to important endpoints
            endpoints = [
                ("8.8.8.8", 53),  # Google DNS
                ("fapi.binance.com", 443),  # Binance API
            ]
            
            connectivity_results = []
            for host, port in endpoints:
                try:
                    # Test socket connection
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(5)
                    result = sock.connect_ex((host, port))
                    sock.close()
                    
                    connectivity_results.append({
                        'host': host,
                        'port': port,
                        'connected': result == 0
                    })
                except Exception as e:
                    connectivity_results.append({
                        'host': host,
                        'port': port,
                        'connected': False,
                        'error': str(e)
                    })
            
            connected_count = sum(1 for r in connectivity_results if r['connected'])
            
            if connected_count == len(endpoints):
                return {
                    'status': HealthStatus.HEALTHY,
                    'message': 'Network connectivity is good',
                    'metrics': {'connected_endpoints': connected_count}
                }
            elif connected_count > 0:
                return {
                    'status': HealthStatus.WARNING,
                    'message': f'Partial network connectivity: {connected_count}/{len(endpoints)}',
                    'metrics': {'connected_endpoints': connected_count}
                }
            else:
                return {
                    'status': HealthStatus.CRITICAL,
                    'message': 'No network connectivity',
                    'metrics': {'connected_endpoints': 0}
                }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to check network connectivity: {str(e)}'
            }
    
    async def _check_trading_engine(self, component: ComponentHealth) -> Dict[str, Any]:
        """Check trading engine health."""
        try:
            # This is a placeholder - you would implement actual trading engine checks
            # For example: check if trading loops are running, positions are being managed, etc.
            
            # For now, we'll do a basic check
            return {
                'status': HealthStatus.HEALTHY,
                'message': 'Trading engine health check not implemented',
                'metrics': {}
            }
        
        except Exception as e:
            return {
                'status': HealthStatus.CRITICAL,
                'message': f'Failed to check trading engine: {str(e)}'
            }
    
    # Public API methods
    def get_component_health(self, name: str) -> Optional[ComponentHealth]:
        """Get health information for a specific component."""
        return self.components.get(name)
    
    def get_all_health(self) -> Dict[str, ComponentHealth]:
        """Get health information for all components."""
        return self.components.copy()
    
    def get_overall_health(self) -> HealthStatus:
        """Get overall system health status."""
        if not self.components:
            return HealthStatus.UNKNOWN
        
        statuses = [comp.status for comp in self.components.values() if comp.enabled]
        
        if not statuses:
            return HealthStatus.UNKNOWN
        
        if any(status == HealthStatus.CRITICAL for status in statuses):
            return HealthStatus.CRITICAL
        elif any(status == HealthStatus.WARNING for status in statuses):
            return HealthStatus.WARNING
        elif all(status == HealthStatus.HEALTHY for status in statuses):
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health."""
        overall_status = self.get_overall_health()
        
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = sum(
                1 for comp in self.components.values() 
                if comp.status == status and comp.enabled
            )
        
        critical_components = [
            name for name, comp in self.components.items()
            if comp.status == HealthStatus.CRITICAL and comp.enabled
        ]
        
        warning_components = [
            name for name, comp in self.components.items()
            if comp.status == HealthStatus.WARNING and comp.enabled
        ]
        
        return {
            'overall_status': overall_status.value,
            'status_counts': status_counts,
            'critical_components': critical_components,
            'warning_components': warning_components,
            'total_components': len([c for c in self.components.values() if c.enabled]),
            'last_updated': datetime.now().isoformat()
        }
    
    def get_health_history(self, component_name: str, limit: int = 50) -> List[Dict]:
        """Get health history for a component."""
        history = self.health_history.get(component_name, [])
        return history[-limit:] if limit else history
    
    async def force_check(self, component_name: str = None):
        """Force a health check for a specific component or all components."""
        if component_name:
            component = self.components.get(component_name)
            if component:
                await self._check_component_health(component_name, component)
        else:
            await self._perform_health_checks() 