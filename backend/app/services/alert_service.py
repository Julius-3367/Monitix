"""Alert service for evaluating and managing alerts."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
import logging

from app.db.models import Alert, AlertRule, Server, MetricData, User
from app.schemas.alert import AlertRuleCreate, AlertRuleUpdate

logger = logging.getLogger(__name__)


class AlertService:
    """Service for alert management."""
    
    @staticmethod
    def create_alert_rule(db: Session, rule: AlertRuleCreate) -> AlertRule:
        """Create a new alert rule."""
        db_rule = AlertRule(**rule.model_dump())
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    
    @staticmethod
    def get_alert_rules(db: Session, enabled_only: bool = False) -> List[AlertRule]:
        """Get all alert rules."""
        query = db.query(AlertRule)
        if enabled_only:
            query = query.filter(AlertRule.enabled == True)
        return query.all()
    
    @staticmethod
    def update_alert_rule(db: Session, rule_id: int, update: AlertRuleUpdate) -> Optional[AlertRule]:
        """Update an alert rule."""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            return None
        
        for key, value in update.model_dump(exclude_unset=True).items():
            setattr(rule, key, value)
        
        db.commit()
        db.refresh(rule)
        return rule
    
    @staticmethod
    def delete_alert_rule(db: Session, rule_id: int) -> bool:
        """Delete an alert rule."""
        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if rule:
            db.delete(rule)
            db.commit()
            return True
        return False
    
    @staticmethod
    def evaluate_rules(db: Session) -> List[Alert]:
        """Evaluate all enabled alert rules and create alerts."""
        rules = AlertService.get_alert_rules(db, enabled_only=True)
        new_alerts = []
        
        for rule in rules:
            # Get servers to check
            if rule.server_id:
                servers = [db.query(Server).get(rule.server_id)]
            else:
                servers = db.query(Server).filter(Server.is_active == True).all()
            
            for server in servers:
                if not server:
                    continue
                
                # Get latest metric
                latest_metric = db.query(MetricData).filter(
                    MetricData.server_id == server.id
                ).order_by(MetricData.timestamp.desc()).first()
                
                if not latest_metric:
                    continue
                
                # Get metric value based on metric name
                current_value = AlertService._get_metric_value(latest_metric, rule.metric_name)
                
                if current_value is None:
                    continue
                
                # Evaluate threshold
                severity = None
                threshold = None
                
                if rule.threshold_critical and AlertService._check_condition(
                    current_value, rule.condition, rule.threshold_critical
                ):
                    severity = "critical"
                    threshold = rule.threshold_critical
                elif rule.threshold_warning and AlertService._check_condition(
                    current_value, rule.condition, rule.threshold_warning
                ):
                    severity = "warning"
                    threshold = rule.threshold_warning
                
                if severity:
                    # Check if alert already exists and is active
                    existing = db.query(Alert).filter(
                        Alert.server_id == server.id,
                        Alert.rule_id == rule.id,
                        Alert.resolved_at == None
                    ).first()
                    
                    if not existing:
                        # Create new alert
                        alert = Alert(
                            server_id=server.id,
                            rule_id=rule.id,
                            alert_type="metric_threshold",
                            severity=severity,
                            metric_name=rule.metric_name,
                            current_value=current_value,
                            threshold_value=threshold,
                            message=f"{rule.name}: {rule.metric_name} is {current_value:.2f} (threshold: {threshold})"
                        )
                        db.add(alert)
                        new_alerts.append(alert)
                        logger.info(f"Created alert for {server.hostname}: {rule.name}")
                else:
                    # Resolve any existing alerts for this rule
                    existing = db.query(Alert).filter(
                        Alert.server_id == server.id,
                        Alert.rule_id == rule.id,
                        Alert.resolved_at == None
                    ).first()
                    
                    if existing:
                        existing.resolved_at = datetime.utcnow()
                        logger.info(f"Resolved alert for {server.hostname}: {rule.name}")
        
        db.commit()
        return new_alerts
    
    @staticmethod
    def _get_metric_value(metric: MetricData, metric_name: str) -> Optional[float]:
        """Extract metric value by name."""
        mapping = {
            'cpu_usage_percent': metric.cpu_usage_percent,
            'cpu_load_1m': metric.cpu_load_1m,
            'cpu_load_5m': metric.cpu_load_5m,
            'memory_percent': metric.memory_percent,
            'swap_percent': metric.swap_percent,
        }
        
        # Handle disk metrics
        if metric_name.startswith('disk_usage_percent'):
            if metric.disk_usage:
                # Return max disk usage across all mounts
                return max((d.get('percent', 0) for d in metric.disk_usage), default=0)
        
        return mapping.get(metric_name)
    
    @staticmethod
    def _check_condition(value: float, condition: str, threshold: float) -> bool:
        """Check if condition is met."""
        if condition == 'gt':
            return value > threshold
        elif condition == 'lt':
            return value < threshold
        elif condition == 'eq':
            return value == threshold
        return False
    
    @staticmethod
    def check_heartbeat_alerts(db: Session, timeout_minutes: int = 10) -> List[Alert]:
        """Check for servers that haven't sent heartbeat."""
        cutoff = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        offline_servers = db.query(Server).filter(
            Server.is_active == True,
            Server.last_seen < cutoff
        ).all()
        
        new_alerts = []
        for server in offline_servers:
            # Update server status
            server.status = "offline"
            
            # Check if alert exists
            existing = db.query(Alert).filter(
                Alert.server_id == server.id,
                Alert.alert_type == "heartbeat",
                Alert.resolved_at == None
            ).first()
            
            if not existing:
                alert = Alert(
                    server_id=server.id,
                    alert_type="heartbeat",
                    severity="critical",
                    metric_name="heartbeat",
                    message=f"Server {server.hostname} is offline (no heartbeat for {timeout_minutes} minutes)"
                )
                db.add(alert)
                new_alerts.append(alert)
                logger.warning(f"Server {server.hostname} is offline")
        
        db.commit()
        return new_alerts
    
    @staticmethod
    def acknowledge_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
        """Acknowledge an alert."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.acknowledged_at = datetime.utcnow()
            alert.acknowledged_by = user_id
            db.commit()
            db.refresh(alert)
        return alert
    
    @staticmethod
    def resolve_alert(db: Session, alert_id: int) -> Optional[Alert]:
        """Manually resolve an alert."""
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if alert:
            alert.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(alert)
        return alert
    
    @staticmethod
    def get_active_alerts(db: Session, server_id: Optional[int] = None) -> List[Alert]:
        """Get active alerts."""
        query = db.query(Alert).filter(Alert.resolved_at == None)
        if server_id:
            query = query.filter(Alert.server_id == server_id)
        return query.order_by(Alert.triggered_at.desc()).all()
