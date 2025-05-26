"""
Alert management system for monitoring notifications.

This module provides:
- Multi-channel alerting (email, webhook, console, file)
- Alert severity levels and escalation
- Alert deduplication and rate limiting
- Alert history and acknowledgment
- Integration with health checker and performance monitor
"""

import asyncio
import smtplib
import aiohttp
import json
import logging
from typing import Dict, List, Optional, Any, Callable, Union, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict, deque
import hashlib
import os

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertType(Enum):
    """Types of alerts."""
    HEALTH_CHECK = "health_check"
    PERFORMANCE = "performance"
    TRADING = "trading"
    SYSTEM = "system"
    NETWORK = "network"
    API = "api"
    DATABASE = "database"
    CUSTOM = "custom"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    CONSOLE = "console"
    FILE = "file"
    SLACK = "slack"
    TELEGRAM = "telegram"


@dataclass
class AlertRule:
    """Alert rule definition."""
    name: str
    condition: str
    severity: AlertSeverity
    alert_type: AlertType
    description: str = ""
    enabled: bool = True
    cooldown_minutes: int = 5
    escalation_minutes: int = 30
    channels: List[NotificationChannel] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """An alert instance."""
    id: str
    rule_name: str
    severity: AlertSeverity
    alert_type: AlertType
    title: str
    message: str
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)
    escalated: bool = False
    notification_count: int = 0


@dataclass
class NotificationConfig:
    """Configuration for notification channels."""
    # Email configuration
    smtp_server: str = "localhost"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    email_from: str = ""
    email_to: List[str] = field(default_factory=list)
    
    # Webhook configuration
    webhook_urls: List[str] = field(default_factory=list)
    webhook_timeout: float = 10.0
    
    # File configuration
    log_file: str = "alerts.log"
    
    # Slack configuration
    slack_webhook_url: str = ""
    slack_channel: str = "#alerts"
    
    # Telegram configuration
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""


