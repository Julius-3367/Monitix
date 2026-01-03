#!/bin/bash

# Monitoring Agent Installation Script

set -e

echo "===================================="
echo "Monitoring Agent Installation"
echo "===================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (use sudo)"
    exit 1
fi

# Configuration
INSTALL_DIR="/opt/monitoring-agent"
LOG_DIR="/var/log/monitoring-agent"
DATA_DIR="/var/lib/monitoring-agent"
SERVICE_NAME="monitoring-agent"

echo "Installing to: $INSTALL_DIR"

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$LOG_DIR"
mkdir -p "$DATA_DIR"

# Copy agent files
echo "Copying agent files..."
cp agent.py "$INSTALL_DIR/"
cp config.py "$INSTALL_DIR/"
cp metrics_collector.py "$INSTALL_DIR/"
cp buffer_manager.py "$INSTALL_DIR/"
cp api_client.py "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Copy or create config file
if [ ! -f "$INSTALL_DIR/config.yaml" ]; then
    if [ -f "config.yaml" ]; then
        cp config.yaml "$INSTALL_DIR/"
    else
        cp config.yaml.example "$INSTALL_DIR/config.yaml"
    fi
    echo "Config file created at $INSTALL_DIR/config.yaml"
    echo "IMPORTANT: Edit $INSTALL_DIR/config.yaml with your backend URL and API key"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
if command -v pip3 &> /dev/null; then
    pip3 install -r "$INSTALL_DIR/requirements.txt"
elif command -v pip &> /dev/null; then
    pip install -r "$INSTALL_DIR/requirements.txt"
else
    echo "ERROR: pip not found. Please install Python pip first."
    exit 1
fi

# Create systemd service file
echo "Creating systemd service..."
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Server Monitoring Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$INSTALL_DIR
ExecStart=/usr/bin/python3 $INSTALL_DIR/agent.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/agent.log
StandardError=append:$LOG_DIR/agent.log

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
echo "Setting permissions..."
chmod 755 "$INSTALL_DIR"
chmod 644 "$INSTALL_DIR"/*.py
chmod 600 "$INSTALL_DIR/config.yaml"
chmod 755 "$LOG_DIR"
chmod 755 "$DATA_DIR"

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

echo ""
echo "===================================="
echo "Installation Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: nano $INSTALL_DIR/config.yaml"
echo "2. Add your backend URL and API key"
echo "3. Start the agent: systemctl start $SERVICE_NAME"
echo "4. Enable on boot: systemctl enable $SERVICE_NAME"
echo "5. Check status: systemctl status $SERVICE_NAME"
echo "6. View logs: tail -f $LOG_DIR/agent.log"
echo ""
