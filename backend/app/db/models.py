"""Database models."""
from sqlalchemy import Boolean, Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class User(Base):
    """User model."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(20), default='viewer')  # admin, viewer
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_login = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))


class Server(Base):
    """Server model."""
    __tablename__ = "servers"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(String(100), unique=True, nullable=False, index=True)
    hostname = Column(String(255), nullable=False, index=True)
    ip_address = Column(String(45))
    api_key_hash = Column(String(255), nullable=False)
    status = Column(String(20), default='offline')  # online, offline, warning, critical
    first_seen = Column(DateTime(timezone=True), server_default=func.now())
    last_seen = Column(DateTime(timezone=True))
    last_heartbeat = Column(DateTime(timezone=True))
    server_metadata = Column(JSON)  # Renamed from metadata to avoid conflict
    tags = Column(JSON)  # Store as JSON array instead of ARRAY for SQLite compatibility
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    alerts = relationship("Alert", back_populates="server")
    metrics = relationship("MetricData", back_populates="server")


class AlertRule(Base):
    """Alert rule model."""
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=True)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(10))  # gt, lt, eq
    threshold_warning = Column(Float)
    threshold_critical = Column(Float)
    duration_minutes = Column(Integer, default=10)
    enabled = Column(Boolean, default=True)
    notification_emails = Column(JSON)  # Store as JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    server = relationship("Server")


class Alert(Base):
    """Alert model."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False)
    rule_id = Column(Integer, ForeignKey('alert_rules.id'), nullable=True)
    alert_type = Column(String(50))
    severity = Column(String(20))  # warning, critical
    metric_name = Column(String(100))
    current_value = Column(Float)
    threshold_value = Column(Float)
    message = Column(Text)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))
    acknowledged_at = Column(DateTime(timezone=True))
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    notification_sent = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime(timezone=True))
    
    # Relationships
    server = relationship("Server", back_populates="alerts")


class Report(Base):
    """Report model."""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_type = Column(String(50), default='periodic')
    period_start = Column(DateTime(timezone=True), nullable=False)
    period_end = Column(DateTime(timezone=True), nullable=False)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    generated_by = Column(Integer, ForeignKey('users.id'))
    summary = Column(JSON)
    file_path = Column(String(500))
    file_format = Column(String(10))
    status = Column(String(20), default='generating')  # generating, completed, failed


class AuditLog(Base):
    """Audit log model."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    resource_id = Column(Integer)
    ip_address = Column(String(45))
    user_agent = Column(String(500))
    details = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)


class ServerGroup(Base):
    """Server group model."""
    __tablename__ = "server_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class MetricData(Base):
    """Metric data model for storing latest metrics."""
    __tablename__ = "metric_data"
    
    id = Column(Integer, primary_key=True, index=True)
    server_id = Column(Integer, ForeignKey('servers.id'), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # CPU metrics
    cpu_usage_percent = Column(Float)
    cpu_load_1m = Column(Float)
    cpu_load_5m = Column(Float)
    cpu_load_15m = Column(Float)
    
    # Memory metrics
    memory_total = Column(Float)
    memory_used = Column(Float)
    memory_available = Column(Float)
    memory_percent = Column(Float)
    swap_total = Column(Float)
    swap_used = Column(Float)
    swap_percent = Column(Float)
    
    # Disk metrics (store as JSON for flexibility)
    disk_usage = Column(JSON)
    disk_io = Column(JSON)
    
    # Network metrics
    network_stats = Column(JSON)
    
    # System metrics
    uptime_seconds = Column(Float)
    
    # Relationships
    server = relationship("Server", back_populates="metrics")
