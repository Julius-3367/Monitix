"""Report API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from pathlib import Path

from app.db.session import get_db
from app.db.models import Report, User
from app.schemas.report import ReportResponse, ReportGenerateRequest
from app.services.report_service import ReportService
from app.core.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[ReportResponse])
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 50
):
    """List all reports."""
    reports = db.query(Report).order_by(
        Report.generated_at.desc()
    ).offset(skip).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get report details."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download report file."""
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    if not report.file_path or not Path(report.file_path).exists():
        raise HTTPException(status_code=404, detail="Report file not found")
    
    return FileResponse(
        report.file_path,
        media_type='text/html',
        filename=f"report_{report.id}.html"
    )


@router.post("/generate", response_model=ReportResponse)
def generate_report(
    request: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate a new report on-demand."""
    # Default to last 5 minutes if not specified
    if not request.end_time:
        request.end_time = datetime.utcnow()
    if not request.start_time:
        request.start_time = request.end_time - timedelta(minutes=5)
    
    report = ReportService.generate_report(
        db,
        request.start_time,
        request.end_time,
        request.report_type,
        current_user.id
    )
    
    return report
