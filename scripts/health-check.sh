#!/bin/bash
# =============================================================================
# GUARDIAN Health Check Script
# Comprehensive health monitoring for GUARDIAN services
# =============================================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
BASE_URL="${BASE_URL:-http://localhost:8000}"
TIMEOUT="${TIMEOUT:-30}"
VERBOSE="${VERBOSE:-false}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-text}"  # text, json, prometheus
ALERT_THRESHOLD="${ALERT_THRESHOLD:-80}"  # Percentage for warnings

# Health check endpoints
HEALTH_ENDPOINTS=(
    "/api/health"
    "/api/health/detailed" 
    "/api/health/dependencies"
)

# Service ports to check
SERVICE_PORTS=(
    "8000"  # GUARDIAN API
    "6379"  # Redis (if exposed)
    "9090"  # Prometheus (if enabled)
    "3000"  # Grafana (if enabled)
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Health check results
HEALTH_RESULTS=()

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [[ "$OUTPUT_FORMAT" == "text" ]]; then
        echo -e "${timestamp} [${level}] ${message}"
    fi
}

log_info() {
    log "INFO" "${BLUE}$*${NC}"
}

log_warn() {
    log "WARN" "${YELLOW}$*${NC}"
}

log_error() {
    log "ERROR" "${RED}$*${NC}"
}

log_success() {
    log "SUCCESS" "${GREEN}$*${NC}"
}

verbose_log() {
    if [[ "$VERBOSE" == "true" ]]; then
        log_info "$@"
    fi
}

# =============================================================================
# Health Check Functions
# =============================================================================

check_http_endpoint() {
    local url="$1"
    local timeout="${2:-$TIMEOUT}"
    
    verbose_log "Checking HTTP endpoint: $url"
    
    local response
    local http_code
    local response_time
    
    response=$(curl -s -w "%{http_code},%{time_total}" -m "$timeout" "$url" 2>/dev/null || echo "000,0")
    http_code=$(echo "$response" | tail -n1 | cut -d',' -f1)
    response_time=$(echo "$response" | tail -n1 | cut -d',' -f2)
    
    if [[ "$http_code" == "200" ]]; then
        verbose_log "✓ $url (${response_time}s)"
        echo "healthy,$response_time"
    elif [[ "$http_code" == "000" ]]; then
        verbose_log "✗ $url (connection failed)"
        echo "failed,0"
    else
        verbose_log "⚠ $url (HTTP $http_code)"
        echo "degraded,$response_time"
    fi
}

check_tcp_port() {
    local port="$1"
    local host="${2:-localhost}"
    local timeout="${3:-5}"
    
    verbose_log "Checking TCP port: $host:$port"
    
    if timeout "$timeout" bash -c "echo >/dev/tcp/$host/$port" 2>/dev/null; then
        verbose_log "✓ Port $port is open"
        echo "open"
    else
        verbose_log "✗ Port $port is closed or unreachable"
        echo "closed"
    fi
}

check_docker_services() {
    verbose_log "Checking Docker services..."
    
    local healthy_count=0
    local total_count=0
    local services_status=""
    
    if command -v docker >/dev/null 2>&1; then
        cd "$PROJECT_DIR"
        
        # Get service status
        local services=$(docker-compose -f docker-compose.yml -f docker-compose.prod.yml ps --format json 2>/dev/null || echo "[]")
        
        if [[ "$services" != "[]" && -n "$services" ]]; then
            while IFS= read -r service; do
                if [[ -n "$service" ]]; then
                    local name=$(echo "$service" | jq -r '.Name // .Service' 2>/dev/null || echo "unknown")
                    local state=$(echo "$service" | jq -r '.State // .Status' 2>/dev/null || echo "unknown")
                    local health=$(echo "$service" | jq -r '.Health // "unknown"' 2>/dev/null || echo "unknown")
                    
                    ((total_count++))
                    
                    if [[ "$state" == "running" ]] && [[ "$health" == "healthy" || "$health" == "unknown" ]]; then
                        ((healthy_count++))
                        services_status+="$name:healthy,"
                        verbose_log "✓ Service $name is running"
                    else
                        services_status+="$name:$state,"
                        verbose_log "✗ Service $name is $state (health: $health)"
                    fi
                fi
            done <<< "$(echo "$services" | jq -c '.[]' 2>/dev/null || echo "")"
        fi
    else
        verbose_log "Docker not available"
        return 1
    fi
    
    echo "$healthy_count,$total_count,$services_status"
}

