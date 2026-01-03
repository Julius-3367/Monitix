"""System metrics collection using psutil."""
import psutil
import platform
import socket
import uuid
from datetime import datetime
from typing import Dict, Any, List


class MetricsCollector:
    """Collect system metrics from the local server."""
    
    def __init__(self):
        self.server_id = self._get_server_id()
        self.hostname = socket.gethostname()
        self.metadata = self._collect_metadata()
    
    def _get_server_id(self) -> str:
        """Generate or retrieve unique server ID."""
        # Use MAC address-based UUID for consistency
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, socket.gethostname()))
    
    def _collect_metadata(self) -> Dict[str, Any]:
        """Collect static server metadata (run once)."""
        uname = platform.uname()
        
        # Get IP addresses
        ip_addresses = []
        try:
            # Get all network interfaces
            for interface, addrs in psutil.net_if_addrs().items():
                for addr in addrs:
                    if addr.family == socket.AF_INET:  # IPv4
                        ip_addresses.append(addr.address)
        except Exception:
            pass
        
        # Get primary IP
        primary_ip = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            primary_ip = s.getsockname()[0]
            s.close()
        except Exception:
            primary_ip = ip_addresses[0] if ip_addresses else "127.0.0.1"
        
        # Get disk mount points
        mount_points = []
        for partition in psutil.disk_partitions():
            mount_points.append({
                'device': partition.device,
                'mountpoint': partition.mountpoint,
                'fstype': partition.fstype
            })
        
        # Get network interfaces
        network_interfaces = []
        for interface in psutil.net_if_addrs().keys():
            if interface != 'lo':  # Skip loopback
                network_interfaces.append(interface)
        
        return {
            'server_id': self.server_id,
            'hostname': self.hostname,
            'ip_address': primary_ip,
            'ip_addresses': ip_addresses,
            'os': uname.system,
            'os_version': uname.release,
            'os_distribution': platform.platform(),
            'kernel_version': uname.version,
            'architecture': uname.machine,
            'cpu_cores': psutil.cpu_count(logical=False),
            'cpu_threads': psutil.cpu_count(logical=True),
            'total_memory': psutil.virtual_memory().total,
            'mount_points': mount_points,
            'network_interfaces': network_interfaces,
        }
    
    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect CPU metrics."""
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
        
        return {
            'cpu_usage_percent': cpu_percent,
            'cpu_per_core_percent': cpu_per_core,
            'load_average_1m': load_avg[0],
            'load_average_5m': load_avg[1],
            'load_average_15m': load_avg[2],
        }
    
    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect memory metrics."""
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        return {
            'memory_total': mem.total,
            'memory_available': mem.available,
            'memory_used': mem.used,
            'memory_percent': mem.percent,
            'swap_total': swap.total,
            'swap_used': swap.used,
            'swap_percent': swap.percent,
        }
    
    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect disk usage and I/O metrics."""
        disk_usage = []
        
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_usage.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent,
                })
            except PermissionError:
                continue
        
        # Disk I/O
        io_counters = psutil.disk_io_counters()
        disk_io = {
            'read_bytes': io_counters.read_bytes if io_counters else 0,
            'write_bytes': io_counters.write_bytes if io_counters else 0,
            'read_count': io_counters.read_count if io_counters else 0,
            'write_count': io_counters.write_count if io_counters else 0,
        }
        
        return {
            'disk_usage': disk_usage,
            'disk_io': disk_io,
        }
    
    def collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network metrics."""
        net_io = psutil.net_io_counters(pernic=True)
        
        network_stats = []
        for interface, counters in net_io.items():
            if interface != 'lo':  # Skip loopback
                network_stats.append({
                    'interface': interface,
                    'bytes_sent': counters.bytes_sent,
                    'bytes_recv': counters.bytes_recv,
                    'packets_sent': counters.packets_sent,
                    'packets_recv': counters.packets_recv,
                    'errin': counters.errin,
                    'errout': counters.errout,
                    'dropin': counters.dropin,
                    'dropout': counters.dropout,
                })
        
        return {'network_interfaces': network_stats}
    
    def collect_system_metrics(self) -> Dict[str, Any]:
        """Collect system-level metrics."""
        boot_time = psutil.boot_time()
        uptime = datetime.now().timestamp() - boot_time
        
        return {
            'boot_time': boot_time,
            'uptime_seconds': uptime,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
    
    def collect_all(self) -> Dict[str, Any]:
        """Collect all metrics and return as a single dictionary."""
        metrics = {
            'server_id': self.server_id,
            'hostname': self.hostname,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
        }
        
        # Collect all metric types
        metrics.update(self.collect_cpu_metrics())
        metrics.update(self.collect_memory_metrics())
        metrics.update(self.collect_disk_metrics())
        metrics.update(self.collect_network_metrics())
        metrics.update(self.collect_system_metrics())
        
        # Add metadata on first collection or periodically
        metrics['metadata'] = self.metadata
        
        return metrics
