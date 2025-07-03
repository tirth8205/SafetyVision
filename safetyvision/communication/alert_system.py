"""
Multi-channel alert and notification system for nuclear facility monitoring
"""

import asyncio
import logging
import smtplib
import json
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4
    EMERGENCY = 5


class AlertChannel(Enum):
    """Available alert channels"""
    EMAIL = "email"
    SMS = "sms"
    DASHBOARD = "dashboard"
    AUDIO = "audio"
    LOG = "log"
    WEBHOOK = "webhook"
    MQTT = "mqtt"


@dataclass
class Alert:
    """Alert data structure"""
    id: str
    severity: AlertSeverity
    title: str
    message: str
    timestamp: datetime
    source: str
    location: Optional[str] = None
    sensor_data: Optional[Dict] = None
    requires_acknowledgment: bool = False
    auto_escalate_after: Optional[int] = None  # seconds
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class AlertSubscription:
    """Alert subscription configuration"""
    user_id: str
    channels: List[AlertChannel]
    severity_filter: List[AlertSeverity]
    location_filter: Optional[List[str]] = None
    source_filter: Optional[List[str]] = None
    quiet_hours: Optional[Dict[str, str]] = None  # {"start": "22:00", "end": "06:00"}


class AlertDeliveryService:
    """Handles delivery of alerts through various channels"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': 'localhost',
            'smtp_port': 587,
            'username': '',
            'password': '',
            'use_tls': True
        }
        self.webhook_urls = {}
        self.mqtt_client = None
        
    async def deliver_email(self, alert: Alert, recipients: List[str]):
        """Deliver alert via email"""
        try:
            subject = f"[SafetyVision] {alert.severity.name}: {alert.title}"
            
            body = f"""
            SafetyVision Alert Notification
            
            Severity: {alert.severity.name}
            Time: {alert.timestamp}
            Location: {alert.location or 'Unknown'}
            Source: {alert.source}
            
            Message:
            {alert.message}
            
            {f'Sensor Data: {json.dumps(alert.sensor_data, indent=2)}' if alert.sensor_data else ''}
            
            Alert ID: {alert.id}
            """
            
            msg = MIMEMultipart()
            msg['From'] = self.email_config['username']
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # For demo purposes, just log the email
            logger.info(f"EMAIL ALERT sent to {recipients}: {subject}")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
    
    async def deliver_sms(self, alert: Alert, phone_numbers: List[str]):
        """Deliver alert via SMS"""
        try:
            message = f"SafetyVision {alert.severity.name}: {alert.title} at {alert.location}. {alert.message[:100]}"
            
            # For demo purposes, just log the SMS
            logger.info(f"SMS ALERT sent to {phone_numbers}: {message}")
            
        except Exception as e:
            logger.error(f"Failed to send SMS alert: {e}")
    
    async def deliver_dashboard(self, alert: Alert):
        """Deliver alert to dashboard"""
        try:
            # In production, would push to dashboard via WebSocket or similar
            logger.info(f"DASHBOARD ALERT: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send dashboard alert: {e}")
    
    async def deliver_audio(self, alert: Alert):
        """Deliver audio alert"""
        try:
            # In production, would trigger audio alarm system
            if alert.severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
                logger.critical(f"AUDIO ALARM: {alert.title}")
            else:
                logger.info(f"AUDIO ALERT: {alert.title}")
                
        except Exception as e:
            logger.error(f"Failed to trigger audio alert: {e}")
    
    async def deliver_webhook(self, alert: Alert, webhook_url: str):
        """Deliver alert via webhook"""
        try:
            import aiohttp
            
            payload = {
                'alert': asdict(alert),
                'timestamp': alert.timestamp.isoformat()
            }
            
            # For demo purposes, just log the webhook
            logger.info(f"WEBHOOK ALERT sent to {webhook_url}: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
    
    async def deliver_mqtt(self, alert: Alert, topic: str):
        """Deliver alert via MQTT"""
        try:
            payload = json.dumps(asdict(alert), default=str)
            
            # For demo purposes, just log the MQTT message
            logger.info(f"MQTT ALERT published to {topic}: {alert.title}")
            
        except Exception as e:
            logger.error(f"Failed to publish MQTT alert: {e}")


class AlertManager:
    """
    Central alert management system for SafetyVision
    
    Manages alert routing, escalation, acknowledgment, and delivery
    across multiple channels based on user subscriptions.
    """
    
    def __init__(self):
        self.active_alerts = {}  # alert_id -> Alert
        self.acknowledged_alerts = {}  # alert_id -> acknowledgment_info
        self.subscriptions = []  # List[AlertSubscription]
        self.delivery_service = AlertDeliveryService()
        self.escalation_tasks = {}  # alert_id -> asyncio.Task
        self.alert_history = []
        self.callbacks = []
        
        # Default system subscriptions
        self._setup_default_subscriptions()
        
        logger.info("Alert Manager initialized")
    
    def _setup_default_subscriptions(self):
        """Setup default alert subscriptions"""
        # Emergency operator - gets all critical alerts
        self.subscriptions.append(AlertSubscription(
            user_id="emergency_operator",
            channels=[AlertChannel.EMAIL, AlertChannel.SMS, AlertChannel.AUDIO, AlertChannel.DASHBOARD],
            severity_filter=[AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        ))
        
        # Safety manager - gets warnings and above
        self.subscriptions.append(AlertSubscription(
            user_id="safety_manager",
            channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD],
            severity_filter=[AlertSeverity.WARNING, AlertSeverity.ERROR, AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        ))
        
        # System admin - gets all alerts
        self.subscriptions.append(AlertSubscription(
            user_id="system_admin",
            channels=[AlertChannel.EMAIL, AlertChannel.DASHBOARD, AlertChannel.LOG],
            severity_filter=list(AlertSeverity)
        ))
    
    def add_subscription(self, subscription: AlertSubscription):
        """Add new alert subscription"""
        self.subscriptions.append(subscription)
        logger.info(f"Added alert subscription for user {subscription.user_id}")
    
    def register_callback(self, callback: Callable):
        """Register callback for alert events"""
        self.callbacks.append(callback)
    
    async def send_alert(self, 
                        severity: AlertSeverity,
                        title: str,
                        message: str,
                        source: str,
                        location: Optional[str] = None,
                        sensor_data: Optional[Dict] = None,
                        requires_acknowledgment: bool = None,
                        auto_escalate_after: Optional[int] = None,
                        tags: Optional[List[str]] = None) -> str:
        """
        Send an alert through the system
        
        Returns:
            Alert ID
        """
        # Generate unique alert ID
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.active_alerts)}"
        
        # Set default acknowledgment requirement based on severity
        if requires_acknowledgment is None:
            requires_acknowledgment = severity in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]
        
        # Set default escalation time based on severity
        if auto_escalate_after is None:
            escalation_times = {
                AlertSeverity.EMERGENCY: 60,     # 1 minute
                AlertSeverity.CRITICAL: 300,     # 5 minutes
                AlertSeverity.ERROR: 900,        # 15 minutes
                AlertSeverity.WARNING: 1800,     # 30 minutes
                AlertSeverity.INFO: None         # No escalation
            }
            auto_escalate_after = escalation_times.get(severity)
        
        # Create alert
        alert = Alert(
            id=alert_id,
            severity=severity,
            title=title,
            message=message,
            timestamp=datetime.now(),
            source=source,
            location=location,
            sensor_data=sensor_data,
            requires_acknowledgment=requires_acknowledgment,
            auto_escalate_after=auto_escalate_after,
            tags=tags or []
        )
        
        # Store alert
        self.active_alerts[alert_id] = alert
        self.alert_history.append(alert)
        
        logger.info(f"Alert created: {alert_id} - {severity.name}: {title}")
        
        # Deliver alert to subscribers
        await self._deliver_alert(alert)
        
        # Setup auto-escalation if needed
        if auto_escalate_after and requires_acknowledgment:
            self.escalation_tasks[alert_id] = asyncio.create_task(
                self._auto_escalate_alert(alert_id, auto_escalate_after)
            )
        
        # Trigger callbacks
        for callback in self.callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error in alert callback: {e}")
        
        return alert_id
    
    async def _deliver_alert(self, alert: Alert):
        """Deliver alert to all matching subscriptions"""
        delivery_tasks = []
        
        for subscription in self.subscriptions:
            if self._should_deliver_to_subscription(alert, subscription):
                for channel in subscription.channels:
                    task = self._deliver_to_channel(alert, channel, subscription)
                    delivery_tasks.append(task)
        
        # Execute all deliveries concurrently
        if delivery_tasks:
            await asyncio.gather(*delivery_tasks, return_exceptions=True)
    
    def _should_deliver_to_subscription(self, alert: Alert, subscription: AlertSubscription) -> bool:
        """Check if alert should be delivered to subscription"""
        # Check severity filter
        if alert.severity not in subscription.severity_filter:
            return False
        
        # Check location filter
        if subscription.location_filter and alert.location:
            if alert.location not in subscription.location_filter:
                return False
        
        # Check source filter
        if subscription.source_filter:
            if alert.source not in subscription.source_filter:
                return False
        
        # Check quiet hours (simplified implementation)
        if subscription.quiet_hours and alert.severity not in [AlertSeverity.CRITICAL, AlertSeverity.EMERGENCY]:
            current_time = datetime.now().strftime("%H:%M")
            # In production, would implement proper quiet hours logic
        
        return True
    
    async def _deliver_to_channel(self, alert: Alert, channel: AlertChannel, subscription: AlertSubscription):
        """Deliver alert to specific channel"""
        try:
            if channel == AlertChannel.EMAIL:
                # In production, would get actual email addresses from user database
                await self.delivery_service.deliver_email(alert, [f"{subscription.user_id}@example.com"])
            
            elif channel == AlertChannel.SMS:
                # In production, would get actual phone numbers from user database
                await self.delivery_service.deliver_sms(alert, [f"+1234567890"])  # Demo number
            
            elif channel == AlertChannel.DASHBOARD:
                await self.delivery_service.deliver_dashboard(alert)
            
            elif channel == AlertChannel.AUDIO:
                await self.delivery_service.deliver_audio(alert)
            
            elif channel == AlertChannel.LOG:
                logger.log(
                    logging.CRITICAL if alert.severity == AlertSeverity.EMERGENCY else
                    logging.ERROR if alert.severity == AlertSeverity.CRITICAL else
                    logging.WARNING if alert.severity == AlertSeverity.ERROR else
                    logging.INFO,
                    f"ALERT [{alert.severity.name}] {alert.title}: {alert.message}"
                )
            
            elif channel == AlertChannel.WEBHOOK:
                webhook_url = f"https://hooks.example.com/{subscription.user_id}"
                await self.delivery_service.deliver_webhook(alert, webhook_url)
            
            elif channel == AlertChannel.MQTT:
                topic = f"safetyvision/alerts/{subscription.user_id}"
                await self.delivery_service.deliver_mqtt(alert, topic)
                
        except Exception as e:
            logger.error(f"Failed to deliver alert {alert.id} via {channel.value}: {e}")
    
    async def acknowledge_alert(self, alert_id: str, user_id: str, message: str = ""):
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            raise ValueError(f"Alert {alert_id} not found or already resolved")
        
        alert = self.active_alerts[alert_id]
        
        acknowledgment = {
            'user_id': user_id,
            'timestamp': datetime.now(),
            'message': message
        }
        
        self.acknowledged_alerts[alert_id] = acknowledgment
        
        # Cancel auto-escalation if it exists
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]
        
        logger.info(f"Alert {alert_id} acknowledged by {user_id}")
        
        # Send acknowledgment notification
        await self.send_alert(
            severity=AlertSeverity.INFO,
            title=f"Alert Acknowledged: {alert.title}",
            message=f"Alert {alert_id} has been acknowledged by {user_id}. Message: {message}",
            source="alert_system",
            tags=['acknowledgment']
        )
    
    async def resolve_alert(self, alert_id: str, user_id: str, resolution_message: str = ""):
        """Resolve an alert"""
        if alert_id not in self.active_alerts:
            raise ValueError(f"Alert {alert_id} not found or already resolved")
        
        alert = self.active_alerts.pop(alert_id)
        
        # Cancel escalation task if exists
        if alert_id in self.escalation_tasks:
            self.escalation_tasks[alert_id].cancel()
            del self.escalation_tasks[alert_id]
        
        logger.info(f"Alert {alert_id} resolved by {user_id}")
        
        # Send resolution notification
        await self.send_alert(
            severity=AlertSeverity.INFO,
            title=f"Alert Resolved: {alert.title}",
            message=f"Alert {alert_id} has been resolved by {user_id}. Resolution: {resolution_message}",
            source="alert_system",
            tags=['resolution']
        )
    
    async def _auto_escalate_alert(self, alert_id: str, delay_seconds: int):
        """Auto-escalate unacknowledged alert"""
        try:
            await asyncio.sleep(delay_seconds)
            
            if alert_id in self.active_alerts and alert_id not in self.acknowledged_alerts:
                alert = self.active_alerts[alert_id]
                
                # Escalate to higher severity
                escalated_severity = AlertSeverity.EMERGENCY if alert.severity != AlertSeverity.EMERGENCY else AlertSeverity.EMERGENCY
                
                await self.send_alert(
                    severity=escalated_severity,
                    title=f"ESCALATED: {alert.title}",
                    message=f"Alert {alert_id} was not acknowledged within {delay_seconds} seconds. Original: {alert.message}",
                    source="alert_escalation",
                    location=alert.location,
                    sensor_data=alert.sensor_data,
                    tags=['escalated'] + alert.tags
                )
                
                logger.warning(f"Alert {alert_id} auto-escalated due to no acknowledgment")
        
        except asyncio.CancelledError:
            logger.debug(f"Auto-escalation for alert {alert_id} was cancelled")
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return list(self.active_alerts.values())
    
    def get_alert_statistics(self) -> Dict:
        """Get alert system statistics"""
        severity_counts = {}
        for severity in AlertSeverity:
            severity_counts[severity.name] = len([
                alert for alert in self.active_alerts.values() 
                if alert.severity == severity
            ])
        
        return {
            'active_alerts': len(self.active_alerts),
            'total_alerts': len(self.alert_history),
            'acknowledged_alerts': len(self.acknowledged_alerts),
            'severity_breakdown': severity_counts,
            'subscriptions': len(self.subscriptions)
        }