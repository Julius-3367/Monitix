"""Application configuration."""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # App
    APP_NAME: str = "Server Monitoring System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database
    DATABASE_URL: str = "sqlite:///./monitoring.db"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-this-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "monitoring@example.com"
    SMTP_TLS: bool = True
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Monitoring
    METRICS_RETENTION_DAYS: int = 7
    AGGREGATED_RETENTION_DAYS: int = 90
    REPORT_INTERVAL_MINUTES: int = 5
    ALERT_CHECK_INTERVAL_SECONDS: int = 60
    
    # Prometheus
    PROMETHEUS_ENABLED: bool = False
    PROMETHEUS_PUSHGATEWAY_URL: str = "http://localhost:9091"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