class AlertManager:
    """Comprehensive alert management system."""
    
    def __init__(self, config: NotificationConfig = None):
        self.config = config or NotificationConfig()
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.running = False
        
        # Alert processing
        self.alert_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        
        # Rate limiting and deduplication
        self.alert_fingerprints: Dict[str, datetime] = {}
        self.notification_counts: Dict[str, int] = defaultdict(int)
        self.last_notifications: Dict[str, datetime] = {}
        
        # Escalation tracking
        self.escalation_tasks: Dict[str, asyncio.Task] = {}
        
        # HTTP session for webhooks
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Register default alert rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default alert rules."""
        default_rules = [
            AlertRule(
                name="high_cpu_usage",
                condition="cpu_usage > 90",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.SYSTEM,
                description="CPU usage is critically high",
                cooldown_minutes=5,
                channels=[NotificationChannel.EMAIL, NotificationChannel.CONSOLE]
            ),
            AlertRule(
                name="high_memory_usage",
                condition="memory_usage > 95",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.SYSTEM,
                description="Memory usage is critically high",
                cooldown_minutes=5,
                channels=[NotificationChannel.EMAIL, NotificationChannel.CONSOLE]
            ),
            AlertRule(
                name="api_connection_failed",
                condition="api_health == 'critical'",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.API,
                description="API connection has failed",
                cooldown_minutes=2,
                channels=[NotificationChannel.EMAIL, NotificationChannel.WEBHOOK, NotificationChannel.CONSOLE]
            ),
            AlertRule(
                name="database_connection_failed",
                condition="database_health == 'critical'",
                severity=AlertSeverity.CRITICAL,
                alert_type=AlertType.DATABASE,
                description="Database connection has failed",
                cooldown_minutes=2,
                channels=[NotificationChannel.EMAIL, NotificationChannel.CONSOLE]
            ),
            AlertRule(
                name="trading_execution_slow",
                condition="avg_execution_time > 2000",
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.TRADING,
                description="Trading execution is slow",
                cooldown_minutes=10,
                channels=[NotificationChannel.CONSOLE, NotificationChannel.FILE]
            ),
            AlertRule(
                name="high_api_error_rate",
                condition="api_error_rate > 10",
                severity=AlertSeverity.WARNING,
                alert_type=AlertType.API,
                description="High API error rate detected",
                cooldown_minutes=5,
                channels=[NotificationChannel.EMAIL, NotificationChannel.CONSOLE]
            )
        ]
        
        for rule in default_rules:
            self.register_rule(rule)
    
    def register_rule(self, rule: AlertRule):
        """Register an alert rule."""
        self.rules[rule.name] = rule
        logger.info(f"Registered alert rule: {rule.name}")
    
    async def start(self):
        """Start the alert manager."""
        if self.running:
            return
        
        self.running = True
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.webhook_timeout)
        )
        
        # Start alert processing task
        self.processing_task = asyncio.create_task(self._process_alerts())
        
        logger.info("Alert manager started")
    
    async def stop(self):
        """Stop the alert manager."""
        self.running = False
        
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
        
        # Cancel all escalation tasks
        for task in self.escalation_tasks.values():
            task.cancel()
        
        if self.session:
            await self.session.close()
        
        logger.info("Alert manager stopped")
    
    async def _process_alerts(self):
        """Process alerts from the queue."""
        logger.info("Alert processing started")
        
        try:
            while self.running:
                try:
                    alert = await asyncio.wait_for(self.alert_queue.get(), timeout=1.0)
                    await self._handle_alert(alert)
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error processing alert: {e}")
        
        except asyncio.CancelledError:
            pass
        finally:
            logger.info("Alert processing stopped")
    
    async def _handle_alert(self, alert: Alert):
        """Handle a single alert."""
        try:
            # Check if alert should be deduplicated
            if self._should_deduplicate(alert):
                logger.debug(f"Alert deduplicated: {alert.id}")
                return
            
            # Add to active alerts
            self.active_alerts[alert.id] = alert
            self.alert_history.append(alert)
            
            # Send notifications
            await self._send_notifications(alert)
            
            # Schedule escalation if needed
            self._schedule_escalation(alert)
            
            logger.info(f"Alert handled: {alert.title} ({alert.severity.value})")
        
        except Exception as e:
            logger.error(f"Error handling alert {alert.id}: {e}")
    
    def _should_deduplicate(self, alert: Alert) -> bool:
        """Check if alert should be deduplicated."""
        # Create fingerprint for deduplication
        fingerprint_data = f"{alert.rule_name}:{alert.title}:{alert.message}"
        fingerprint = hashlib.md5(fingerprint_data.encode()).hexdigest()
        
        # Check if we've seen this alert recently
        if fingerprint in self.alert_fingerprints:
            rule = self.rules.get(alert.rule_name)
            if rule:
                cooldown = timedelta(minutes=rule.cooldown_minutes)
                if datetime.now() - self.alert_fingerprints[fingerprint] < cooldown:
                    return True
        
        # Update fingerprint timestamp
        self.alert_fingerprints[fingerprint] = datetime.now()
        return False
    
    async def _send_notifications(self, alert: Alert):
        """Send notifications for an alert."""
        rule = self.rules.get(alert.rule_name)
        if not rule or not rule.enabled:
            return
        
        # Send to configured channels
        notification_tasks = []
        
        for channel in rule.channels:
            if channel == NotificationChannel.EMAIL:
                task = asyncio.create_task(self._send_email_notification(alert))
                notification_tasks.append(task)
            elif channel == NotificationChannel.WEBHOOK:
                task = asyncio.create_task(self._send_webhook_notification(alert))
                notification_tasks.append(task)
            elif channel == NotificationChannel.CONSOLE:
                task = asyncio.create_task(self._send_console_notification(alert))
                notification_tasks.append(task)
            elif channel == NotificationChannel.FILE:
                task = asyncio.create_task(self._send_file_notification(alert))
                notification_tasks.append(task)
            elif channel == NotificationChannel.SLACK:
                task = asyncio.create_task(self._send_slack_notification(alert))
                notification_tasks.append(task)
            elif channel == NotificationChannel.TELEGRAM:
                task = asyncio.create_task(self._send_telegram_notification(alert))
                notification_tasks.append(task)
        
        if notification_tasks:
            await asyncio.gather(*notification_tasks, return_exceptions=True)
            alert.notification_count += 1
    
    async def _send_email_notification(self, alert: Alert):
        """Send email notification."""
        try:
            if not self.config.email_to or not self.config.email_from:
                return
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.config.email_from
            msg['To'] = ', '.join(self.config.email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Email body
            body = f"""
