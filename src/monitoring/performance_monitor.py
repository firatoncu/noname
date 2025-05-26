"""
Performance monitoring system for trading operations and system metrics.

This module provides:
- Trading performance metrics (P&L, win rate, execution times)
- System performance monitoring (CPU, memory, network)
- Real-time metrics collection and aggregation
- Performance analytics and reporting
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import json
import psutil
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricCategory(Enum):
    """Categories of metrics."""
    TRADING = "trading"
    SYSTEM = "system"
    NETWORK = "network"
    API = "api"
    DATABASE = "database"
    CUSTOM = "custom"


@dataclass
class MetricValue:
    """A single metric value with metadata."""
    value: Union[int, float]
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Metric:
    """A metric definition and its values."""
    name: str
    metric_type: MetricType
    category: MetricCategory
    description: str = ""
    unit: str = ""
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    aggregated_values: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class TradingMetrics:
    """Trading-specific performance metrics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    avg_trade_duration: float = 0.0
    avg_execution_time: float = 0.0
    order_fill_rate: float = 100.0
    slippage: float = 0.0


@dataclass
class SystemMetrics:
    """System performance metrics."""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_io: Dict[str, float] = field(default_factory=dict)
    disk_io: Dict[str, float] = field(default_factory=dict)
    process_count: int = 0
    thread_count: int = 0
    uptime: float = 0.0
    load_average: List[float] = field(default_factory=list)


