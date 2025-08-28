#!/bin/bash

# Script to kill any process on port 5051 and start the GUARDIAN backend

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Backend port
PORT=5051

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo -e "${YELLOW}GUARDIAN Backend Startup Script${NC}"
echo "================================"

# Check if backend directory exists
if [ ! -d "$BACKEND_DIR" ]; then
    echo -e "${RED}Error: Backend directory not found at $BACKEND_DIR${NC}"
    exit 1
fi

# Kill any process running on port 5051
echo -e "\n${YELLOW}Checking for processes on port $PORT...${NC}"
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${YELLOW}Found process(es) on port $PORT. Killing...${NC}"
    lsof -Pi :$PORT -sTCP:LISTEN -t | xargs kill -9 2>/dev/null || true
    sleep 2
    echo -e "${GREEN}Processes killed${NC}"
else
    echo -e "${GREEN}No processes found on port $PORT${NC}"
fi

# Change to backend directory
cd "$BACKEND_DIR"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}Error: Virtual environment not found at $BACKEND_DIR/.venv${NC}"
    echo -e "${YELLOW}Please create it with: python -m venv .venv${NC}"
    exit 1
fi

# Activate virtual environment
echo -e "\n${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Check if requirements are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python -c "import flask" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}Warning: .env file not found!${NC}"
    echo -e "${YELLOW}Copy .env.example to .env and configure it:${NC}"
    echo -e "  cp .env.example .env"
    echo -e "${YELLOW}Continuing with default configuration...${NC}"
fi

# Start the backend
echo -e "\n${GREEN}Starting GUARDIAN backend on port $PORT...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}\n"

# Export environment variables
export FLASK_ENV=${FLASK_ENV:-development}
export API_PORT=$PORT

# Run the backend as a module from the project root
cd "$PROJECT_ROOT"

# Enable detailed logging
export PYTHONUNBUFFERED=1
export FLASK_DEBUG=1
export LOG_LEVEL=DEBUG

# Run with explicit error output
python -m backend.main 2>&1 | tee backend-debug.log