"""Main agent logic."""
import sys
import signal
import time
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

from config import Config
from metrics_collector import MetricsCollector
from buffer_manager import BufferManager
from api_client import APIClient


class MonitoringAgent:
    """Main monitoring agent."""
    
    def __init__(self, config_path: str = None):
        self.running = False
        self.config = Config(config_path) if config_path else Config()
        self._setup_logging()
        
        self.logger.info("Initializing Monitoring Agent")
        
        # Initialize components
        self.collector = MetricsCollector()
        self.buffer = BufferManager(
            self.config.buffer_path,
            self.config.buffer_max_records
        ) if self.config.buffer_enabled else None
        
        self.api_client = APIClient(
            self.config.backend_url,
            self.config.api_key,
            self.config.verify_ssl,
            self.config.timeout
        )
        
        self.retry_delay = self.config.retry_initial_delay
        self.last_collection_time = 0
        
        # Setup signal handlers
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        self.logger.info(f"Agent initialized for server: {self.collector.hostname}")
        self.logger.info(f"Server ID: {self.collector.server_id}")
        self.logger.info(f"Backend URL: {self.config.backend_url}")
    
    def _setup_logging(self):
        """Setup logging configuration."""
        # Ensure log directory exists
        log_file = self.config.log_file
        log_dir = os.path.dirname(log_file)
        
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except PermissionError:
                # Fallback to local logging if can't create system log dir
                log_file = "agent.log"
        
        # For development, also log to local file if system log fails
        if not os.access(log_dir, os.W_OK) if log_dir else False:
            log_file = "agent.log"
        
        self.logger = logging.getLogger('MonitoringAgent')
        self.logger.setLevel(getattr(logging, self.config.log_level))
        
        # Rotating file handler
        try:
            handler = RotatingFileHandler(
                log_file,
                maxBytes=self.config.log_max_bytes,
                backupCount=self.config.log_backup_count
            )
        except Exception:
            # Fallback to console if file logging fails
            handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        
        # Also log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        self.logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def _collect_and_send(self):
        """Collect metrics and send to backend."""
        try:
            # Collect metrics
            self.logger.debug("Collecting metrics...")
            metrics = self.collector.collect_all()
            
            # Try to send to backend
            success = self.api_client.send_metrics(metrics)
            
            if success:
                self.logger.info("Metrics sent successfully")
                self.retry_delay = self.config.retry_initial_delay
                
                # Try to send buffered metrics if any
                if self.buffer:
                    self._send_buffered_metrics()
            else:
                self.logger.warning("Failed to send metrics to backend")
                
                # Store in buffer if enabled
                if self.buffer:
                    self.buffer.add(metrics)
                    buffer_count = self.buffer.get_count()
                    self.logger.info(f"Metrics buffered locally ({buffer_count} total)")
        
        except Exception as e:
            self.logger.error(f"Error in collect_and_send: {e}", exc_info=True)
    
    def _send_buffered_metrics(self):
        """Attempt to send buffered metrics."""
        if not self.buffer:
            return
        
        buffer_count = self.buffer.get_count()
        if buffer_count == 0:
            return
        
        self.logger.info(f"Attempting to send {buffer_count} buffered metrics")
        
        batch = self.buffer.get_batch(self.config.buffer_batch_size)
        if not batch:
            return
        
        # Extract metrics from batch
        metrics_list = [item['metrics'] for item in batch]
        ids = [item['id'] for item in batch]
        
        # Try to send
        success = self.api_client.send_metrics_batch(metrics_list)
        
        if success:
            self.buffer.remove_batch(ids)
            remaining = self.buffer.get_count()
            self.logger.info(
                f"Sent {len(batch)} buffered metrics, {remaining} remaining"
            )
        else:
            self.buffer.increment_retry(ids)
            self.logger.warning(f"Failed to send buffered metrics")
    
    def _send_heartbeat(self):
        """Send heartbeat to backend."""
        try:
            self.api_client.send_heartbeat(
                self.collector.server_id,
                self.collector.hostname
            )
        except Exception as e:
            self.logger.debug(f"Heartbeat error: {e}")
    
    def run(self):
        """Main agent loop."""
        self.running = True
        self.logger.info("Agent started")
        
        # Test connection on startup
        if self.api_client.test_connection():
            self.logger.info("Backend connection successful")
        else:
            self.logger.warning("Cannot reach backend - will retry")
        
        # Initial collection
        self._collect_and_send()
        self.last_collection_time = time.time()
        
        # Main loop
        heartbeat_interval = 60  # Send heartbeat every minute
        last_heartbeat = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Check if it's time to collect metrics
                if current_time - self.last_collection_time >= self.config.collection_interval:
                    self._collect_and_send()
                    self.last_collection_time = current_time
                
                # Send heartbeat
                if current_time - last_heartbeat >= heartbeat_interval:
                    self._send_heartbeat()
                    last_heartbeat = current_time
                
                # Sleep for a short interval
                time.sleep(10)
            
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(30)
        
        self.logger.info("Agent stopped")
    
    def cleanup(self):
        """Cleanup resources."""
        self.logger.info("Cleaning up...")
        
        # Clear old buffered records
        if self.buffer:
            deleted = self.buffer.clear_old_records(days=7)
            if deleted > 0:
                self.logger.info(f"Cleared {deleted} old buffered records")


def main():
    """Entry point."""
    config_path = None
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    
    agent = MonitoringAgent(config_path)
    
    try:
        agent.run()
    except KeyboardInterrupt:
        pass
    finally:
        agent.cleanup()


if __name__ == '__main__':
    main()
