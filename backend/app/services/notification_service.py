"""Notification service for sending alerts."""
from typing import List
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

from app.core.config import settings
from app.db.models import Alert, Server

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""
    
    @staticmethod
    def send_alert_email(alert: Alert, server: Server, recipients: List[str]) -> bool:
        """Send alert notification via email."""
        if not recipients or not settings.SMTP_HOST:
            logger.warning("Email notification skipped: no recipients or SMTP not configured")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"[{alert.severity.upper()}] Alert: {alert.metric_name} on {server.hostname}"
            msg['From'] = settings.SMTP_FROM
            msg['To'] = ', '.join(recipients)
            
            # Email body
            html = f"""
            <html>
            <head></head>
            <body>
                <h2 style="color: {'#ef4444' if alert.severity == 'critical' else '#f59e0b'}">
                    {alert.severity.upper()} Alert
                </h2>
                <p><strong>Server:</strong> {server.hostname} ({server.ip_address})</p>
                <p><strong>Metric:</strong> {alert.metric_name}</p>
                <p><strong>Current Value:</strong> {alert.current_value:.2f if alert.current_value else 'N/A'}</p>
                <p><strong>Threshold:</strong> {alert.threshold_value:.2f if alert.threshold_value else 'N/A'}</p>
                <p><strong>Time:</strong> {alert.triggered_at}</p>
                <p><strong>Message:</strong> {alert.message}</p>
                <hr>
                <p>This is an automated message from the Server Monitoring System.</p>
            </body>
            </html>
            """
            
            part = MIMEText(html, 'html')
            msg.attach(part)
            
            # Send email
            if settings.SMTP_TLS:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                server.starttls()
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
            
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            
            server.sendmail(settings.SMTP_FROM, recipients, msg.as_string())
            server.quit()
            
            logger.info(f"Alert email sent to {recipients}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to send alert email: {e}")
            return False
