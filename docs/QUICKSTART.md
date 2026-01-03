# Monitix - Quick Start Guide

This guide will help you set up and test the monitoring system in under 5 minutes.

## Automated Setup (Recommended)

```bash
# Make scripts executable
chmod +x setup.sh test.sh

# Run setup (this will prompt for admin credentials)
./setup.sh

# The setup script will:
# 1. Create Python virtual environment
# 2. Install all dependencies
# 3. Initialize database
# 4. Create admin user
# 5. Create test server with API key
# 6. Configure agent with API key
```

## Manual Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create configuration
cp .env.example .env
# Edit .env if needed (defaults work for testing)

# Initialize database
python scripts/init_db.py

# Create admin user
python scripts/create_admin.py

# Create test server
python scripts/create_test_server.py
# IMPORTANT: Copy the API key shown!
```

### 2. Agent Setup

```bash
cd agent

# Install dependencies
pip install -r requirements.txt

# Create configuration
cp config.yaml.example config.yaml

# Edit config.yaml and add:
# - backend.url: http://localhost:8000
# - backend.api_key: <API key from test server>
```

## Running the System

### Terminal 1: Start Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
INFO:     Scheduler started
```

### Terminal 2: Run Agent

```bash
cd agent
python3 agent.py
```

You should see:
```
INFO - Initializing Monitoring Agent
INFO - Agent started
INFO - Metrics sent successfully
```

### Terminal 3: Test the System

```bash
./test.sh
```

## Verify It's Working

### 1. Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "healthy"}
```

### 2. Check API Documentation

Open browser to: `http://localhost:8000/docs`

You'll see the interactive API documentation.

### 3. Login and Get Token

```bash
# Get access token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=YOUR_PASSWORD"
```

Response:
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

### 4. Check System Stats

```bash
# Use the token from above
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/system/stats
```

Response:
```json
{
  "total_servers": 1,
  "servers_online": 1,
  "servers_offline": 0,
  "active_alerts": 0,
  "critical_alerts": 0
}
```

### 5. List Servers

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/servers
```

You should see your test server with current metrics.

### 6. Check Reports

```bash
# Wait 5 minutes for first automatic report, or generate manually:
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/reports/generate" \
  -H "Content-Type: application/json" \
  -d '{}'

# List reports
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/reports
```

## Real-Time Monitoring Test

Let the system run for 10-15 minutes and observe:

1. **Agent behavior:**
   - Collects metrics every 5 minutes
   - Sends heartbeat every minute
   - Stores metrics locally if backend is down

2. **Backend behavior:**
   - Receives and stores metrics
   - Evaluates alerts every minute
   - Generates reports every 5 minutes
   - Updates server status

3. **Check logs:**
   ```bash
   # Backend logs (in Terminal 1)
   # You'll see: "Processed metric for server..."
   
   # Agent logs (in Terminal 2)
   # You'll see: "Metrics sent successfully"
   ```

## Create Alert Rules

```bash
# Create a CPU alert rule
curl -X POST -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:8000/api/v1/alert-rules" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "High CPU Usage",
    "metric_name": "cpu_usage_percent",
    "condition": "gt",
    "threshold_warning": 70,
    "threshold_critical": 90,
    "duration_minutes": 5,
    "enabled": true
  }'
```

## Simulate High Load (Optional)

To test alerting, create artificial load:

```bash
# CPU stress
yes > /dev/null &
PID=$!

# Wait for metrics collection and alert evaluation
sleep 120

# Stop stress
kill $PID

# Check alerts
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/alerts/alerts
```

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
lsof -i :8000

# Check database
cd backend
source venv/bin/activate
python -c "from app.db.session import engine; print(engine.url)"
```

### Agent can't connect

```bash
# Verify backend is running
curl http://localhost:8000/health

# Check agent config
cat agent/config.yaml

# Test with verbose logging
cd agent
python3 agent.py
# Watch for connection errors
```

### No metrics showing up

```bash
# Check server was registered
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/v1/servers

# Check agent logs
# Look for "Metrics sent successfully"

# Check backend logs
# Look for "Processed metric for server"
```

## Next Steps

1. **Add more servers:** Run `scripts/create_test_server.py` for each server
2. **Set up alert rules:** Define thresholds for your environment
3. **Configure email:** Edit `.env` SMTP settings for email alerts
4. **Review reports:** Check auto-generated reports in `backend/reports/`
5. **Production deployment:** Use Docker or systemd (see main README.md)

## Success Criteria

✅ Backend starts without errors
✅ Agent connects and sends metrics
✅ Metrics appear in API responses
✅ Reports are generated every 5 minutes
✅ Alerts are evaluated every minute
✅ Server status updates correctly

If all checks pass, your system is fully functional and monitoring in real-time!

## Quick Commands Reference

```bash
# Start backend
cd backend && source venv/bin/activate && python main.py

# Run agent
cd agent && python3 agent.py

# Test system
./test.sh

# View logs
tail -f backend/logs/app.log
tail -f agent/agent.log

# Check database
cd backend && source venv/bin/activate
python -c "from app.db.session import SessionLocal; from app.db.models import *; \
db = SessionLocal(); print(f'Servers: {db.query(Server).count()}'); \
print(f'Metrics: {db.query(MetricData).count()}'); \
print(f'Alerts: {db.query(Alert).count()}'); \
print(f'Reports: {db.query(Report).count()}')"
```
