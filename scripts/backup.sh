#!/bin/bash
# =============================================================================
# GUARDIAN Backup Script
# Automated backup and restore functionality for GUARDIAN data
# =============================================================================

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-/opt/guardian/backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
COMPRESS_BACKUPS="${COMPRESS_BACKUPS:-true}"
VERIFY_BACKUPS="${VERIFY_BACKUPS:-true}"

# Data directories to backup
DATA_DIRS=(
    "/opt/guardian/storage"
    "/opt/guardian/logs"
    "/opt/guardian/redis"
)

# Configuration files to backup
CONFIG_FILES=(
    "$PROJECT_DIR/.env"
    "$PROJECT_DIR/docker-compose.yml"
    "$PROJECT_DIR/docker-compose.prod.yml"
    "$PROJECT_DIR/gunicorn.conf.py"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# =============================================================================
# Utility Functions
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    echo -e "${timestamp} [${level}] ${message}"
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

check_permissions() {
    if [[ ! -w "$(dirname "$BACKUP_DIR")" ]]; then
        log_error "No write permission to backup directory: $(dirname "$BACKUP_DIR")"
        log_info "Try running with sudo or changing BACKUP_DIR"
        exit 1
    fi
}

create_backup() {
    local backup_name="${1:-guardian-$(date +%Y%m%d-%H%M%S)}"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    log_info "Creating backup: $backup_name"
    
    # Create backup directory
    mkdir -p "$backup_path"
    
    # Create metadata file
    cat > "$backup_path/backup_info.json" << EOF
{
    "backup_name": "$backup_name",
    "timestamp": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "guardian_version": "$(get_guardian_version)",
    "backup_type": "full",
    "compressed": $COMPRESS_BACKUPS
}
EOF
    
    # Backup data directories
    for dir in "${DATA_DIRS[@]}"; do
        if [[ -d "$dir" ]]; then
            local dir_name=$(basename "$dir")
            log_info "Backing up data directory: $dir"
            
            if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
                tar -czf "$backup_path/${dir_name}.tar.gz" -C "$(dirname "$dir")" "$dir_name" 2>/dev/null || {
                    log_warn "Failed to backup $dir (may not exist or be empty)"
                }
            else
                cp -r "$dir" "$backup_path/" 2>/dev/null || {
                    log_warn "Failed to backup $dir (may not exist)"
                }
            fi
        else
            log_warn "Data directory not found: $dir"
        fi
    done
    
    # Backup configuration files
    local config_dir="$backup_path/config"
    mkdir -p "$config_dir"
    
    for file in "${CONFIG_FILES[@]}"; do
        if [[ -f "$file" ]]; then
            log_info "Backing up config file: $file"
            cp "$file" "$config_dir/" 2>/dev/null || {
                log_warn "Failed to backup $file"
            }
        else
            log_warn "Config file not found: $file"
        fi
    done
    
    # Backup Docker volumes
    backup_docker_volumes "$backup_path"
    
    # Verify backup if requested
    if [[ "$VERIFY_BACKUPS" == "true" ]]; then
        verify_backup "$backup_path"
    fi
    
    # Calculate backup size
    local backup_size=$(du -sh "$backup_path" | cut -f1)
    
    log_success "Backup created successfully"
    log_info "Backup location: $backup_path"
    log_info "Backup size: $backup_size"
    
    # Update backup info with final size
    local temp_file=$(mktemp)
    jq ". + {\"backup_size\": \"$backup_size\"}" "$backup_path/backup_info.json" > "$temp_file"
    mv "$temp_file" "$backup_path/backup_info.json"
    
    echo "$backup_path"
}

backup_docker_volumes() {
    local backup_path="$1"
    local volumes_dir="$backup_path/docker_volumes"
    
    mkdir -p "$volumes_dir"
    
    log_info "Backing up Docker volumes..."
    
    # Get GUARDIAN-related volumes
    local volumes=$(docker volume ls --filter name=guardian --format "{{.Name}}" 2>/dev/null || true)
    
    for volume in $volumes; do
        if [[ -n "$volume" ]]; then
            log_info "Backing up Docker volume: $volume"
            
            # Create a temporary container to access volume data
            docker run --rm \
                -v "$volume:/volume_data:ro" \
                -v "$volumes_dir:/backup" \
                alpine:latest \
                tar -czf "/backup/${volume}.tar.gz" -C /volume_data . 2>/dev/null || {
                log_warn "Failed to backup volume: $volume"
            }
        fi
    done
}

verify_backup() {
    local backup_path="$1"
    
    log_info "Verifying backup integrity..."
    
    # Check if backup directory exists and is not empty
    if [[ ! -d "$backup_path" ]] || [[ -z "$(ls -A "$backup_path" 2>/dev/null)" ]]; then
        log_error "Backup directory is empty or doesn't exist"
        return 1
    fi
    
    # Verify compressed files if compression is enabled
    if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
        find "$backup_path" -name "*.tar.gz" -exec tar -tzf {} >/dev/null \; || {
            log_error "Backup verification failed: corrupted compressed files"
            return 1
        }
    fi
    
    # Check backup metadata
    if [[ -f "$backup_path/backup_info.json" ]]; then
        jq empty "$backup_path/backup_info.json" 2>/dev/null || {
            log_error "Backup verification failed: corrupted metadata"
            return 1
        }
    fi
    
    log_success "Backup verification passed"
}

restore_backup() {
    local backup_name="$1"
    local backup_path="$BACKUP_DIR/$backup_name"
    
    if [[ ! -d "$backup_path" ]]; then
        log_error "Backup not found: $backup_path"
        exit 1
    fi
    
    log_info "Restoring backup: $backup_name"
    
    # Verify backup before restore
    if [[ "$VERIFY_BACKUPS" == "true" ]]; then
        verify_backup "$backup_path" || {
            log_error "Backup verification failed, aborting restore"
            exit 1
        }
    fi
    
    # Stop services before restore
    log_info "Stopping GUARDIAN services..."
    cd "$PROJECT_DIR"
    docker-compose -f docker-compose.yml -f docker-compose.prod.yml down 2>/dev/null || true
    
    # Restore data directories
    for dir in "${DATA_DIRS[@]}"; do
        local dir_name=$(basename "$dir")
        
        if [[ "$COMPRESS_BACKUPS" == "true" ]]; then
            if [[ -f "$backup_path/${dir_name}.tar.gz" ]]; then
                log_info "Restoring data directory: $dir"
                
                # Create parent directory
                sudo mkdir -p "$(dirname "$dir")"
                
                # Remove existing directory
                sudo rm -rf "$dir"
                
                # Extract backup
                sudo tar -xzf "$backup_path/${dir_name}.tar.gz" -C "$(dirname "$dir")"
            fi
        else
            if [[ -d "$backup_path/$dir_name" ]]; then
                log_info "Restoring data directory: $dir"
                
                # Remove existing directory
                sudo rm -rf "$dir"
                
                # Copy backup
                sudo cp -r "$backup_path/$dir_name" "$dir"
            fi
        fi
    done
    
    # Restore configuration files
    if [[ -d "$backup_path/config" ]]; then
        for file in "${CONFIG_FILES[@]}"; do
            local filename=$(basename "$file")
            if [[ -f "$backup_path/config/$filename" ]]; then
                log_info "Restoring config file: $file"
                cp "$backup_path/config/$filename" "$file"
            fi
        done
    fi
    
    # Restore Docker volumes
    restore_docker_volumes "$backup_path"
    
    # Fix permissions
    sudo chown -R 1000:1000 /opt/guardian/ 2>/dev/null || true
    
    log_success "Backup restored successfully"
    log_info "You can now start the services with: ./scripts/deploy.sh"
}

restore_docker_volumes() {
    local backup_path="$1"
    local volumes_dir="$backup_path/docker_volumes"
    
    if [[ ! -d "$volumes_dir" ]]; then
        return
    fi
    
    log_info "Restoring Docker volumes..."
    
    # Find volume backups
    find "$volumes_dir" -name "*.tar.gz" | while read -r volume_backup; do
        local volume_name=$(basename "$volume_backup" .tar.gz)
        
        log_info "Restoring Docker volume: $volume_name"
        
        # Create volume if it doesn't exist
        docker volume create "$volume_name" >/dev/null 2>&1 || true
        
        # Restore volume data
        docker run --rm \
            -v "$volume_name:/volume_data" \
            -v "$volumes_dir:/backup:ro" \
            alpine:latest \
            tar -xzf "/backup/$(basename "$volume_backup")" -C /volume_data 2>/dev/null || {
            log_warn "Failed to restore volume: $volume_name"
        }
    done
}

list_backups() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        log_info "No backups found (backup directory doesn't exist)"
        return
    fi
    
    log_info "Available backups:"
    
    # Find all backup directories
    find "$BACKUP_DIR" -maxdepth 1 -type d -name "guardian-*" | sort -r | while read -r backup; do
        local backup_name=$(basename "$backup")
        local backup_info="$backup/backup_info.json"
        
        if [[ -f "$backup_info" ]]; then
            local timestamp=$(jq -r '.timestamp // "unknown"' "$backup_info" 2>/dev/null)
            local size=$(jq -r '.backup_size // "unknown"' "$backup_info" 2>/dev/null)
            local version=$(jq -r '.guardian_version // "unknown"' "$backup_info" 2>/dev/null)
            
            printf "  %-25s %s (size: %s, version: %s)\n" "$backup_name" "$timestamp" "$size" "$version"
        else
            local mod_time=$(stat -c %y "$backup" 2>/dev/null | cut -d' ' -f1,2 | cut -d. -f1)
            printf "  %-25s %s (no metadata)\n" "$backup_name" "$mod_time"
        fi
    done
}

