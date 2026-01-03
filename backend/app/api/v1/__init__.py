"""API v1 router initialization."""
from fastapi import APIRouter

from app.api.v1 import auth, metrics, servers, alerts, reports, users, system

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
api_router.include_router(servers.router, prefix="/servers", tags=["servers"])
api_router.include_router(alerts.router, tags=["alerts"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(system.router, prefix="/system", tags=["system"])
