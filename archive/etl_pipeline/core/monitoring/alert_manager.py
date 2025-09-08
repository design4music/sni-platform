"""
Alert Management System for Strategic Narrative Intelligence ETL Pipeline

This module provides comprehensive alerting capabilities with multiple
notification channels, alert routing, and intelligent alert suppression.
"""

import json
import smtplib
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import aiohttp
import structlog

from ..config import AlertingConfig
from ..exceptions import AlertingError

logger = structlog.get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlertRule:
    """Alert rule definition"""

    name: str
    condition: str
    severity: AlertSeverity
    description: str
    enabled: bool = True
    cooldown_minutes: int = 30
    channels: List[str] = field(default_factory=lambda: ["email"])
    template: Optional[str] = None
    escalation_rules: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class Alert:
    """Individual alert instance"""

    id: str
    rule_name: str
    severity: AlertSeverity
    title: str
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: AlertStatus = AlertStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    notification_attempts: int = 0
    last_notification_at: Optional[datetime] = None


class AlertManager:
    """
    Comprehensive alert management system with intelligent routing,
    suppression, escalation, and multiple notification channels.
    """

    def __init__(self, config: AlertingConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__)

        # Alert storage and tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)
        self.alert_counts: Dict[str, int] = defaultdict(int)
        self.suppressed_alerts: Set[str] = set()

        # Rate limiting
        self.alert_timestamps: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Alert rules
        self.alert_rules = self._initialize_alert_rules()

        # Notification templates
        self.templates = self._initialize_templates()

        # HTTP session for webhook notifications
        self.http_session: Optional[aiohttp.ClientSession] = None

        logger.info(
            "Alert manager initialized",
            rules_count=len(self.alert_rules),
            channels_configured=self._get_configured_channels(),
        )

    def _initialize_alert_rules(self) -> Dict[str, AlertRule]:
        """Initialize predefined alert rules"""
        rules = {
            "pipeline_failure": AlertRule(
                name="pipeline_failure",
                condition='pipeline_status == "failed"',
                severity=AlertSeverity.CRITICAL,
                description="ETL pipeline execution failed",
                cooldown_minutes=5,
                channels=["slack", "email"],
            ),
            "pipeline_slow": AlertRule(
                name="pipeline_slow",
                condition="pipeline_duration > processing_window * 0.9",
                severity=AlertSeverity.WARNING,
                description="ETL pipeline taking longer than expected",
                cooldown_minutes=30,
                channels=["slack"],
            ),
            "feed_failures": AlertRule(
                name="feed_failures",
                condition="failed_feeds_count >= feed_failure_threshold",
                severity=AlertSeverity.WARNING,
                description="Multiple feed ingestion failures detected",
                cooldown_minutes=15,
                channels=["email"],
            ),
            "processing_errors": AlertRule(
                name="processing_errors",
                condition="error_rate > error_rate_threshold",
                severity=AlertSeverity.WARNING,
                description="High error rate in content processing",
                cooldown_minutes=20,
                channels=["slack", "email"],
            ),
            "no_recent_articles": AlertRule(
                name="no_recent_articles",
                condition="articles_last_6h == 0",
                severity=AlertSeverity.WARNING,
                description="No articles ingested in the last 6 hours",
                cooldown_minutes=60,
                channels=["email"],
            ),
            "database_connection": AlertRule(
                name="database_connection",
                condition='database_status != "healthy"',
                severity=AlertSeverity.CRITICAL,
                description="Database connection issues detected",
                cooldown_minutes=5,
                channels=["slack", "email"],
            ),
            "redis_connection": AlertRule(
                name="redis_connection",
                condition='redis_status != "healthy"',
                severity=AlertSeverity.CRITICAL,
                description="Redis connection issues detected",
                cooldown_minutes=5,
                channels=["slack", "email"],
            ),
            "worker_unavailable": AlertRule(
                name="worker_unavailable",
                condition="active_workers == 0",
                severity=AlertSeverity.CRITICAL,
                description="No Celery workers available",
                cooldown_minutes=5,
                channels=["slack", "email"],
            ),
            "queue_backlog": AlertRule(
                name="queue_backlog",
                condition="queue_length > 1000",
                severity=AlertSeverity.WARNING,
                description="Large task queue backlog detected",
                cooldown_minutes=30,
                channels=["slack"],
            ),
            "disk_space_low": AlertRule(
                name="disk_space_low",
                condition="disk_usage_percent > 85",
                severity=AlertSeverity.WARNING,
                description="Low disk space detected",
                cooldown_minutes=60,
                channels=["email"],
            ),
            "memory_usage_high": AlertRule(
                name="memory_usage_high",
                condition="memory_usage_percent > 90",
                severity=AlertSeverity.WARNING,
                description="High memory usage detected",
                cooldown_minutes=15,
                channels=["slack"],
            ),
        }

        return rules

    def _initialize_templates(self) -> Dict[str, Dict[str, str]]:
        """Initialize notification templates"""
        return {
            "pipeline_failure": {
                "email_subject": "ALERT: ETL Pipeline Failure - {pipeline_id}",
                "email_body": """
                <h2>ETL Pipeline Failure Alert</h2>
                <p><strong>Pipeline ID:</strong> {pipeline_id}</p>
                <p><strong>Error:</strong> {error_message}</p>
                <p><strong>Started:</strong> {started_at}</p>
                <p><strong>Failed:</strong> {failed_at}</p>
                
                <h3>Context</h3>
                <ul>
                    <li>Articles Processed: {articles_processed}</li>
                    <li>Processing Time: {processing_time_minutes} minutes</li>
                    <li>Error Count: {error_count}</li>
                </ul>
                
                <p>Please investigate the pipeline logs for detailed error information.</p>
                """,
                "slack_text": "CRITICAL: *Pipeline Failure*\n*Pipeline:* {pipeline_id}\n*Error:* {error_message}\n*Time:* {failed_at}",
            },
            "feed_failures": {
                "email_subject": "WARNING: Multiple Feed Failures Detected",
                "email_body": """
                <h2>Feed Ingestion Failures</h2>
                <p><strong>Failed Feeds:</strong> {failed_feeds_count}</p>
                <p><strong>Time Window:</strong> Last {time_window} hours</p>
                
                <h3>Failed Feeds</h3>
                <ul>
                {failed_feeds_list}
                </ul>
                
                <p>Please check feed configurations and network connectivity.</p>
                """,
                "slack_text": "WARNING: *Feed Failures*\n*Count:* {failed_feeds_count}\n*Time:* Last {time_window}h",
            },
            "database_connection": {
                "email_subject": "CRITICAL: Database Connection Alert",
                "email_body": """
                <h2>Database Connection Critical Alert</h2>
                <p><strong>Status:</strong> {database_status}</p>
                <p><strong>Error:</strong> {error_message}</p>
                <p><strong>Detected:</strong> {detected_at}</p>
                
                <p>Immediate action required - ETL pipeline cannot function without database connectivity.</p>
                """,
                "slack_text": "CRITICAL: *Database Down*\n*Status:* {database_status}\n*Error:* {error_message}",
            },
            "no_recent_articles": {
                "email_subject": "ALERT: No Recent Articles",
                "email_body": """
                <h2>No Recent Articles Alert</h2>
                <p>No articles have been ingested in the last 6 hours.</p>
                <p><strong>Last Article:</strong> {last_article_time}</p>
                <p><strong>Active Feeds:</strong> {active_feeds_count}</p>
                
                <p>Please check feed ingestion status and network connectivity.</p>
                """,
                "slack_text": "WARNING: *No Recent Articles*\nLast article: {last_article_time}\nActive feeds: {active_feeds_count}",
            },
        }

    def _get_configured_channels(self) -> List[str]:
        """Get list of configured notification channels"""
        channels = []

        if self.config.email_smtp_host and self.config.email_recipients:
            channels.append("email")

        if self.config.slack_webhook_url:
            channels.append("slack")

        return channels

    async def send_alert(
        self,
        alert_type: str,
        message: str,
        severity: str = "warning",
        context: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an alert with intelligent routing and suppression.

        Args:
            alert_type: Type of alert (should match rule name)
            message: Alert message
            severity: Alert severity (critical, warning, info, debug)
            context: Additional context for the alert

        Returns:
            True if alert was sent, False if suppressed
        """
        try:
            # Create alert instance
            alert_id = f"{alert_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            alert_severity = AlertSeverity(severity.lower())

            alert = Alert(
                id=alert_id,
                rule_name=alert_type,
                severity=alert_severity,
                title=message,
                description=message,
                context=context or {},
            )

            # Check if alert should be suppressed
            if self._should_suppress_alert(alert):
                self.logger.info(
                    "Alert suppressed due to rate limiting",
                    alert_type=alert_type,
                    alert_id=alert_id,
                )
                alert.status = AlertStatus.SUPPRESSED
                self.suppressed_alerts.add(alert_id)
                return False

            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            self.alert_counts[alert_type] += 1

            # Send notifications
            success = await self._send_notifications(alert)

            if success:
                alert.notification_attempts += 1
                alert.last_notification_at = datetime.utcnow()

                self.logger.info(
                    "Alert sent successfully",
                    alert_type=alert_type,
                    alert_id=alert_id,
                    severity=severity,
                )
            else:
                self.logger.error(
                    "Failed to send alert notifications",
                    alert_type=alert_type,
                    alert_id=alert_id,
                )

            return success

        except Exception as exc:
            self.logger.error(
                "Failed to send alert",
                alert_type=alert_type,
                error=str(exc),
                exc_info=True,
            )
            raise AlertingError(f"Failed to send alert: {str(exc)}") from exc

    def _should_suppress_alert(self, alert: Alert) -> bool:
        """Check if alert should be suppressed due to rate limiting"""

        # Get alert rule
        rule = self.alert_rules.get(alert.rule_name)
        if not rule or not rule.enabled:
            return True

        current_time = datetime.utcnow()

        # Check cooldown period
        cooldown_cutoff = current_time - timedelta(minutes=rule.cooldown_minutes)

        # Check recent alerts of the same type
        recent_alerts = [
            a
            for a in self.alert_history
            if (
                a.rule_name == alert.rule_name
                and a.created_at > cooldown_cutoff
                and a.status != AlertStatus.SUPPRESSED
            )
        ]

        if recent_alerts:
            self.logger.debug(
                "Alert suppressed due to cooldown",
                rule_name=alert.rule_name,
                cooldown_minutes=rule.cooldown_minutes,
                recent_alerts_count=len(recent_alerts),
            )
            return True

        # Check global rate limiting
        hour_cutoff = current_time - timedelta(hours=1)
        recent_count = sum(
            1
            for timestamp in self.alert_timestamps[alert.rule_name]
            if timestamp > hour_cutoff
        )

        if recent_count >= self.config.max_alerts_per_hour:
            self.logger.debug(
                "Alert suppressed due to rate limiting",
                rule_name=alert.rule_name,
                recent_count=recent_count,
                max_per_hour=self.config.max_alerts_per_hour,
            )
            return True

        # Update rate limiting tracking
        self.alert_timestamps[alert.rule_name].append(current_time)

        return False

    async def _send_notifications(self, alert: Alert) -> bool:
        """Send notifications through configured channels"""
        rule = self.alert_rules.get(alert.rule_name)
        if not rule:
            return False

        success = True

        # Send to each configured channel
        for channel in rule.channels:
            try:
                if channel == "email":
                    await self._send_email_notification(alert)
                elif channel == "slack":
                    await self._send_slack_notification(alert)
                else:
                    self.logger.warning("Unknown notification channel", channel=channel)
                    success = False

            except Exception as exc:
                self.logger.error(
                    "Failed to send notification",
                    channel=channel,
                    alert_id=alert.id,
                    error=str(exc),
                )
                success = False

        return success

    async def _send_email_notification(self, alert: Alert):
        """Send email notification"""
        if not self.config.email_smtp_host or not self.config.email_recipients:
            raise AlertingError("Email configuration incomplete")

        # Get template
        template = self.templates.get(alert.rule_name, {})
        subject_template = template.get("email_subject", "ETL Pipeline Alert: {title}")
        body_template = template.get(
            "email_body", "<p>{description}</p><pre>{context}</pre>"
        )

        # Format message
        context_str = (
            json.dumps(alert.context, indent=2)
            if alert.context
            else "No additional context"
        )

        subject = subject_template.format(
            title=alert.title, severity=alert.severity.value.upper(), **alert.context
        )

        body = body_template.format(
            title=alert.title,
            description=alert.description,
            severity=alert.severity.value.upper(),
            created_at=alert.created_at.isoformat(),
            context=context_str,
            **alert.context,
        )

        # Create email message
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.config.email_username or "etl-pipeline@company.com"
        msg["To"] = ", ".join(self.config.email_recipients)

        # Add HTML part
        html_part = MIMEText(body, "html")
        msg.attach(html_part)

        # Send email
        try:
            with smtplib.SMTP(
                self.config.email_smtp_host, self.config.email_smtp_port
            ) as server:
                if self.config.email_username and self.config.email_password:
                    server.starttls()
                    server.login(self.config.email_username, self.config.email_password)

                server.send_message(msg)

                self.logger.info(
                    "Email notification sent",
                    alert_id=alert.id,
                    recipients=len(self.config.email_recipients),
                )

        except Exception as exc:
            raise AlertingError(f"Failed to send email: {str(exc)}") from exc

    async def _send_slack_notification(self, alert: Alert):
        """Send Slack notification"""
        if not self.config.slack_webhook_url:
            raise AlertingError("Slack webhook URL not configured")

        # Get template
        template = self.templates.get(alert.rule_name, {})
        text_template = template.get(
            "slack_text", "*{severity}*: {title}\n{description}"
        )

        # Format message
        text = text_template.format(
            title=alert.title,
            description=alert.description,
            severity=alert.severity.value.upper(),
            created_at=alert.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"),
            **alert.context,
        )

        # Determine color based on severity
        color_map = {
            AlertSeverity.CRITICAL: "danger",
            AlertSeverity.WARNING: "warning",
            AlertSeverity.INFO: "good",
            AlertSeverity.DEBUG: "#808080",
        }

        # Create Slack payload
        payload = {
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "warning"),
                    "title": f"{alert.severity.value.upper()}: {alert.title}",
                    "text": text,
                    "footer": "ETL Pipeline Monitoring",
                    "ts": int(alert.created_at.timestamp()),
                }
            ]
        }

        # Add context fields if available
        if alert.context:
            fields = []
            for key, value in alert.context.items():
                if isinstance(value, (str, int, float, bool)):
                    fields.append(
                        {
                            "title": key.replace("_", " ").title(),
                            "value": str(value),
                            "short": True,
                        }
                    )

            if fields:
                payload["attachments"][0]["fields"] = fields[:10]  # Limit to 10 fields

        # Send to Slack
        try:
            if not self.http_session:
                self.http_session = aiohttp.ClientSession()

            async with self.http_session.post(
                self.config.slack_webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as response:
                if response.status == 200:
                    self.logger.info(
                        "Slack notification sent",
                        alert_id=alert.id,
                        webhook_response=response.status,
                    )
                else:
                    error_text = await response.text()
                    raise AlertingError(
                        f"Slack webhook returned {response.status}: {error_text}"
                    )

        except Exception as exc:
            raise AlertingError(
                f"Failed to send Slack notification: {str(exc)}"
            ) from exc

    async def resolve_alert(
        self, alert_id: str, resolved_by: Optional[str] = None
    ) -> bool:
        """Mark an alert as resolved"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.utcnow()

            self.logger.info(
                "Alert resolved", alert_id=alert_id, resolved_by=resolved_by
            )

            # Remove from active alerts
            del self.active_alerts[alert_id]
            return True

        return False

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = acknowledged_by

            self.logger.info(
                "Alert acknowledged", alert_id=alert_id, acknowledged_by=acknowledged_by
            )

            return True

        return False

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        return [
            {
                "id": alert.id,
                "rule_name": alert.rule_name,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description,
                "status": alert.status.value,
                "created_at": alert.created_at.isoformat(),
                "context": alert.context,
            }
            for alert in self.active_alerts.values()
        ]

    def get_alert_statistics(self) -> Dict[str, Any]:
        """Get alert statistics"""
        current_time = datetime.utcnow()

        # Count alerts by severity for last 24 hours
        day_cutoff = current_time - timedelta(hours=24)
        recent_alerts = [a for a in self.alert_history if a.created_at > day_cutoff]

        severity_counts = defaultdict(int)
        status_counts = defaultdict(int)
        rule_counts = defaultdict(int)

        for alert in recent_alerts:
            severity_counts[alert.severity.value] += 1
            status_counts[alert.status.value] += 1
            rule_counts[alert.rule_name] += 1

        return {
            "timestamp": current_time.isoformat(),
            "active_alerts_count": len(self.active_alerts),
            "suppressed_alerts_count": len(self.suppressed_alerts),
            "total_alerts_24h": len(recent_alerts),
            "severity_distribution_24h": dict(severity_counts),
            "status_distribution_24h": dict(status_counts),
            "rule_distribution_24h": dict(rule_counts),
            "configured_channels": self._get_configured_channels(),
        }

    def cleanup_old_alerts(self, max_age_hours: int = 72):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)

        # Clean up alert history
        while (
            self.alert_history
            and self.alert_history[0].created_at < cutoff_time
            and self.alert_history[0].status
            in [AlertStatus.RESOLVED, AlertStatus.SUPPRESSED]
        ):
            self.alert_history.popleft()

        # Clean up suppressed alerts set
        self.suppressed_alerts = {
            alert_id
            for alert_id in self.suppressed_alerts
            if alert_id in self.active_alerts
            or any(
                a.id == alert_id and a.created_at > cutoff_time
                for a in self.alert_history
            )
        }

        self.logger.debug("Old alerts cleaned up", cutoff_time=cutoff_time.isoformat())

    async def close(self):
        """Close HTTP session and cleanup resources"""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