cleanup_old_backups() {
    if [[ ! -d "$BACKUP_DIR" ]]; then
        return
    fi
    
    log_info "Cleaning up backups older than $RETENTION_DAYS days..."
    
    local deleted_count=0
    
    # Find and delete old backups
    find "$BACKUP_DIR" -maxdepth 1 -type d -name "guardian-*" -mtime +$RETENTION_DAYS | while read -r backup; do
        local backup_name=$(basename "$backup")
        log_info "Deleting old backup: $backup_name"
        rm -rf "$backup"
        ((deleted_count++))
    done
    
    if [[ $deleted_count -gt 0 ]]; then
        log_success "Deleted $deleted_count old backups"
    else
        log_info "No old backups to delete"
    fi
}

get_guardian_version() {
    # Try to get version from package or git
    if [[ -f "$PROJECT_DIR/backend/version.txt" ]]; then
        cat "$PROJECT_DIR/backend/version.txt"
    elif git -C "$PROJECT_DIR" describe --tags 2>/dev/null; then
        git -C "$PROJECT_DIR" describe --tags
    else
        echo "unknown"
    fi
}

# =============================================================================
# Main Functions
# =============================================================================

show_usage() {
    cat << EOF
GUARDIAN Backup Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    create [NAME]       Create a new backup (optional name)
    restore NAME        Restore from backup
    list               List available backups
    cleanup            Remove old backups
    verify NAME        Verify backup integrity
    help               Show this help message

Options:
    --backup-dir DIR       Backup directory (default: /opt/guardian/backups)
    --retention DAYS       Keep backups for N days (default: 30)
    --compress            Enable compression (default: true)
    --no-compress         Disable compression
    --verify              Verify backups (default: true)
    --no-verify           Skip backup verification

Examples:
    $0 create                           # Create backup with auto-generated name
    $0 create emergency-backup          # Create backup with custom name
    $0 restore guardian-20250625-120000 # Restore specific backup
    $0 list                            # List all backups
    $0 cleanup                         # Remove old backups

Environment Variables:
    BACKUP_DIR              Backup directory path
    RETENTION_DAYS          Backup retention in days
    COMPRESS_BACKUPS        Enable/disable compression (true/false)
    VERIFY_BACKUPS          Enable/disable verification (true/false)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --backup-dir)
            BACKUP_DIR="$2"
            shift 2
            ;;
        --retention)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        --compress)
            COMPRESS_BACKUPS="true"
            shift
            ;;
        --no-compress)
            COMPRESS_BACKUPS="false"
            shift
            ;;
        --verify)
            VERIFY_BACKUPS="true"
            shift
            ;;
        --no-verify)
            VERIFY_BACKUPS="false"
            shift
            ;;
        create)
            COMMAND="create"
            BACKUP_NAME="${2:-}"
            shift
            [[ -n "${2:-}" ]] && shift
            ;;
        restore)
            COMMAND="restore"
            BACKUP_NAME="$2"
            shift 2
            ;;
        list)
            COMMAND="list"
            shift
            ;;
        cleanup)
            COMMAND="cleanup"
            shift
            ;;
        verify)
            COMMAND="verify"
            BACKUP_NAME="$2"
            shift 2
            ;;
        help|--help|-h)
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

# Check permissions
check_permissions

# Execute command
case "${COMMAND:-}" in
    create)
        create_backup "$BACKUP_NAME"
        ;;
    restore)
        if [[ -z "${BACKUP_NAME:-}" ]]; then
            log_error "Backup name required for restore command"
            show_usage
            exit 1
        fi
        restore_backup "$BACKUP_NAME"
        ;;
    list)
        list_backups
        ;;
    cleanup)
        cleanup_old_backups
        ;;
    verify)
        if [[ -z "${BACKUP_NAME:-}" ]]; then
            log_error "Backup name required for verify command"
            show_usage
            exit 1
        fi
        verify_backup "$BACKUP_DIR/$BACKUP_NAME"
        ;;
    "")
        log_error "Command required"
        show_usage
        exit 1
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_usage
        exit 1
        ;;
esac