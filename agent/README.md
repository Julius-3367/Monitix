# Monitoring Agent

Lightweight Python agent for collecting server metrics and sending them to the central monitoring backend.

## Features

- Collects CPU, memory, disk, and network metrics
- Runs every 5 minutes automatically
- Local SQLite buffering for offline resilience
- Exponential backoff retry logic
- Runs as systemd service
- Low resource usage (<50MB RAM)

## Installation

### Prerequisites

- Python 3.7+
- pip
- Root access (for systemd service)

### Quick Install

```bash
# Run the installation script
sudo ./install.sh
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Copy files to /opt/monitoring-agent/
sudo mkdir -p /opt/monitoring-agent
sudo cp *.py /opt/monitoring-agent/
sudo cp config.yaml.example /opt/monitoring-agent/config.yaml

# Create directories
sudo mkdir -p /var/log/monitoring-agent
sudo mkdir -p /var/lib/monitoring-agent

# Install systemd service
sudo cp monitoring-agent.service /etc/systemd/system/
sudo systemctl daemon-reload
```

## Configuration

Edit `/opt/monitoring-agent/config.yaml`:

```yaml
backend:
  url: "http://your-backend-server:8000"
  api_key: "your-api-key-here"  # Get from backend admin
  verify_ssl: true
  timeout: 30

collection:
  interval_seconds: 300  # 5 minutes

logging:
  level: "INFO"
```

### Getting an API Key

1. Log into the monitoring backend dashboard as admin
2. Go to Settings → Servers
3. Click "Add Server" or "Register Server"
4. Copy the generated API key
5. Paste it into the agent config.yaml

## Usage

```bash
# Start agent
sudo systemctl start monitoring-agent

# Stop agent
sudo systemctl stop monitoring-agent

# Restart agent
sudo systemctl restart monitoring-agent

# Enable on boot
sudo systemctl enable monitoring-agent

# Check status
sudo systemctl status monitoring-agent

# View logs
sudo tail -f /var/log/monitoring-agent/agent.log
```

## Testing

Test the agent before installing as a service:

```bash
# Create local config
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Run agent in foreground
python3 agent.py

# Check if metrics are being collected
# Check backend dashboard to see if server appears
```

## Metrics Collected

- **CPU:** Usage %, load average, per-core usage
- **Memory:** Total, used, available, swap
- **Disk:** Usage per mount point, I/O stats
- **Network:** Bytes/packets in/out, errors per interface
- **System:** Uptime, heartbeat timestamp

## Offline Behavior

When the backend is unreachable:
- Metrics are stored in local SQLite database
- Up to 1000 records buffered (configurable)
- Automatic retry with exponential backoff
- Metrics sent when connection restored

## Troubleshooting

### Agent not starting

```bash
# Check service status
sudo systemctl status monitoring-agent

# Check logs
sudo journalctl -u monitoring-agent -n 50

# Check configuration
sudo cat /opt/monitoring-agent/config.yaml
```

### Can't connect to backend

- Verify backend URL is correct
- Check network connectivity: `ping your-backend-server`
- Verify firewall rules allow outbound HTTP/HTTPS
- Check API key is valid

### High CPU usage

- Check collection interval (should be 300 seconds minimum)
- Review logs for errors
- Ensure psutil is properly installed

## Uninstallation

```bash
# Stop and disable service
sudo systemctl stop monitoring-agent
sudo systemctl disable monitoring-agent

# Remove files
sudo rm -rf /opt/monitoring-agent
sudo rm -rf /var/log/monitoring-agent
sudo rm -rf /var/lib/monitoring-agent
sudo rm /etc/systemd/system/monitoring-agent.service

# Reload systemd
sudo systemctl daemon-reload
```

## Security

- API keys are stored in config file (600 permissions)
- Agent runs as root to access system metrics
- Supports SSL/TLS verification
- No inbound connections required

## Performance

- Memory usage: ~30-50MB
- CPU usage: <1% average
- Disk usage: <100MB (including buffer)
- Network usage: ~1KB per 5-minute interval

## Support

For issues, check:
1. Agent logs: `/var/log/monitoring-agent/agent.log`
2. System logs: `journalctl -u monitoring-agent`
3. Backend API health: `http://backend:8000/api/v1/system/health`