Alert Details:
- Severity: {alert.severity.value.upper()}
- Type: {alert.alert_type.value}
- Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
- Message: {alert.message}

Alert ID: {alert.id}
Rule: {alert.rule_name}

This is an automated alert from the trading bot monitoring system.
            """.strip()
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.config.smtp_server, self.config.smtp_port) as server:
                if self.config.smtp_use_tls:
                    server.starttls()
                if self.config.smtp_username and self.config.smtp_password:
                    server.login(self.config.smtp_username, self.config.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")
    
    async def _send_webhook_notification(self, alert: Alert):
        """Send webhook notification."""
        try:
            if not self.config.webhook_urls:
                return
            
            # Prepare webhook payload
            payload = {
                'alert_id': alert.id,
                'rule_name': alert.rule_name,
                'severity': alert.severity.value,
                'alert_type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'status': alert.status.value,
                'created_at': alert.created_at.isoformat(),
                'metadata': alert.metadata,
                'tags': alert.tags
            }
            
            # Send to all webhook URLs
            for url in self.config.webhook_urls:
                try:
                    async with self.session.post(
                        url,
                        json=payload,
                        headers={'Content-Type': 'application/json'}
                    ) as response:
                        if response.status < 400:
                            logger.info(f"Webhook notification sent to {url} for alert {alert.id}")
                        else:
                            logger.error(f"Webhook notification failed: {response.status}")
                except Exception as e:
                    logger.error(f"Failed to send webhook to {url}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
    
    async def _send_console_notification(self, alert: Alert):
        """Send console notification."""
        try:
            severity_colors = {
                AlertSeverity.INFO: '\033[94m',      # Blue
                AlertSeverity.WARNING: '\033[93m',   # Yellow
                AlertSeverity.CRITICAL: '\033[91m',  # Red
                AlertSeverity.EMERGENCY: '\033[95m'  # Magenta
            }
            
            color = severity_colors.get(alert.severity, '')
            reset_color = '\033[0m'
            
            print(f"\n{color}🚨 ALERT [{alert.severity.value.upper()}]{reset_color}")
            print(f"Title: {alert.title}")
            print(f"Message: {alert.message}")
            print(f"Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Type: {alert.alert_type.value}")
            print(f"Rule: {alert.rule_name}")
            print(f"ID: {alert.id}")
            print("-" * 50)
            
            logger.info(f"Console notification sent for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Failed to send console notification: {e}")
    
    async def _send_file_notification(self, alert: Alert):
        """Send file notification."""
        try:
            log_entry = {
                'timestamp': alert.created_at.isoformat(),
                'alert_id': alert.id,
                'rule_name': alert.rule_name,
                'severity': alert.severity.value,
                'alert_type': alert.alert_type.value,
                'title': alert.title,
                'message': alert.message,
                'status': alert.status.value,
                'metadata': alert.metadata,
                'tags': alert.tags
            }
            
            with open(self.config.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.info(f"File notification written for alert {alert.id}")
        
        except Exception as e:
            logger.error(f"Failed to write file notification: {e}")
    
    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification."""
        try:
            if not self.config.slack_webhook_url:
                return
            
            # Slack color mapping
            color_map = {
                AlertSeverity.INFO: 'good',
                AlertSeverity.WARNING: 'warning',
                AlertSeverity.CRITICAL: 'danger',
                AlertSeverity.EMERGENCY: 'danger'
            }
            
            payload = {
                'channel': self.config.slack_channel,
                'username': 'Trading Bot Monitor',
                'icon_emoji': ':warning:',
                'attachments': [{
                    'color': color_map.get(alert.severity, 'warning'),
                    'title': f"[{alert.severity.value.upper()}] {alert.title}",
                    'text': alert.message,
                    'fields': [
                        {'title': 'Type', 'value': alert.alert_type.value, 'short': True},
                        {'title': 'Rule', 'value': alert.rule_name, 'short': True},
                        {'title': 'Time', 'value': alert.created_at.strftime('%Y-%m-%d %H:%M:%S'), 'short': True},
                        {'title': 'Alert ID', 'value': alert.id, 'short': True}
                    ],
                    'footer': 'Trading Bot Monitoring System',
                    'ts': int(alert.created_at.timestamp())
                }]
            }
            
            async with self.session.post(
                self.config.slack_webhook_url,
                json=payload
            ) as response:
                if response.status < 400:
                    logger.info(f"Slack notification sent for alert {alert.id}")
                else:
                    logger.error(f"Slack notification failed: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Slack notification: {e}")
    
    async def _send_telegram_notification(self, alert: Alert):
        """Send Telegram notification."""
        try:
            if not self.config.telegram_bot_token or not self.config.telegram_chat_id:
                return
            
            # Format message for Telegram
            message = f"""
🚨 *ALERT [{alert.severity.value.upper()}]*

*{alert.title}*

{alert.message}

📊 Type: {alert.alert_type.value}
⏰ Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
🔧 Rule: {alert.rule_name}
🆔 ID: `{alert.id}`
            """.strip()
            
            url = f"https://api.telegram.org/bot{self.config.telegram_bot_token}/sendMessage"
            payload = {
                'chat_id': self.config.telegram_chat_id,
                'text': message,
                'parse_mode': 'Markdown'
            }
            
            async with self.session.post(url, json=payload) as response:
                if response.status < 400:
                    logger.info(f"Telegram notification sent for alert {alert.id}")
                else:
                    logger.error(f"Telegram notification failed: {response.status}")
        
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")
    
    def _schedule_escalation(self, alert: Alert):
        """Schedule alert escalation."""
        rule = self.rules.get(alert.rule_name)
        if not rule or rule.escalation_minutes <= 0:
            return
        
        async def escalate():
            await asyncio.sleep(rule.escalation_minutes * 60)
            
            # Check if alert is still active and not acknowledged
            if (alert.id in self.active_alerts and 
                alert.status == AlertStatus.ACTIVE and 
                not alert.escalated):
                
                alert.escalated = True
                alert.severity = AlertSeverity.EMERGENCY
                alert.updated_at = datetime.now()
                
                # Send escalated notification
                await self._send_notifications(alert)
                
                logger.warning(f"Alert escalated: {alert.id}")
        
        task = asyncio.create_task(escalate())
        self.escalation_tasks[alert.id] = task
    
    # Public API methods
    async def create_alert(self, rule_name: str, title: str, message: str,
                          severity: AlertSeverity = None, alert_type: AlertType = None,
                          metadata: Dict[str, Any] = None, tags: Dict[str, str] = None) -> str:
        """Create a new alert."""
        rule = self.rules.get(rule_name)
        if not rule:
            logger.error(f"Alert rule not found: {rule_name}")
            return None
        
        # Generate alert ID
        alert_id = hashlib.md5(
            f"{rule_name}:{title}:{datetime.now().isoformat()}".encode()
        ).hexdigest()[:12]
        
        alert = Alert(
            id=alert_id,
            rule_name=rule_name,
            severity=severity or rule.severity,
            alert_type=alert_type or rule.alert_type,
            title=title,
            message=message,
            metadata=metadata or {},
            tags=tags or {}
        )
        
        # Queue alert for processing
        await self.alert_queue.put(alert)
        
        return alert_id
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "system") -> bool:
        """Acknowledge an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by
        alert.updated_at = datetime.now()
        
        # Cancel escalation task
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]
        
        logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
        return True
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        alert = self.active_alerts.get(alert_id)
        if not alert:
            return False
        
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        alert.updated_at = datetime.now()
        
        # Remove from active alerts
        del self.active_alerts[alert_id]
        
        # Cancel escalation task
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]
        
        logger.info(f"Alert resolved: {alert_id}")
        return True
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history."""
        history = list(self.alert_history)
        return history[-limit:] if limit else history
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary."""
        active_alerts = list(self.active_alerts.values())
        
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.value] = sum(
                1 for alert in active_alerts if alert.severity == severity
            )
        
        type_counts = {}
        for alert_type in AlertType:
            type_counts[alert_type.value] = sum(
                1 for alert in active_alerts if alert.alert_type == alert_type
            )
        
        return {
            'total_active': len(active_alerts),
            'severity_counts': severity_counts,
            'type_counts': type_counts,
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for rule in self.rules.values() if rule.enabled),
            'last_updated': datetime.now().isoformat()
        } 