check_disk_usage() {
    verbose_log "Checking disk usage..."
    
    local guardian_dirs=(
        "/opt/guardian/storage"
        "/opt/guardian/logs"
        "/opt/guardian/redis"
        "/opt/guardian/backups"
    )
    
    local max_usage=0
    local usage_details=""
    
    for dir in "${guardian_dirs[@]}"; do
        if [[ -d "$dir" ]]; then
            local usage=$(df "$dir" | tail -1 | awk '{print $5}' | sed 's/%//')
            usage_details+="$dir:${usage}%,"
            
            if [[ $usage -gt $max_usage ]]; then
                max_usage=$usage
            fi
            
            if [[ $usage -gt $ALERT_THRESHOLD ]]; then
                verbose_log "⚠ High disk usage in $dir: ${usage}%"
            else
                verbose_log "✓ Disk usage in $dir: ${usage}%"
            fi
        fi
    done
    
    echo "$max_usage,$usage_details"
}

check_memory_usage() {
    verbose_log "Checking memory usage..."
    
    local total_mem=$(free | grep '^Mem:' | awk '{print $2}')
    local used_mem=$(free | grep '^Mem:' | awk '{print $3}')
    local usage_percent=$(( (used_mem * 100) / total_mem ))
    
    if [[ $usage_percent -gt $ALERT_THRESHOLD ]]; then
        verbose_log "⚠ High memory usage: ${usage_percent}%"
    else
        verbose_log "✓ Memory usage: ${usage_percent}%"
    fi
    
    echo "$usage_percent"
}

check_api_functionality() {
    verbose_log "Checking API functionality..."
    
    local functional_tests=(
        "$BASE_URL/docs/endpoints"
        "$BASE_URL/api/health/detailed"
    )
    
    local passed=0
    local total=${#functional_tests[@]}
    
    for endpoint in "${functional_tests[@]}"; do
        local result=$(check_http_endpoint "$endpoint" 10)
        local status=$(echo "$result" | cut -d',' -f1)
        
        if [[ "$status" == "healthy" ]]; then
            ((passed++))
        fi
    done
    
    echo "$passed,$total"
}

get_system_metrics() {
    local cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F% '{print $1}' | tr -d ' ' || echo "0")
    local load_avg=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | tr -d ',' || echo "0")
    local disk_io=$(iostat -d 1 1 2>/dev/null | tail -n+4 | awk '{sum += $4} END {print sum}' || echo "0")
    
    echo "$cpu_usage,$load_avg,$disk_io"
}

# =============================================================================
# Output Formatters
# =============================================================================

output_text_summary() {
    local overall_status="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo
    echo "==============================================="
    echo "GUARDIAN Health Check Summary"
    echo "Time: $timestamp"
    echo "Status: $overall_status"
    echo "==============================================="
    
    # Display results
    for result in "${HEALTH_RESULTS[@]}"; do
        echo "$result"
    done
    
    echo "==============================================="
}

output_json_summary() {
    local overall_status="$1"
    local timestamp=$(date -Iseconds)
    
    cat << EOF
{
    "timestamp": "$timestamp",
    "overall_status": "$overall_status",
    "base_url": "$BASE_URL",
    "checks": {
EOF
    
    local first=true
    for result in "${HEALTH_RESULTS[@]}"; do
        if [[ "$first" == "true" ]]; then
            first=false
        else
            echo ","
        fi
        echo "        $result"
    done
    
    cat << EOF
    }
}
EOF
}

