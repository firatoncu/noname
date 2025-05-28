"""
Monitoring dashboard for web-based system monitoring.

This module provides:
- Web-based monitoring dashboard
- Real-time system status updates
- Interactive charts and graphs
- Alert management interface
- Health check controls
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from .system_monitor import SystemMonitor, MonitoringConfig
from .alert_manager import AlertSeverity, AlertType

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """Web-based monitoring dashboard."""
    
    def __init__(self, system_monitor: SystemMonitor, host: str = "localhost", port: int = 8001):
        self.system_monitor = system_monitor
        self.host = host
        self.port = port
        
        # FastAPI app
        self.app = FastAPI(title="Trading Bot Monitoring Dashboard")
        
        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []
        
        # Dashboard state
        self.running = False
        self.server = None
        self.update_task: Optional[asyncio.Task] = None
        
        # Setup routes
        self._setup_routes()
        
        # Register for system status updates
        self.system_monitor.register_status_callback(self._handle_status_update)
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def dashboard_home():
            """Serve the main dashboard page."""
            return self._get_dashboard_html()
        
        @self.app.get("/api/status")
        async def get_system_status():
            """Get current system status."""
            status = self.system_monitor.get_system_status()
            if not status:
                raise HTTPException(status_code=503, detail="Monitoring system not ready")
            
            return {
                "overall_health": status.overall_health.value,
                "component_health": {k: v.value for k, v in status.component_health.items()},
                "active_alerts": status.active_alerts,
                "critical_alerts": status.critical_alerts,
                "warning_alerts": status.warning_alerts,
                "system_uptime": status.system_uptime,
                "last_updated": status.last_updated.isoformat()
            }
        
        @self.app.get("/api/health")
        async def get_health_details():
            """Get detailed health information."""
            return self.system_monitor.get_health_status()
        
        @self.app.get("/api/performance")
        async def get_performance_metrics():
            """Get performance metrics."""
            interval = "60s"  # Default to 1 minute
            return self.system_monitor.get_performance_metrics(interval)
        
        @self.app.get("/api/alerts")
        async def get_alerts():
            """Get active alerts."""
            alerts = self.system_monitor.get_active_alerts()
            return [
                {
                    "id": alert.id,
                    "title": alert.title,
                    "message": alert.message,
                    "severity": alert.severity.value,
                    "type": alert.alert_type.value,
                    "status": alert.status.value,
                    "created_at": alert.created_at.isoformat(),
                    "updated_at": alert.updated_at.isoformat()
                }
                for alert in alerts
            ]
        
        @self.app.post("/api/alerts/{alert_id}/acknowledge")
        async def acknowledge_alert(alert_id: str):
            """Acknowledge an alert."""
            success = await self.system_monitor.acknowledge_alert(alert_id, "dashboard_user")
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "acknowledged"}
        
        @self.app.post("/api/alerts/{alert_id}/resolve")
        async def resolve_alert(alert_id: str):
            """Resolve an alert."""
            success = await self.system_monitor.resolve_alert(alert_id)
            if not success:
                raise HTTPException(status_code=404, detail="Alert not found")
            return {"status": "resolved"}
        
        @self.app.post("/api/health/check")
        async def force_health_check():
            """Force a health check on all components."""
            await self.system_monitor.force_health_check()
            return {"status": "health_check_initiated"}
        
        @self.app.post("/api/health/check/{component}")
        async def force_component_health_check(component: str):
            """Force a health check on a specific component."""
            await self.system_monitor.force_health_check(component)
            return {"status": f"health_check_initiated_for_{component}"}
        
        @self.app.get("/api/dashboard")
        async def get_dashboard_data():
            """Get comprehensive dashboard data."""
            return self.system_monitor.get_monitoring_dashboard_data()
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)
            
            try:
                # Send initial data
                dashboard_data = self.system_monitor.get_monitoring_dashboard_data()
                await websocket.send_text(json.dumps({
                    "type": "initial_data",
                    "data": dashboard_data
                }))
                
                # Keep connection alive
                while True:
                    await websocket.receive_text()
            
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if websocket in self.websocket_connections:
                    self.websocket_connections.remove(websocket)
    
    def _get_dashboard_html(self) -> str:
        """Generate the dashboard HTML page."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Bot Monitoring Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f5f5f5;
            color: #333;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        
        .header h1 {
            margin: 0;
            font-size: 1.8rem;
        }
        
        .status-bar {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-top: 0.5rem;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 500;
        }
        
        .status-healthy { background-color: #10b981; }
        .status-warning { background-color: #f59e0b; }
        .status-critical { background-color: #ef4444; }
        .status-unknown { background-color: #6b7280; }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 2rem;
        }
        
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }
        
        .card {
            background: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border: 1px solid #e5e7eb;
        }
        
        .card h3 {
            margin-bottom: 1rem;
            color: #374151;
            font-size: 1.1rem;
        }
        
        .metric {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem 0;
            border-bottom: 1px solid #f3f4f6;
        }
        
        .metric:last-child {
            border-bottom: none;
        }
        
        .metric-label {
            font-weight: 500;
            color: #6b7280;
        }
        
        .metric-value {
            font-weight: 600;
            color: #111827;
        }
        
        .alert-item {
            padding: 1rem;
            margin-bottom: 0.5rem;
            border-radius: 6px;
            border-left: 4px solid;
        }
        
        .alert-critical {
            background-color: #fef2f2;
            border-left-color: #ef4444;
        }
        
        .alert-warning {
            background-color: #fffbeb;
            border-left-color: #f59e0b;
        }
        
        .alert-info {
            background-color: #eff6ff;
            border-left-color: #3b82f6;
        }
        
        .alert-header {
            display: flex;
            justify-content: between;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .alert-title {
            font-weight: 600;
            color: #111827;
        }
        
        .alert-time {
            font-size: 0.8rem;
            color: #6b7280;
        }
        
        .alert-message {
            color: #374151;
            font-size: 0.9rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9rem;
            font-weight: 500;
            margin: 0.25rem;
        }
        
        .btn-primary {
            background-color: #3b82f6;
            color: white;
        }
        
        .btn-secondary {
            background-color: #6b7280;
            color: white;
        }
        
        .btn:hover {
            opacity: 0.9;
        }
        
        .chart-container {
            position: relative;
            height: 300px;
            margin-top: 1rem;
        }
        
        .component-health {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
        }
        
        .component-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem;
            border-radius: 6px;
            background-color: #f9fafb;
        }
        
        .health-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }
        
        .health-healthy { background-color: #10b981; }
        .health-warning { background-color: #f59e0b; }
        .health-critical { background-color: #ef4444; }
        .health-unknown { background-color: #6b7280; }
        
        .loading {
            text-align: center;
            padding: 2rem;
            color: #6b7280;
        }
        
        .error {
            background-color: #fef2f2;
            color: #dc2626;
            padding: 1rem;
            border-radius: 6px;
            margin: 1rem 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Trading Bot Monitoring Dashboard</h1>
        <div class="status-bar">
            <div id="overall-status" class="status-indicator">
                <span id="status-dot">●</span>
                <span id="status-text">Loading...</span>
            </div>
            <div id="uptime">Uptime: --</div>
            <div id="last-updated">Last updated: --</div>
        </div>
    </div>
    
    <div class="container">
        <div id="loading" class="loading">
            Loading monitoring data...
        </div>
        
        <div id="error" class="error" style="display: none;">
            Failed to load monitoring data. Please refresh the page.
        </div>
        
        <div id="dashboard-content" style="display: none;">
            <div class="grid">
                <div class="card">
                    <h3>System Health</h3>
                    <div id="component-health" class="component-health">
                        <!-- Component health items will be populated here -->
                    </div>
                </div>
                
                <div class="card">
                    <h3>Performance Metrics</h3>
                    <div id="performance-metrics">
                        <!-- Performance metrics will be populated here -->
                    </div>
                </div>
                
                <div class="card">
                    <h3>Alert Summary</h3>
                    <div class="metric">
                        <span class="metric-label">Active Alerts</span>
                        <span id="active-alerts" class="metric-value">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Critical</span>
                        <span id="critical-alerts" class="metric-value">0</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">Warning</span>
                        <span id="warning-alerts" class="metric-value">0</span>
                    </div>
                </div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>Recent Alerts</h3>
                    <div id="recent-alerts">
                        <!-- Recent alerts will be populated here -->
                    </div>
                </div>
                
                <div class="card">
                    <h3>System Performance</h3>
                    <div class="chart-container">
                        <canvas id="performance-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>Actions</h3>
                <button class="btn btn-primary" onclick="forceHealthCheck()">Force Health Check</button>
                <button class="btn btn-secondary" onclick="refreshData()">Refresh Data</button>
            </div>
        </div>
    </div>
    
    <script>
        let ws = null;
        let performanceChart = null;
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            initializeWebSocket();
            loadInitialData();
        });
        
        function initializeWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            ws = new WebSocket(wsUrl);
            
            ws.onopen = function() {
                console.log('WebSocket connected');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                if (message.type === 'initial_data' || message.type === 'status_update') {
                    updateDashboard(message.data);
                }
            };
            
            ws.onclose = function() {
                console.log('WebSocket disconnected');
                setTimeout(initializeWebSocket, 5000); // Reconnect after 5 seconds
            };
            
            ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        }
        
        async function loadInitialData() {
            try {
                const response = await fetch('/api/dashboard');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to load initial data:', error);
                showError();
            }
        }
        
        function updateDashboard(data) {
            hideLoading();
            hideError();
            showDashboard();
            
            // Update overall status
            updateOverallStatus(data.system_status);
            
            // Update component health
            updateComponentHealth(data.component_health);
            
            // Update performance metrics
            updatePerformanceMetrics(data.performance);
            
            // Update alerts
            updateAlerts(data.alerts);
            
            // Update performance chart
            updatePerformanceChart(data.performance);
        }
        
        function updateOverallStatus(status) {
            const statusElement = document.getElementById('overall-status');
            const statusDot = document.getElementById('status-dot');
            const statusText = document.getElementById('status-text');
            const uptimeElement = document.getElementById('uptime');
            const lastUpdatedElement = document.getElementById('last-updated');
            
            // Update status
            statusElement.className = `status-indicator status-${status.overall_health}`;
            statusText.textContent = status.overall_health.charAt(0).toUpperCase() + status.overall_health.slice(1);
            
            // Update uptime
            const hours = Math.floor(status.uptime / 3600);
            const minutes = Math.floor((status.uptime % 3600) / 60);
            uptimeElement.textContent = `Uptime: ${hours}h ${minutes}m`;
            
            // Update last updated
            const lastUpdated = new Date(status.last_updated);
            lastUpdatedElement.textContent = `Last updated: ${lastUpdated.toLocaleTimeString()}`;
        }
        
        function updateComponentHealth(componentHealth) {
            const container = document.getElementById('component-health');
            container.innerHTML = '';
            
            for (const [component, health] of Object.entries(componentHealth)) {
                const item = document.createElement('div');
                item.className = 'component-item';
                item.innerHTML = `
                    <div class="health-dot health-${health}"></div>
                    <span>${component.replace('_', ' ').toUpperCase()}</span>
                `;
                container.appendChild(item);
            }
        }
        
        function updatePerformanceMetrics(performance) {
            const container = document.getElementById('performance-metrics');
            container.innerHTML = '';
            
            if (performance && performance.system_metrics) {
                const metrics = [
                    { label: 'CPU Usage', value: `${performance.system_metrics.cpu_usage?.toFixed(1) || 0}%` },
                    { label: 'Memory Usage', value: `${performance.system_metrics.memory_usage?.toFixed(1) || 0}%` },
                    { label: 'Disk Usage', value: `${performance.system_metrics.disk_usage?.toFixed(1) || 0}%` }
                ];
                
                metrics.forEach(metric => {
                    const metricElement = document.createElement('div');
                    metricElement.className = 'metric';
                    metricElement.innerHTML = `
                        <span class="metric-label">${metric.label}</span>
                        <span class="metric-value">${metric.value}</span>
                    `;
                    container.appendChild(metricElement);
                });
            }
        }
        
        function updateAlerts(alerts) {
            document.getElementById('active-alerts').textContent = alerts.active || 0;
            document.getElementById('critical-alerts').textContent = alerts.critical || 0;
            document.getElementById('warning-alerts').textContent = alerts.warning || 0;
            
            const recentAlertsContainer = document.getElementById('recent-alerts');
            recentAlertsContainer.innerHTML = '';
            
            if (alerts.recent && alerts.recent.length > 0) {
                alerts.recent.forEach(alert => {
                    const alertElement = document.createElement('div');
                    alertElement.className = `alert-item alert-${alert.severity}`;
                    alertElement.innerHTML = `
                        <div class="alert-header">
                            <span class="alert-title">${alert.title}</span>
                            <span class="alert-time">${new Date(alert.created_at).toLocaleTimeString()}</span>
                        </div>
                        <div class="alert-message">${alert.message || ''}</div>
                    `;
                    recentAlertsContainer.appendChild(alertElement);
                });
            } else {
                recentAlertsContainer.innerHTML = '<p style="color: #6b7280; text-align: center;">No recent alerts</p>';
            }
        }
        
        function updatePerformanceChart(performance) {
            const ctx = document.getElementById('performance-chart').getContext('2d');
            
            if (performanceChart) {
                performanceChart.destroy();
            }
            
            const systemMetrics = performance?.system_metrics || {};
            
            performanceChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['CPU Usage', 'Memory Usage', 'Disk Usage'],
                    datasets: [{
                        data: [
                            systemMetrics.cpu_usage || 0,
                            systemMetrics.memory_usage || 0,
                            systemMetrics.disk_usage || 0
                        ],
                        backgroundColor: [
                            '#3b82f6',
                            '#10b981',
                            '#f59e0b'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        async function forceHealthCheck() {
            try {
                await fetch('/api/health/check', { method: 'POST' });
                alert('Health check initiated');
            } catch (error) {
                alert('Failed to initiate health check');
            }
        }
        
        function refreshData() {
            loadInitialData();
        }
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
        }
        
        function showError() {
            document.getElementById('error').style.display = 'block';
        }
        
        function hideError() {
            document.getElementById('error').style.display = 'none';
        }
        
        function showDashboard() {
            document.getElementById('dashboard-content').style.display = 'block';
        }
    </script>
</body>
</html>
        """
    
    async def start(self):
        """Start the monitoring dashboard server."""
        if self.running:
            return
        
        self.running = True
        
        # Start real-time update task
        self.update_task = asyncio.create_task(self._update_loop())
        
        # Start the server
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        self.server = uvicorn.Server(config)
        
        logger.info(f"Starting monitoring dashboard on http://{self.host}:{self.port}")
        await self.server.serve()
    
    async def stop(self):
        """Stop the monitoring dashboard server."""
        self.running = False
        
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        if self.server:
            self.server.should_exit = True
        
        logger.info("Monitoring dashboard stopped")
    
    async def _update_loop(self):
        """Send periodic updates to WebSocket clients."""
        try:
            while self.running:
                if self.websocket_connections:
                    dashboard_data = self.system_monitor.get_monitoring_dashboard_data()
                    message = json.dumps({
                        "type": "status_update",
                        "data": dashboard_data
                    })
                    
                    # Send to all connected clients
                    disconnected = []
                    for websocket in self.websocket_connections:
                        try:
                            await websocket.send_text(message)
                        except Exception:
                            disconnected.append(websocket)
                    
                    # Remove disconnected clients
                    for websocket in disconnected:
                        self.websocket_connections.remove(websocket)
                
                await asyncio.sleep(5)  # Update every 5 seconds
        
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in dashboard update loop: {e}")
    
    async def _handle_status_update(self, status):
        """Handle system status updates."""
        if self.websocket_connections:
            dashboard_data = self.system_monitor.get_monitoring_dashboard_data()
            message = json.dumps({
                "type": "status_update",
                "data": dashboard_data
            })
            
            # Send to all connected clients
            disconnected = []
            for websocket in self.websocket_connections:
                try:
                    await websocket.send_text(message)
                except Exception:
                    disconnected.append(websocket)
            
            # Remove disconnected clients
            for websocket in disconnected:
                self.websocket_connections.remove(websocket) 