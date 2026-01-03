"""FastAPI main application."""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1 import api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Setup logging
logger = setup_logging("INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting application...")
    start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    stop_scheduler()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(api_router, prefix="/api/v1")

# Mount static files and templates
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except Exception:
    logger.warning("Static files directory not found, skipping mount")

templates = Jinja2Templates(directory="app/templates")


# Root endpoint - Dashboard
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - return dashboard."""
    return templates.TemplateResponse("index.html", {"request": request})


# Login page
@app.get("/login.html", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


# System info page
@app.get("/info.html", response_class=HTMLResponse)
async def info_page(request: Request):
    """System information page."""
    return templates.TemplateResponse("info.html", {"request": request})


# Charts page
@app.get("/charts.html", response_class=HTMLResponse)
async def charts_page(request: Request):
    """Metrics charts page."""
    return templates.TemplateResponse("charts.html", {"request": request})


# Alerts management page
@app.get("/alerts.html", response_class=HTMLResponse)
async def alerts_page(request: Request):
    """Alert management page."""
    return templates.TemplateResponse("alerts.html", {"request": request})


# Health check
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