class MetricsCollector:
    """Collects and aggregates metrics from various sources."""
    
    def __init__(self, collection_interval: float = 5.0):
        self.collection_interval = collection_interval
        self.metrics: Dict[str, Metric] = {}
        self.collectors: Dict[str, Callable] = {}
        self.running = False
        self.collection_task: Optional[asyncio.Task] = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Metric aggregation settings
        self.aggregation_intervals = [60, 300, 900, 3600]  # 1m, 5m, 15m, 1h
        self.aggregation_tasks: List[asyncio.Task] = []
        
        # Register default collectors
        self._register_default_collectors()
    
    def _register_default_collectors(self):
        """Register default metric collectors."""
        self.register_collector("system_metrics", self._collect_system_metrics)
        self.register_collector("trading_metrics", self._collect_trading_metrics)
        self.register_collector("api_metrics", self._collect_api_metrics)
    
    def register_metric(self, metric: Metric):
        """Register a metric for collection."""
        self.metrics[metric.name] = metric
        logger.info(f"Registered metric: {metric.name}")
    
    def register_collector(self, name: str, collector_func: Callable):
        """Register a metric collector function."""
        self.collectors[name] = collector_func
        logger.info(f"Registered metric collector: {name}")
    
    async def start(self):
        """Start metrics collection."""
        if self.running:
            return
        
        self.running = True
        
        # Register default metrics
        self._register_default_metrics()
        
        # Start collection loop
        self.collection_task = asyncio.create_task(self._collection_loop())
        
        # Start aggregation tasks
        for interval in self.aggregation_intervals:
            task = asyncio.create_task(self._aggregation_loop(interval))
            self.aggregation_tasks.append(task)
        
        logger.info("Metrics collector started")
    
    async def stop(self):
        """Stop metrics collection."""
        self.running = False
        
        if self.collection_task:
            self.collection_task.cancel()
            try:
                await self.collection_task
            except asyncio.CancelledError:
                pass
        
        for task in self.aggregation_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.executor.shutdown(wait=True)
        logger.info("Metrics collector stopped")
    
    def _register_default_metrics(self):
        """Register default metrics."""
        default_metrics = [
            # System metrics
            Metric("cpu_usage", MetricType.GAUGE, MetricCategory.SYSTEM, "CPU usage percentage", "%"),
            Metric("memory_usage", MetricType.GAUGE, MetricCategory.SYSTEM, "Memory usage percentage", "%"),
            Metric("disk_usage", MetricType.GAUGE, MetricCategory.SYSTEM, "Disk usage percentage", "%"),
            Metric("network_bytes_sent", MetricType.COUNTER, MetricCategory.NETWORK, "Network bytes sent", "bytes"),
            Metric("network_bytes_recv", MetricType.COUNTER, MetricCategory.NETWORK, "Network bytes received", "bytes"),
            
            # Trading metrics
            Metric("trade_count", MetricType.COUNTER, MetricCategory.TRADING, "Total number of trades", "count"),
            Metric("pnl", MetricType.GAUGE, MetricCategory.TRADING, "Profit and Loss", "USD"),
            Metric("win_rate", MetricType.GAUGE, MetricCategory.TRADING, "Win rate percentage", "%"),
            Metric("execution_time", MetricType.HISTOGRAM, MetricCategory.TRADING, "Order execution time", "ms"),
            Metric("slippage", MetricType.HISTOGRAM, MetricCategory.TRADING, "Order slippage", "bps"),
            
            # API metrics
            Metric("api_requests", MetricType.COUNTER, MetricCategory.API, "API requests count", "count"),
            Metric("api_response_time", MetricType.HISTOGRAM, MetricCategory.API, "API response time", "ms"),
            Metric("api_errors", MetricType.COUNTER, MetricCategory.API, "API errors count", "count"),
            
            # Database metrics
            Metric("db_queries", MetricType.COUNTER, MetricCategory.DATABASE, "Database queries count", "count"),
            Metric("db_response_time", MetricType.HISTOGRAM, MetricCategory.DATABASE, "Database response time", "ms"),
        ]
        
        for metric in default_metrics:
            self.register_metric(metric)
    
    async def _collection_loop(self):
        """Main metrics collection loop."""
        logger.info("Metrics collection loop started")
        
        try:
            while self.running:
                await self._collect_all_metrics()
                await asyncio.sleep(self.collection_interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in metrics collection loop: {e}")
        finally:
            logger.info("Metrics collection loop stopped")
    
    async def _collect_all_metrics(self):
        """Collect metrics from all registered collectors."""
        collection_tasks = []
        
        for name, collector in self.collectors.items():
            task = asyncio.create_task(self._run_collector(name, collector))
            collection_tasks.append(task)
        
        if collection_tasks:
            await asyncio.gather(*collection_tasks, return_exceptions=True)
    
    async def _run_collector(self, name: str, collector: Callable):
        """Run a single metric collector."""
        try:
            # Run collector in thread pool if it's not async
            if asyncio.iscoroutinefunction(collector):
                await collector()
            else:
                await asyncio.get_event_loop().run_in_executor(
                    self.executor, collector
                )
        except Exception as e:
            logger.error(f"Error in collector {name}: {e}")
    
    async def _aggregation_loop(self, interval: int):
        """Aggregation loop for a specific interval."""
        try:
            while self.running:
                await self._aggregate_metrics(interval)
                await asyncio.sleep(interval)
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in aggregation loop ({interval}s): {e}")
    
    async def _aggregate_metrics(self, interval: int):
        """Aggregate metrics for a specific time interval."""
        current_time = datetime.now()
        cutoff_time = current_time - timedelta(seconds=interval)
        
        for metric_name, metric in self.metrics.items():
            try:
                # Filter values within the interval
                interval_values = [
                    v for v in metric.values
                    if v.timestamp >= cutoff_time
                ]
                
                if not interval_values:
                    continue
                
                # Calculate aggregations based on metric type
                aggregation_key = f"{interval}s"
                
                if metric.metric_type == MetricType.GAUGE:
                    # For gauges, use latest value and calculate avg, min, max
                    values = [v.value for v in interval_values]
                    metric.aggregated_values[aggregation_key] = {
                        'latest': values[-1] if values else 0,
                        'avg': sum(values) / len(values) if values else 0,
                        'min': min(values) if values else 0,
                        'max': max(values) if values else 0,
                        'count': len(values)
                    }
                
                elif metric.metric_type == MetricType.COUNTER:
                    # For counters, calculate rate and total
                    values = [v.value for v in interval_values]
                    total = sum(values) if values else 0
                    rate = total / interval if interval > 0 else 0
                    
                    metric.aggregated_values[aggregation_key] = {
                        'total': total,
                        'rate': rate,
                        'count': len(values)
                    }
                
                elif metric.metric_type == MetricType.HISTOGRAM:
                    # For histograms, calculate percentiles
                    values = sorted([v.value for v in interval_values])
                    if values:
                        metric.aggregated_values[aggregation_key] = {
                            'count': len(values),
                            'avg': sum(values) / len(values),
                            'min': values[0],
                            'max': values[-1],
                            'p50': self._percentile(values, 50),
                            'p90': self._percentile(values, 90),
                            'p95': self._percentile(values, 95),
                            'p99': self._percentile(values, 99)
                        }
                
                elif metric.metric_type == MetricType.TIMER:
                    # Similar to histogram but with time-specific aggregations
                    values = [v.value for v in interval_values]
                    if values:
                        metric.aggregated_values[aggregation_key] = {
                            'count': len(values),
                            'total_time': sum(values),
                            'avg_time': sum(values) / len(values),
                            'min_time': min(values),
                            'max_time': max(values)
                        }
            
            except Exception as e:
                logger.error(f"Error aggregating metric {metric_name}: {e}")
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of a list of values."""
        if not values:
            return 0.0
        
        k = (len(values) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f + 1 < len(values):
            return values[f] * (1 - c) + values[f + 1] * c
        else:
            return values[f]
    
    # Default metric collectors
    def _collect_system_metrics(self):
        """Collect system performance metrics."""
        try:
            current_time = datetime.now()
            
            # CPU usage
            cpu_percent = psutil.cpu_percent()
            self.record_metric("cpu_usage", cpu_percent, current_time)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.record_metric("memory_usage", memory.percent, current_time)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.record_metric("disk_usage", disk.percent, current_time)
            
            # Network I/O
            net_io = psutil.net_io_counters()
            self.record_metric("network_bytes_sent", net_io.bytes_sent, current_time)
            self.record_metric("network_bytes_recv", net_io.bytes_recv, current_time)
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def _collect_trading_metrics(self):
        """Collect trading performance metrics."""
        try:
            # This would be implemented to collect actual trading metrics
            # For now, it's a placeholder
            current_time = datetime.now()
            
            # Example metrics (would be replaced with actual data)
            self.record_metric("trade_count", 0, current_time)
            self.record_metric("pnl", 0.0, current_time)
            self.record_metric("win_rate", 0.0, current_time)
            
        except Exception as e:
            logger.error(f"Error collecting trading metrics: {e}")
    
    def _collect_api_metrics(self):
        """Collect API performance metrics."""
        try:
            # This would be implemented to collect actual API metrics
            # For now, it's a placeholder
            current_time = datetime.now()
            
            # Example metrics (would be replaced with actual data)
            self.record_metric("api_requests", 0, current_time)
            self.record_metric("api_errors", 0, current_time)
            
        except Exception as e:
            logger.error(f"Error collecting API metrics: {e}")
    
    # Public API methods
    def record_metric(self, name: str, value: Union[int, float], 
                     timestamp: datetime = None, tags: Dict[str, str] = None,
                     metadata: Dict[str, Any] = None):
        """Record a metric value."""
        if name not in self.metrics:
            logger.warning(f"Metric {name} not registered")
            return
        
        metric_value = MetricValue(
            value=value,
            timestamp=timestamp or datetime.now(),
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.metrics[name].values.append(metric_value)
        self.metrics[name].last_updated = datetime.now()
    
    def get_metric(self, name: str) -> Optional[Metric]:
        """Get a metric by name."""
        return self.metrics.get(name)
    
    def get_all_metrics(self) -> Dict[str, Metric]:
        """Get all metrics."""
        return self.metrics.copy()
    
    def get_metric_values(self, name: str, limit: int = 100) -> List[MetricValue]:
        """Get recent values for a metric."""
        metric = self.metrics.get(name)
        if not metric:
            return []
        
        values = list(metric.values)
        return values[-limit:] if limit else values
    
    def get_aggregated_metrics(self, interval: str = "60s") -> Dict[str, Any]:
        """Get aggregated metrics for a specific interval."""
        result = {}
        
        for name, metric in self.metrics.items():
            if interval in metric.aggregated_values:
                result[name] = metric.aggregated_values[interval]
        
        return result


class PerformanceMonitor:
    """Main performance monitoring system."""
    
    def __init__(self, collection_interval: float = 5.0):
        self.metrics_collector = MetricsCollector(collection_interval)
        self.trading_metrics = TradingMetrics()
        self.system_metrics = SystemMetrics()
        self.running = False
        
        # Performance thresholds for alerting
        self.thresholds = {
            'cpu_usage': {'warning': 75, 'critical': 90},
            'memory_usage': {'warning': 80, 'critical': 95},
            'disk_usage': {'warning': 85, 'critical': 95},
            'api_response_time': {'warning': 1000, 'critical': 5000},  # ms
            'execution_time': {'warning': 500, 'critical': 2000},  # ms
        }
        
        # Performance callbacks
        self.performance_callbacks: List[Callable] = []
    
    async def start(self):
        """Start performance monitoring."""
        if self.running:
            return
        
        self.running = True
        await self.metrics_collector.start()
        
        logger.info("Performance monitor started")
    
    async def stop(self):
        """Stop performance monitoring."""
        self.running = False
        await self.metrics_collector.stop()
        
        logger.info("Performance monitor stopped")
    
    def register_performance_callback(self, callback: Callable):
        """Register a callback for performance events."""
        self.performance_callbacks.append(callback)
    
    def record_trade_execution(self, symbol: str, side: str, quantity: float,
                             price: float, execution_time: float, slippage: float = 0.0):
        """Record a trade execution for performance tracking."""
        current_time = datetime.now()
        
        # Record execution time
        self.metrics_collector.record_metric(
            "execution_time", execution_time, current_time,
            tags={'symbol': symbol, 'side': side}
        )
        
        # Record slippage
        if slippage != 0.0:
            self.metrics_collector.record_metric(
                "slippage", slippage, current_time,
                tags={'symbol': symbol, 'side': side}
            )
        
        # Update trading metrics
        self.trading_metrics.total_trades += 1
        
        # Trigger performance callbacks
        for callback in self.performance_callbacks:
            try:
                callback({
                    'type': 'trade_execution',
                    'symbol': symbol,
                    'side': side,
                    'quantity': quantity,
                    'price': price,
                    'execution_time': execution_time,
                    'slippage': slippage,
                    'timestamp': current_time
                })
            except Exception as e:
                logger.error(f"Error in performance callback: {e}")
    
    def record_api_call(self, endpoint: str, response_time: float, 
                       status_code: int, error: str = None):
        """Record an API call for performance tracking."""
        current_time = datetime.now()
        
        # Record API metrics
        self.metrics_collector.record_metric(
            "api_requests", 1, current_time,
            tags={'endpoint': endpoint, 'status': str(status_code)}
        )
        
        self.metrics_collector.record_metric(
            "api_response_time", response_time, current_time,
            tags={'endpoint': endpoint}
        )
        
        if error or status_code >= 400:
            self.metrics_collector.record_metric(
                "api_errors", 1, current_time,
                tags={'endpoint': endpoint, 'error': error or 'unknown'}
            )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a comprehensive performance summary."""
        # Get latest aggregated metrics
        metrics_1m = self.metrics_collector.get_aggregated_metrics("60s")
        metrics_5m = self.metrics_collector.get_aggregated_metrics("300s")
        
        return {
            'trading_metrics': {
                'total_trades': self.trading_metrics.total_trades,
                'win_rate': self.trading_metrics.win_rate,
                'total_pnl': self.trading_metrics.total_pnl,
                'avg_execution_time': metrics_1m.get('execution_time', {}).get('avg', 0),
                'avg_slippage': metrics_1m.get('slippage', {}).get('avg', 0),
            },
            'system_metrics': {
                'cpu_usage': metrics_1m.get('cpu_usage', {}).get('latest', 0),
                'memory_usage': metrics_1m.get('memory_usage', {}).get('latest', 0),
                'disk_usage': metrics_1m.get('disk_usage', {}).get('latest', 0),
            },
            'api_metrics': {
                'requests_per_minute': metrics_1m.get('api_requests', {}).get('rate', 0),
                'avg_response_time': metrics_1m.get('api_response_time', {}).get('avg', 0),
                'error_rate': metrics_1m.get('api_errors', {}).get('rate', 0),
            },
            'intervals': {
                '1m': metrics_1m,
                '5m': metrics_5m
            }
        }
    
    def check_performance_thresholds(self) -> List[Dict[str, Any]]:
        """Check if any performance metrics exceed thresholds."""
        alerts = []
        latest_metrics = self.metrics_collector.get_aggregated_metrics("60s")
        
        for metric_name, thresholds in self.thresholds.items():
            metric_data = latest_metrics.get(metric_name, {})
            current_value = metric_data.get('latest') or metric_data.get('avg', 0)
            
            if current_value >= thresholds['critical']:
                alerts.append({
                    'metric': metric_name,
                    'level': 'critical',
                    'value': current_value,
                    'threshold': thresholds['critical'],
                    'message': f"{metric_name} is critically high: {current_value}"
                })
            elif current_value >= thresholds['warning']:
                alerts.append({
                    'metric': metric_name,
                    'level': 'warning',
                    'value': current_value,
                    'threshold': thresholds['warning'],
                    'message': f"{metric_name} is elevated: {current_value}"
                })
        
        return alerts 