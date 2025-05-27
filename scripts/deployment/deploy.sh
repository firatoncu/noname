#!/bin/bash
"""
Deployment script for n0name Trading Bot
Handles deployment to different environments with proper validation
"""

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEPLOY_LOG="$PROJECT_ROOT/logs/deploy.log"

# Default values
ENVIRONMENT="development"
DOCKER_TAG="n0name-trading-bot"
COMPOSE_FILE="docker-compose.yml"
BACKUP_ENABLED="true"
HEALTH_CHECK_TIMEOUT=300
DRY_RUN="false"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "INFO")
            echo -e "${GREEN}[INFO]${NC} $message"
            ;;
        "WARN")
            echo -e "${YELLOW}[WARN]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "DEBUG")
            echo -e "${BLUE}[DEBUG]${NC} $message"
            ;;
    esac
    
    # Log to file
    mkdir -p "$(dirname "$DEPLOY_LOG")"
    echo "[$timestamp] [$level] $message" >> "$DEPLOY_LOG"
}

# Error handler
error_exit() {
    log "ERROR" "$1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "INFO" "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed or not in PATH"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed or not in PATH"
    fi
    
    # Check if required files exist
    if [[ ! -f "$PROJECT_ROOT/$COMPOSE_FILE" ]]; then
        error_exit "Docker Compose file not found: $COMPOSE_FILE"
    fi
    
    # Check if environment file exists
    if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
        log "WARN" ".env file not found, using environment variables"
    fi
    
    log "INFO" "Prerequisites check passed"
}

# Validate environment
validate_environment() {
    log "INFO" "Validating environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        "development"|"staging"|"production")
            log "INFO" "Environment validation passed"
            ;;
        *)
            error_exit "Invalid environment: $ENVIRONMENT. Must be development, staging, or production"
            ;;
    esac
    
    # Set compose file based on environment
    if [[ "$ENVIRONMENT" == "development" ]]; then
        COMPOSE_FILE="docker-compose.dev.yml"
    fi
}

# Create backup
create_backup() {
    if [[ "$BACKUP_ENABLED" == "true" ]]; then
        log "INFO" "Creating backup..."
        
        local backup_dir="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$backup_dir"
        
        # Backup database
        if docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" ps postgres | grep -q "Up"; then
            log "INFO" "Backing up database..."
            docker-compose -f "$PROJECT_ROOT/$COMPOSE_FILE" exec -T postgres pg_dump -U n0name n0name_trading > "$backup_dir/database.sql"
        fi
        
        # Backup configuration
        if [[ -d "$PROJECT_ROOT/config" ]]; then
            cp -r "$PROJECT_ROOT/config" "$backup_dir/"
        fi
        
        # Backup data directory
        if [[ -d "$PROJECT_ROOT/data" ]]; then
            cp -r "$PROJECT_ROOT/data" "$backup_dir/"
        fi
        
        log "INFO" "Backup created at: $backup_dir"
    else
        log "INFO" "Backup disabled, skipping..."
    fi
}

# Build images
build_images() {
    log "INFO" "Building Docker images..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would build images with tag: $DOCKER_TAG"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # Build the main application image
    docker build -t "$DOCKER_TAG:latest" .
    
    # Tag with environment
    docker tag "$DOCKER_TAG:latest" "$DOCKER_TAG:$ENVIRONMENT"
    
    log "INFO" "Images built successfully"
}

# Deploy services
deploy_services() {
    log "INFO" "Deploying services..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would deploy using $COMPOSE_FILE"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # Pull latest images for external services
    docker-compose -f "$COMPOSE_FILE" pull postgres redis influxdb grafana nginx
    
    # Deploy services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    log "INFO" "Services deployed successfully"
}

# Health check
health_check() {
    log "INFO" "Performing health checks..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would perform health checks"
        return
    fi
    
    local timeout=$HEALTH_CHECK_TIMEOUT
    local interval=10
    local elapsed=0
    
    while [[ $elapsed -lt $timeout ]]; do
        # Check if main application is healthy
        if curl -f -s http://localhost:8080/health > /dev/null 2>&1; then
            log "INFO" "Application health check passed"
            return 0
        fi
        
        log "INFO" "Waiting for application to be healthy... ($elapsed/$timeout seconds)"
        sleep $interval
        elapsed=$((elapsed + interval))
    done
    
    error_exit "Health check failed after $timeout seconds"
}

# Rollback function
rollback() {
    log "WARN" "Rolling back deployment..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would rollback deployment"
        return
    fi
    
    cd "$PROJECT_ROOT"
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore from backup if available
    local latest_backup=$(ls -t "$PROJECT_ROOT/backups" 2>/dev/null | head -n1)
    if [[ -n "$latest_backup" ]]; then
        log "INFO" "Restoring from backup: $latest_backup"
        
        # Restore database
        if [[ -f "$PROJECT_ROOT/backups/$latest_backup/database.sql" ]]; then
            docker-compose -f "$COMPOSE_FILE" up -d postgres
            sleep 10
            docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U n0name -d n0name_trading < "$PROJECT_ROOT/backups/$latest_backup/database.sql"
        fi
        
        # Restore configuration
        if [[ -d "$PROJECT_ROOT/backups/$latest_backup/config" ]]; then
            rm -rf "$PROJECT_ROOT/config"
            cp -r "$PROJECT_ROOT/backups/$latest_backup/config" "$PROJECT_ROOT/"
        fi
    fi
    
    log "INFO" "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log "INFO" "Cleaning up old resources..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log "INFO" "DRY RUN: Would cleanup old resources"
        return
    fi
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove old backups (keep last 5)
    if [[ -d "$PROJECT_ROOT/backups" ]]; then
        cd "$PROJECT_ROOT/backups"
        ls -t | tail -n +6 | xargs -r rm -rf
    fi
    
    log "INFO" "Cleanup completed"
}

# Show usage
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy n0name Trading Bot to specified environment

OPTIONS:
    -e, --environment ENV    Target environment (development|staging|production) [default: development]
    -t, --tag TAG           Docker image tag [default: n0name-trading-bot]
    -f, --compose-file FILE Docker Compose file [default: auto-detected]
    --no-backup             Disable backup creation
    --timeout SECONDS       Health check timeout [default: 300]
    --dry-run               Show what would be done without executing
    --rollback              Rollback to previous deployment
    -h, --help              Show this help message

EXAMPLES:
    $0 -e production -t v1.0.0
    $0 --environment staging --no-backup
    $0 --dry-run -e production
    $0 --rollback

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                DOCKER_TAG="$2"
                shift 2
                ;;
            -f|--compose-file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            --no-backup)
                BACKUP_ENABLED="false"
                shift
                ;;
            --timeout)
                HEALTH_CHECK_TIMEOUT="$2"
                shift 2
                ;;
            --dry-run)
                DRY_RUN="true"
                shift
                ;;
            --rollback)
                rollback
                exit 0
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                error_exit "Unknown option: $1"
                ;;
        esac
    done
}

# Main deployment function
main() {
    log "INFO" "Starting deployment process..."
    log "INFO" "Environment: $ENVIRONMENT"
    log "INFO" "Docker tag: $DOCKER_TAG"
    log "INFO" "Compose file: $COMPOSE_FILE"
    log "INFO" "Dry run: $DRY_RUN"
    
    # Trap errors and rollback
    trap 'log "ERROR" "Deployment failed, initiating rollback..."; rollback; exit 1' ERR
    
    check_prerequisites
    validate_environment
    create_backup
    build_images
    deploy_services
    health_check
    cleanup
    
    log "INFO" "Deployment completed successfully!"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    parse_args "$@"
    main
fi 