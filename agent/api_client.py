"""HTTP client for communicating with backend API."""
import requests
from typing import Dict, Any, List, Optional
import logging


class APIClient:
    """Client for backend API communication."""
    
    def __init__(self, base_url: str, api_key: str, verify_ssl: bool = True, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        })
        self.logger = logging.getLogger(__name__)
    
    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Send single metrics payload to backend."""
        return self.send_metrics_batch([metrics])
    
    def send_metrics_batch(self, metrics_list: List[Dict[str, Any]]) -> bool:
        """Send batch of metrics to backend."""
        try:
            url = f"{self.base_url}/api/v1/metrics/ingest"
            
            payload = {
                'metrics': metrics_list,
                'batch_size': len(metrics_list)
            }
            
            response = self.session.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Successfully sent {len(metrics_list)} metrics")
                return True
            elif response.status_code == 401:
                self.logger.error("Authentication failed - check API key")
                return False
            else:
                self.logger.warning(
                    f"Failed to send metrics: {response.status_code} - {response.text}"
                )
                return False
        
        except requests.exceptions.Timeout:
            self.logger.warning(f"Request timeout after {self.timeout}s")
            return False
        except requests.exceptions.ConnectionError as e:
            self.logger.warning(f"Connection error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending metrics: {e}")
            return False
    
    def send_heartbeat(self, server_id: str, hostname: str) -> bool:
        """Send heartbeat to backend."""
        try:
            url = f"{self.base_url}/api/v1/metrics/heartbeat"
            
            payload = {
                'server_id': server_id,
                'hostname': hostname
            }
            
            response = self.session.post(
                url,
                json=payload,
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            return response.status_code == 200
        
        except Exception as e:
            self.logger.debug(f"Heartbeat failed: {e}")
            return False
    
    def test_connection(self) -> bool:
        """Test connection to backend."""
        try:
            url = f"{self.base_url}/api/v1/system/health"
            response = self.session.get(
                url,
                verify=self.verify_ssl,
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