output_prometheus_metrics() {
    local overall_status="$1"
    local timestamp=$(date +%s)
    
    # Convert status to numeric
    local status_value=0
    case "$overall_status" in
        "HEALTHY") status_value=1 ;;
        "DEGRADED") status_value=0.5 ;;
        "UNHEALTHY") status_value=0 ;;
    esac
    
    echo "# HELP guardian_health_status Overall health status of GUARDIAN system"
    echo "# TYPE guardian_health_status gauge"
    echo "guardian_health_status $status_value $timestamp"
    
    # Add individual metrics from health results
    for result in "${HEALTH_RESULTS[@]}"; do
        # Parse and convert results to Prometheus format
        # This would need to be expanded based on actual result format
        echo "# Additional metrics would be added here"
    done
}

# =============================================================================
# Main Health Check Logic
# =============================================================================

run_health_checks() {
    local overall_status="HEALTHY"
    local failed_checks=0
    local total_checks=0
    
    # Check HTTP endpoints
    for endpoint in "${HEALTH_ENDPOINTS[@]}"; do
        local url="$BASE_URL$endpoint"
        local result=$(check_http_endpoint "$url")
        local status=$(echo "$result" | cut -d',' -f1)
        local response_time=$(echo "$result" | cut -d',' -f2)
        
        ((total_checks++))
        
        if [[ "$status" == "healthy" ]]; then
            HEALTH_RESULTS+=("\"endpoint_${endpoint//\//_}\": {\"status\": \"healthy\", \"response_time\": $response_time}")
        else
            HEALTH_RESULTS+=("\"endpoint_${endpoint//\//_}\": {\"status\": \"$status\", \"response_time\": $response_time}")
            ((failed_checks++))
            if [[ "$status" == "failed" ]]; then
                overall_status="UNHEALTHY"
            elif [[ "$overall_status" == "HEALTHY" ]]; then
                overall_status="DEGRADED"
            fi
        fi
    done
    
    # Check TCP ports
    for port in "${SERVICE_PORTS[@]}"; do
        local result=$(check_tcp_port "$port")
        ((total_checks++))
        
        if [[ "$result" == "open" ]]; then
            HEALTH_RESULTS+=("\"port_$port\": {\"status\": \"open\"}")
        else
            HEALTH_RESULTS+=("\"port_$port\": {\"status\": \"closed\"}")
            ((failed_checks++))
            if [[ "$overall_status" == "HEALTHY" ]]; then
                overall_status="DEGRADED"
            fi
        fi
    done
    
    # Check Docker services
    local docker_result=$(check_docker_services)
    if [[ $? -eq 0 ]]; then
        local healthy_services=$(echo "$docker_result" | cut -d',' -f1)
        local total_services=$(echo "$docker_result" | cut -d',' -f2)
        
        HEALTH_RESULTS+=("\"docker_services\": {\"healthy\": $healthy_services, \"total\": $total_services}")
        
        if [[ $healthy_services -lt $total_services ]]; then
            ((failed_checks++))
            if [[ $healthy_services -eq 0 ]]; then
                overall_status="UNHEALTHY"
            elif [[ "$overall_status" == "HEALTHY" ]]; then
                overall_status="DEGRADED"
            fi
        fi
    else
        HEALTH_RESULTS+=("\"docker_services\": {\"status\": \"unavailable\"}")
    fi
    
    # Check disk usage
    local disk_result=$(check_disk_usage)
    local max_disk_usage=$(echo "$disk_result" | cut -d',' -f1)
    
    HEALTH_RESULTS+=("\"disk_usage\": {\"max_usage_percent\": $max_disk_usage}")
    
    if [[ $max_disk_usage -gt $ALERT_THRESHOLD ]]; then
        if [[ "$overall_status" == "HEALTHY" ]]; then
            overall_status="DEGRADED"
        fi
    fi
    
    # Check memory usage
    local memory_usage=$(check_memory_usage)
    HEALTH_RESULTS+=("\"memory_usage\": {\"usage_percent\": $memory_usage}")
    
    if [[ $memory_usage -gt $ALERT_THRESHOLD ]]; then
        if [[ "$overall_status" == "HEALTHY" ]]; then
            overall_status="DEGRADED"
        fi
    fi
    
    # Check API functionality
    local api_result=$(check_api_functionality)
    local passed_tests=$(echo "$api_result" | cut -d',' -f1)
    local total_tests=$(echo "$api_result" | cut -d',' -f2)
    
    HEALTH_RESULTS+=("\"api_functionality\": {\"passed\": $passed_tests, \"total\": $total_tests}")
    
    if [[ $passed_tests -lt $total_tests ]]; then
        if [[ $passed_tests -eq 0 ]]; then
            overall_status="UNHEALTHY"
        elif [[ "$overall_status" == "HEALTHY" ]]; then
            overall_status="DEGRADED"
        fi
    fi
    
    # Get system metrics
    local metrics=$(get_system_metrics)
    local cpu_usage=$(echo "$metrics" | cut -d',' -f1)
    local load_avg=$(echo "$metrics" | cut -d',' -f2)
    
    HEALTH_RESULTS+=("\"system_metrics\": {\"cpu_usage\": $cpu_usage, \"load_average\": $load_avg}")
    
    echo "$overall_status"
}

