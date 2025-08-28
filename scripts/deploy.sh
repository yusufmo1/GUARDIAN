#!/bin/bash

# GUARDIAN Deployment Script
# Simple production deployment using Docker Compose

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo "Please create a .env file with the following variables:"
    echo "  POSTGRES_PASSWORD"
    echo "  GOOGLE_CLIENT_ID"
    echo "  GOOGLE_CLIENT_SECRET"
    echo "  SECRET_KEY"
    echo "  SESSION_SECRET"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Function to check if required env vars are set
check_env_vars() {
    local required_vars=("GOOGLE_CLIENT_ID" "GOOGLE_CLIENT_SECRET" "SECRET_KEY" "SESSION_SECRET")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo -e "${RED}Error: Required environment variable $var is not set!${NC}"
            exit 1
        fi
    done
}

# Main deployment function
deploy() {
    echo -e "${GREEN}Starting GUARDIAN deployment...${NC}"
    
    # Check environment variables
    check_env_vars
    
    # Build and start containers
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build --no-cache
    
    echo -e "${YELLOW}Starting services...${NC}"
    docker-compose up -d
    
    # Wait for services to be healthy
    echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
    sleep 10
    
    # Check service health
    if docker-compose ps | grep -q "unhealthy"; then
        echo -e "${RED}Some services are unhealthy!${NC}"
        docker-compose ps
        exit 1
    fi
    
    echo -e "${GREEN}Deployment complete!${NC}"
    echo ""
    echo "Services are running at:"
    echo "  Frontend: http://localhost:3000"
    echo "  Backend API: http://localhost:5051"
    echo "  PostgreSQL: localhost:5432"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
}

# Handle commands
case "$1" in
    "")
        deploy
        ;;
    "down")
        echo -e "${YELLOW}Stopping services...${NC}"
        docker-compose down
        echo -e "${GREEN}Services stopped${NC}"
        ;;
    "logs")
        docker-compose logs -f
        ;;
    "ps")
        docker-compose ps
        ;;
    "restart")
        echo -e "${YELLOW}Restarting services...${NC}"
        docker-compose restart
        echo -e "${GREEN}Services restarted${NC}"
        ;;
    *)
        echo "Usage: $0 [command]"
        echo "Commands:"
        echo "  (empty)   - Deploy the application"
        echo "  down      - Stop all services"
        echo "  logs      - View logs"
        echo "  ps        - Show service status"
        echo "  restart   - Restart all services"
        exit 1
        ;;
esac