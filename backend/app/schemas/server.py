"""Server schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any


class ServerBase(BaseModel):
    hostname: str
    ip_address: Optional[str] = None
    tags: Optional[List[str]] = None


class ServerCreate(ServerBase):
    pass


class ServerUpdate(BaseModel):
    hostname: Optional[str] = None
    ip_address: Optional[str] = None
    tags: Optional[List[str]] = None
    is_active: Optional[bool] = None


class ServerResponse(ServerBase):
    id: int
    server_id: str
    status: str
    first_seen: datetime
    last_seen: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    server_metadata: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class ServerDetailResponse(ServerResponse):
    """Detailed server response with current metrics."""
    current_metrics: Optional[Dict[str, Any]] = None


class ServerRegisterResponse(BaseModel):
    """Response after registering a new server."""
    server: ServerResponse
    api_key: str  # Only returned once
