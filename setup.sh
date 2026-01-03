#!/bin/bash

# Complete Setup and Test Script for Monitix

set -e

echo "╔════════════════════════════════════════════════════╗"
echo "║   Monitix - Server Monitoring System Setup       ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    echo -e "${GREEN}✓ Python 3 found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found. Please install Python 3.9+${NC}"
    exit 1
fi

# Setup Backend
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Setting up Backend"
echo "═══════════════════════════════════════════════════"
echo ""

cd backend

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Create .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
python scripts/init_db.py
echo -e "${GREEN}✓ Database initialized${NC}"

# Create admin user
echo ""
echo -e "${YELLOW}Creating admin user...${NC}"
echo "Please enter admin credentials:"
python scripts/create_admin.py

# Create test server
echo ""
echo -e "${YELLOW}Creating test server for testing...${NC}"
python scripts/create_test_server.py > test_server_config.txt

echo -e "${GREEN}✓ Test server created${NC}"
echo -e "${YELLOW}API key saved to: backend/test_server_config.txt${NC}"

cd ..

# Setup Agent
echo ""
echo "═══════════════════════════════════════════════════"
echo "  Setting up Agent"
echo "═══════════════════════════════════════════════════"
echo ""

cd agent

# Install agent dependencies
echo -e "${YELLOW}Installing agent dependencies...${NC}"
pip install -r requirements.txt > /dev/null 2>&1
echo -e "${GREEN}✓ Agent dependencies installed${NC}"

# Create config file
if [ ! -f config.yaml ]; then
    echo -e "${YELLOW}Creating agent config.yaml...${NC}"
    cp config.yaml.example config.yaml
    
    # Extract API key from test server config
    if [ -f ../backend/test_server_config.txt ]; then
        API_KEY=$(grep "api_key:" ../backend/test_server_config.txt | tail -1 | awk '{print $2}')
        if [ ! -z "$API_KEY" ]; then
            sed -i "s/YOUR_API_KEY_HERE/$API_KEY/g" config.yaml
            sed -i "s|http://localhost:8000|http://127.0.0.1:8000|g" config.yaml
            echo -e "${GREEN}✓ Agent config created and API key configured${NC}"
        fi
    fi
fi

cd ..

# Summary
echo ""
echo "╔════════════════════════════════════════════════════╗"
echo "║              Setup Complete!                      ║"
echo "╚════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo ""
echo "1. Start the backend:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "2. In a new terminal, test the agent:"
echo "   cd agent"
echo "   python3 agent.py"
echo ""
echo "3. Access the API:"
echo "   http://localhost:8000/docs"
echo ""
echo "4. Check health:"
echo "   curl http://localhost:8000/health"
echo ""
echo -e "${GREEN}Ready to test!${NC}"
