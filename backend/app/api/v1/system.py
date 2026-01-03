"""System API endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import Server, Alert, User
from app.core.deps import get_current_user

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "monitoring-backend"}


@router.get("/stats")
def system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system statistics."""
    total_servers = db.query(func.count(Server.id)).filter(Server.is_active == True).scalar()
    servers_online = db.query(func.count(Server.id)).filter(
        Server.is_active == True,
        Server.status == 'online'
    ).scalar()
    servers_offline = db.query(func.count(Server.id)).filter(
        Server.is_active == True,
        Server.status == 'offline'
    ).scalar()
    
    active_alerts = db.query(func.count(Alert.id)).filter(
        Alert.resolved_at == None
    ).scalar()
    
    critical_alerts = db.query(func.count(Alert.id)).filter(
        Alert.resolved_at == None,
        Alert.severity == 'critical'
    ).scalar()
    
    return {
        "total_servers": total_servers or 0,
        "servers_online": servers_online or 0,
        "servers_offline": servers_offline or 0,
        "active_alerts": active_alerts or 0,
        "critical_alerts": critical_alerts or 0
    }