# =============================================================================
# Main Function
# =============================================================================

main() {
    local overall_status
    
    if [[ "$OUTPUT_FORMAT" == "text" ]]; then
        log_info "Starting GUARDIAN health check..."
        log_info "Base URL: $BASE_URL"
        log_info "Timeout: ${TIMEOUT}s"
    fi
    
    # Run all health checks
    overall_status=$(run_health_checks)
    
    # Output results in requested format
    case "$OUTPUT_FORMAT" in
        "json")
            output_json_summary "$overall_status"
            ;;
        "prometheus")
            output_prometheus_metrics "$overall_status"
            ;;
        "text"|*)
            output_text_summary "$overall_status"
            ;;
    esac
    
    # Set exit code based on overall status
    case "$overall_status" in
        "HEALTHY")
            exit 0
            ;;
        "DEGRADED")
            exit 1
            ;;
        "UNHEALTHY")
            exit 2
            ;;
        *)
            exit 3
            ;;
    esac
}

# =============================================================================
# Command Line Interface
# =============================================================================

show_usage() {
    cat << EOF
GUARDIAN Health Check Script

Usage: $0 [OPTIONS]

Options:
    --base-url URL         Base URL for health checks (default: http://localhost:8000)
    --timeout SECONDS      Timeout for HTTP requests (default: 30)
    --format FORMAT        Output format: text, json, prometheus (default: text)
    --verbose              Enable verbose output
    --alert-threshold PCT  Alert threshold percentage (default: 80)
    --help                 Show this help message

Examples:
    $0                                      # Basic health check
    $0 --verbose                            # Verbose output
    $0 --format json                        # JSON output
    $0 --base-url https://api.example.com   # Custom URL
    $0 --format prometheus > metrics.txt    # Export metrics

Exit Codes:
    0 - HEALTHY      All checks passed
    1 - DEGRADED     Some checks failed, system partially functional
    2 - UNHEALTHY    Critical failures, system not functional
    3 - ERROR        Script error or unknown status

Environment Variables:
    BASE_URL              Base URL for API
    TIMEOUT               HTTP timeout in seconds
    VERBOSE               Enable verbose output (true/false)
    OUTPUT_FORMAT         Output format (text/json/prometheus)
    ALERT_THRESHOLD       Alert threshold percentage

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --base-url)
            BASE_URL="$2"
            shift 2
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --format)
            OUTPUT_FORMAT="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE="true"
            shift
            ;;
        --alert-threshold)
            ALERT_THRESHOLD="$2"
            shift 2
            ;;
        --help|-h)
            show_usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Validate output format
case "$OUTPUT_FORMAT" in
    "text"|"json"|"prometheus")
        # Valid format
        ;;
    *)
        log_error "Invalid output format: $OUTPUT_FORMAT"
        show_usage
        exit 1
        ;;
esac

# Run main function
main