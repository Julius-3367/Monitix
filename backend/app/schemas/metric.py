"""Metric schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import List, Dict, Any, Optional


class DiskUsageMetric(BaseModel):
    device: str
    mountpoint: str
    total: float
    used: float
    free: float
    percent: float


class DiskIOMetric(BaseModel):
    read_bytes: float
    write_bytes: float
    read_count: float
    write_count: float


class NetworkInterfaceMetric(BaseModel):
    interface: str
    bytes_sent: float
    bytes_recv: float
    packets_sent: float
    packets_recv: float
    errin: float
    errout: float
    dropin: float
    dropout: float


class MetricPayload(BaseModel):
    """Single metric payload from agent."""
    server_id: str
    hostname: str
    timestamp: str
    
    # CPU
    cpu_usage_percent: float
    cpu_per_core_percent: Optional[List[float]] = None
    load_average_1m: float
    load_average_5m: float
    load_average_15m: float
    
    # Memory
    memory_total: float
    memory_available: float
    memory_used: float
    memory_percent: float
    swap_total: float
    swap_used: float
    swap_percent: float
    
    # Disk
    disk_usage: List[Dict[str, Any]]
    disk_io: Dict[str, float]
    
    # Network
    network_interfaces: List[Dict[str, Any]]
    
    # System
    boot_time: Optional[float] = None
    uptime_seconds: float
    
    # Metadata (optional, sent periodically)
    metadata: Optional[Dict[str, Any]] = None


class MetricBatchPayload(BaseModel):
    """Batch of metrics from agent."""
    metrics: List[MetricPayload]
    batch_size: int


class HeartbeatPayload(BaseModel):
    """Heartbeat payload."""
    server_id: str
    hostname: str


class MetricQueryParams(BaseModel):
    """Parameters for querying metrics."""
    server_id: Optional[str] = None
    metric_name: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    limit: int = 1000
