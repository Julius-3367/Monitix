"""Configuration management for the monitoring agent."""
import os
import yaml
from typing import Dict, Any


class Config:
    """Agent configuration manager."""
    
    def __init__(self, config_path: str = "/opt/monitoring-agent/config.yaml"):
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        # For development, try local config first
        dev_config = "config.yaml"
        if os.path.exists(dev_config):
            config_path = dev_config
        elif os.path.exists(self.config_path):
            config_path = self.config_path
        else:
            raise FileNotFoundError(
                f"Configuration file not found at {self.config_path} or config.yaml"
            )
        
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value by dot-separated path.
        
        Example: config.get('backend.url')
        """
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    @property
    def backend_url(self) -> str:
        return self.get('backend.url')
    
    @property
    def api_key(self) -> str:
        return self.get('backend.api_key')
    
    @property
    def verify_ssl(self) -> bool:
        return self.get('backend.verify_ssl', True)
    
    @property
    def timeout(self) -> int:
        return self.get('backend.timeout', 30)
    
    @property
    def collection_interval(self) -> int:
        return self.get('collection.interval_seconds', 300)
    
    @property
    def buffer_enabled(self) -> bool:
        return self.get('buffer.enabled', True)
    
    @property
    def buffer_path(self) -> str:
        return self.get('buffer.storage_path', '/var/lib/monitoring-agent/buffer.db')
    
    @property
    def buffer_max_records(self) -> int:
        return self.get('buffer.max_records', 1000)
    
    @property
    def buffer_batch_size(self) -> int:
        return self.get('buffer.batch_size', 50)
    
    @property
    def retry_enabled(self) -> bool:
        return self.get('retry.enabled', True)
    
    @property
    def retry_initial_delay(self) -> int:
        return self.get('retry.initial_delay', 60)
    
    @property
    def retry_max_delay(self) -> int:
        return self.get('retry.max_delay', 600)
    
    @property
    def retry_backoff(self) -> float:
        return self.get('retry.backoff_multiplier', 2.0)
    
    @property
    def log_level(self) -> str:
        return self.get('logging.level', 'INFO')
    
    @property
    def log_file(self) -> str:
        return self.get('logging.file', '/var/log/monitoring-agent/agent.log')
    
    @property
    def log_max_bytes(self) -> int:
        return self.get('logging.max_bytes', 10485760)
    
    @property
    def log_backup_count(self) -> int:
        return self.get('logging.backup_count', 5)
