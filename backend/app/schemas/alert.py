"""Alert schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class AlertRuleBase(BaseModel):
    name: str
    server_id: Optional[int] = None
    metric_name: str
    condition: str  # gt, lt, eq
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    duration_minutes: int = 10
    enabled: bool = True
    notification_emails: Optional[List[str]] = None


class AlertRuleCreate(AlertRuleBase):
    pass


class AlertRuleUpdate(BaseModel):
    name: Optional[str] = None
    metric_name: Optional[str] = None
    condition: Optional[str] = None
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    duration_minutes: Optional[int] = None
    enabled: Optional[bool] = None
    notification_emails: Optional[List[str]] = None


class AlertRuleResponse(AlertRuleBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertBase(BaseModel):
    alert_type: str
    severity: str
    metric_name: str
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    message: str


class AlertResponse(AlertBase):
    id: int
    server_id: int
    rule_id: Optional[int] = None
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[int] = None
    notification_sent: bool
    notification_sent_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class AlertAcknowledge(BaseModel):
    """Acknowledge alert request."""
    pass


class AlertResolve(BaseModel):
    """Resolve alert request."""
    pass
