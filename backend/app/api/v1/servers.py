"""Server API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import Server, User
from app.schemas.server import (
    ServerCreate, ServerUpdate, ServerResponse, 
    ServerDetailResponse, ServerRegisterResponse
)
from app.core.deps import get_current_user, get_current_admin_user
from app.core.security import generate_api_key, hash_api_key
from app.services.metric_service import MetricService

router = APIRouter()


@router.get("", response_model=List[ServerResponse])
def list_servers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """List all servers."""
    query = db.query(Server).filter(Server.is_active == True)
    
    if status:
        query = query.filter(Server.status == status)
    
    servers = query.offset(skip).limit(limit).all()
    return servers


@router.get("/{server_id}", response_model=ServerDetailResponse)
def get_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get server details."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Get current metrics
    current_metrics = MetricService.get_server_summary(db, server.id)
    
    response = ServerDetailResponse.model_validate(server)
    response.current_metrics = current_metrics
    return response


@router.post("", response_model=ServerRegisterResponse)
def register_server(
    server: ServerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Register a new server (admin only)."""
    # Generate API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    # Generate server ID
    import uuid
    server_id = str(uuid.uuid4())
    
    # Create server
    db_server = Server(
        server_id=server_id,
        hostname=server.hostname,
        ip_address=server.ip_address,
        api_key_hash=api_key_hash,
        status="offline",
        tags=server.tags
    )
    
    db.add(db_server)
    db.commit()
    db.refresh(db_server)
    
    return ServerRegisterResponse(
        server=db_server,
        api_key=api_key
    )


@router.put("/{server_id}", response_model=ServerResponse)
def update_server(
    server_id: int,
    update: ServerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Update server (admin only)."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(server, key, value)
    
    db.commit()
    db.refresh(server)
    return server


@router.delete("/{server_id}")
def delete_server(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Deactivate server (admin only)."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    server.is_active = False
    db.commit()
    return {"message": "Server deactivated"}


@router.post("/{server_id}/regenerate-key", response_model=dict)
def regenerate_api_key(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user)
):
    """Regenerate API key for server (admin only)."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    # Generate new API key
    api_key = generate_api_key()
    api_key_hash = hash_api_key(api_key)
    
    server.api_key_hash = api_key_hash
    db.commit()
    
    return {"api_key": api_key}


@router.get("/{server_id}/metrics/historical")
def get_historical_metrics(
    server_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    hours: int = 24
):
    """Get historical metrics for a server."""
    server = db.query(Server).filter(Server.id == server_id).first()
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=hours)
    
    metrics = MetricService.get_historical_metrics(db, server.id, start_time, end_time)
    
    # Format for response
    return {
        "server_id": server.server_id,
        "hostname": server.hostname,
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "data_points": len(metrics),
        "metrics": [
            {
                "timestamp": m.timestamp.isoformat(),
                "cpu_percent": m.cpu_usage_percent,
                "memory_percent": m.memory_percent,
                "disk_usage": m.disk_usage,
                "network_stats": m.network_stats
            }
            for m in metrics
        ]
    }
