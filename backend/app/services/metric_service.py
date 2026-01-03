"""Metric service for processing and storing metrics."""
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import logging

from app.db.models import Server, MetricData
from app.schemas.metric import MetricPayload
from app.core.security import hash_api_key

logger = logging.getLogger(__name__)


class MetricService:
    """Service for handling metrics."""
    
    @staticmethod
    def process_metric(db: Session, metric: MetricPayload, server: Server) -> bool:
        """Process and store a single metric."""
        try:
            # Update server metadata if provided
            if metric.metadata:
                server.server_metadata = metric.metadata
            
            # Update server last_seen
            server.last_seen = datetime.utcnow()
            server.status = "online"
            
            # Parse timestamp
            try:
                timestamp = datetime.fromisoformat(metric.timestamp.replace('Z', '+00:00'))
            except Exception:
                timestamp = datetime.utcnow()
            
            # Create metric record
            metric_data = MetricData(
                server_id=server.id,
                timestamp=timestamp,
                cpu_usage_percent=metric.cpu_usage_percent,
                cpu_load_1m=metric.load_average_1m,
                cpu_load_5m=metric.load_average_5m,
                cpu_load_15m=metric.load_average_15m,
                memory_total=metric.memory_total,
                memory_used=metric.memory_used,
                memory_available=metric.memory_available,
                memory_percent=metric.memory_percent,
                swap_total=metric.swap_total,
                swap_used=metric.swap_used,
                swap_percent=metric.swap_percent,
                disk_usage=metric.disk_usage,
                disk_io=metric.disk_io,
                network_stats=metric.network_interfaces,
                uptime_seconds=metric.uptime_seconds
            )
            
            db.add(metric_data)
            db.commit()
            
            logger.info(f"Processed metric for server {server.hostname}")
            return True
        
        except Exception as e:
            logger.error(f"Error processing metric: {e}")
            db.rollback()
            return False
    
    @staticmethod
    def process_metrics_batch(db: Session, metrics: List[MetricPayload], server: Server) -> int:
        """Process a batch of metrics."""
        success_count = 0
        
        for metric in metrics:
            if MetricService.process_metric(db, metric, server):
                success_count += 1
        
        return success_count
    
    @staticmethod
    def get_latest_metrics(db: Session, server_id: int) -> Optional[MetricData]:
        """Get latest metrics for a server."""
        return db.query(MetricData).filter(
            MetricData.server_id == server_id
        ).order_by(MetricData.timestamp.desc()).first()
    
    @staticmethod
    def get_historical_metrics(
        db: Session,
        server_id: int,
        start_time: datetime,
        end_time: datetime,
        limit: int = 1000
    ) -> List[MetricData]:
        """Get historical metrics for a server."""
        return db.query(MetricData).filter(
            MetricData.server_id == server_id,
            MetricData.timestamp >= start_time,
            MetricData.timestamp <= end_time
        ).order_by(MetricData.timestamp.desc()).limit(limit).all()
    
    @staticmethod
    def cleanup_old_metrics(db: Session, retention_days: int = 7) -> int:
        """Delete metrics older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        deleted = db.query(MetricData).filter(
            MetricData.timestamp < cutoff
        ).delete()
        
        db.commit()
        logger.info(f"Cleaned up {deleted} old metric records")
        return deleted
    
    @staticmethod
    def get_server_summary(db: Session, server_id: int) -> Dict[str, Any]:
        """Get summary statistics for a server."""
        # Get latest metric
        latest = MetricService.get_latest_metrics(db, server_id)
        
        if not latest:
            return {}
        
        # Calculate max disk usage across all mounts
        max_disk_percent = 0
        if latest.disk_usage:
            for disk in latest.disk_usage:
                if disk.get('percent', 0) > max_disk_percent:
                    max_disk_percent = disk['percent']
        
        return {
            'cpu_percent': latest.cpu_usage_percent,
            'memory_percent': latest.memory_percent,
            'disk_percent': max_disk_percent,
            'timestamp': latest.timestamp,
            'uptime_seconds': latest.uptime_seconds
        }
