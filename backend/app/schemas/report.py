"""Report schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class ReportBase(BaseModel):
    report_type: str = "periodic"
    period_start: datetime
    period_end: datetime


class ReportCreate(ReportBase):
    pass


class ReportResponse(ReportBase):
    id: int
    generated_at: datetime
    generated_by: Optional[int] = None
    summary: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    file_format: Optional[str] = None
    status: str
    
    class Config:
        from_attributes = True


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    report_type: str = "on-demand"
    format: str = "html"  # html, pdf, csv
