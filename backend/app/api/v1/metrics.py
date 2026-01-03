"""Metrics API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Server
from app.schemas.metric import MetricPayload, MetricBatchPayload, HeartbeatPayload
from app.services.metric_service import MetricService
from app.core.deps import verify_agent_api_key

router = APIRouter()


@router.post("/ingest")
def ingest_metrics(
    payload: MetricBatchPayload,
    db: Session = Depends(get_db),
    server: Server = Depends(verify_agent_api_key)
):
    """Ingest metrics batch from agent."""
    # Process metrics
    success_count = MetricService.process_metrics_batch(db, payload.metrics, server)
    
    return {
        "status": "success",
        "received": payload.batch_size,
        "processed": success_count,
        "server_id": server.server_id
    }


@router.post("/heartbeat")
def heartbeat(
    payload: HeartbeatPayload,
    db: Session = Depends(get_db),
    server: Server = Depends(verify_agent_api_key)
):
    """Receive heartbeat from agent."""
    server.last_heartbeat = datetime.utcnow()
    server.last_seen = datetime.utcnow()
    server.status = "online"
    db.commit()
    
    return {"status": "acknowledged", "server_id": server.server_id}
