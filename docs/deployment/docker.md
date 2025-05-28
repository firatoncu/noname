# n0name Trading Bot - Deployment Guide

This guide covers the deployment and distribution system for the n0name Trading Bot, including Docker containers, environment-specific configurations, and automated build processes.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Docker Deployment](#docker-deployment)
- [Build System](#build-system)
- [CI/CD Pipeline](#cicd-pipeline)
- [Environment Configurations](#environment-configurations)
- [Monitoring and Logging](#monitoring-and-logging)
- [Troubleshooting](#troubleshooting)

## Overview

The n0name Trading Bot deployment system provides:

- **Multi-stage Docker builds** for optimized production images
- **Environment-specific configurations** (development, staging, production)
- **Automated build processes** with PyInstaller for standalone executables
- **CI/CD pipeline** with GitHub Actions
- **Comprehensive monitoring** with Grafana and InfluxDB
- **Security-focused** deployment with proper secrets management

## Prerequisites

### System Requirements

- **Docker** 20.10+ and Docker Compose 2.0+
- **Python** 3.9+ (for local development)
- **Git** for version control
- **Make** (optional, for convenience commands)

### Development Tools

```bash
# Install development dependencies
pip install -e .[dev,performance,monitoring]

# Install pre-commit hooks
pre-commit install
```

## Environment Setup

### 1. Environment Variables

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your actual configuration:

```bash
# Required: Binance API credentials
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret

# Required: Database passwords
DB_PASSWORD=secure_password
REDIS_PASSWORD=secure_password

# Optional: Notification settings
TELEGRAM_BOT_TOKEN=your_bot_token
EMAIL_USERNAME=your_email@domain.com
```

### 2. SSL Certificates (Production)

For production deployment, generate SSL certificates:

```bash
# Create SSL directory
mkdir -p config/nginx/ssl

# Generate self-signed certificate (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout config/nginx/ssl/key.pem \
  -out config/nginx/ssl/cert.pem

# Or use Let's Encrypt for production
certbot certonly --standalone -d yourdomain.com
```

## Docker Deployment

### Development Environment

Start the development environment with hot reloading:

```bash
# Start development services
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f n0name-bot-dev

# Access Jupyter notebook
open http://localhost:8888
```

### Production Environment

Deploy to production:

```bash
# Build and start production services
docker-compose up -d

# Check service health
docker-compose ps
docker-compose logs n0name-bot
```

### Using the Deployment Script

The automated deployment script provides comprehensive deployment management:

```bash
# Development deployment
./scripts/deploy.sh -e development

# Production deployment with specific tag
./scripts/deploy.sh -e production -t v2.0.0

# Dry run to see what would happen
./scripts/deploy.sh --dry-run -e production

# Rollback to previous deployment
./scripts/deploy.sh --rollback
```

#### Deployment Script Options

```bash
Usage: ./scripts/deploy.sh [OPTIONS]

OPTIONS:
    -e, --environment ENV    Target environment (development|staging|production)
    -t, --tag TAG           Docker image tag
    -f, --compose-file FILE Docker Compose file
    --no-backup             Disable backup creation
    --timeout SECONDS       Health check timeout
    --dry-run               Show what would be done without executing
    --rollback              Rollback to previous deployment
    -h, --help              Show help message
```

## Build System

### Automated Build Script

The build system supports multiple build types:

```bash
# Development build
python scripts/build.py --type dev

# Production wheel package
python scripts/build.py --type prod --test --lint

# Standalone executable
python scripts/build.py --type exe --onefile

# Docker image
python scripts/build.py --type docker --docker-tag n0name:latest

# Complete release build
python scripts/build.py --type release --version 2.0.0
```

### Manual Building

#### Docker Images

```bash
# Build production image
docker build --target production -t n0name-trading-bot:latest .

# Build development image
docker build --target development -t n0name-trading-bot:dev .
```

#### Python Package

```bash
# Build wheel package
python -m build

# Install locally
pip install -e .
```

#### Standalone Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build executable
pyinstaller build/n0name.spec
```

## CI/CD Pipeline

### GitHub Actions Workflow

The CI/CD pipeline automatically:

1. **Tests** code on multiple Python versions
2. **Builds** Docker images and executables
3. **Scans** for security vulnerabilities
4. **Deploys** to staging/production environments
5. **Monitors** deployment health

### Workflow Triggers

- **Push to main**: Full pipeline with production deployment
- **Push to develop**: Pipeline with staging deployment
- **Pull requests**: Testing and validation only
- **Tags (v*)**: Release pipeline with PyPI publishing

### Required Secrets

Configure these secrets in your GitHub repository:

```bash
# Docker Hub
DOCKER_USERNAME=your_docker_username
DOCKER_PASSWORD=your_docker_password

# PyPI (for releases)
PYPI_API_TOKEN=your_pypi_token

# Deployment
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
```

## Environment Configurations

### Development (`config/development.yml`)

- Paper trading enabled
- Debug logging
- SQLite database
- Memory caching
- Hot reloading
- Test endpoints enabled

### Production (`config/production.yml`)

- Live trading
- PostgreSQL database
- Redis caching
- Comprehensive monitoring
- Security hardening
- Performance optimization

### Configuration Override

Environment variables override configuration files:

```bash
# Override trading capital
export TRADING_CAPITAL=50000.0

# Override log level
export LOG_LEVEL=DEBUG
```

## Monitoring and Logging

### Services

- **Grafana**: Visualization dashboard (http://localhost:3001)
- **InfluxDB**: Time-series database for metrics
- **Nginx**: Reverse proxy with rate limiting
- **Redis**: Caching and session storage

### Health Checks

```bash
# Application health
curl http://localhost:8080/health

# Service status
docker-compose ps

# View logs
docker-compose logs -f n0name-bot
```

### Metrics Collection

The system automatically collects:

- Trading performance metrics
- System resource usage
- API response times
- Error rates and patterns

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

```bash
# Check logs
docker-compose logs n0name-bot

# Check environment variables
docker-compose config

# Restart services
docker-compose restart
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose exec postgres pg_isready

# Reset database
docker-compose down -v
docker-compose up -d postgres
```

#### 3. API Key Issues

```bash
# Verify API keys are set
docker-compose exec n0name-bot env | grep BINANCE

# Test API connection
docker-compose exec n0name-bot python -c "
from binance.client import Client
client = Client(api_key='$BINANCE_API_KEY', api_secret='$BINANCE_API_SECRET')
print(client.get_account())
"
```

#### 4. Build Failures

```bash
# Clean build cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache

# Check disk space
df -h
```

### Performance Optimization

#### 1. Resource Limits

Adjust Docker resource limits in `docker-compose.yml`:

```yaml
services:
  n0name-bot:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

#### 2. Database Tuning

Optimize PostgreSQL settings in `config/postgres.conf`:

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
```

#### 3. Redis Optimization

Tune Redis configuration in `config/redis.conf`:

```ini
maxmemory 512mb
maxmemory-policy allkeys-lru
```

### Security Considerations

#### 1. Secrets Management

- Never commit secrets to version control
- Use environment variables for sensitive data
- Rotate API keys regularly
- Use strong passwords for databases

#### 2. Network Security

- Enable SSL/TLS for all external connections
- Use firewall rules to restrict access
- Implement rate limiting
- Monitor for suspicious activity

#### 3. Container Security

- Run containers as non-root users
- Use minimal base images
- Scan images for vulnerabilities
- Keep dependencies updated

### Backup and Recovery

#### 1. Automated Backups

Backups are created automatically during deployment:

```bash
# Manual backup
./scripts/deploy.sh --environment production --backup-only

# List backups
ls -la backups/
```

#### 2. Recovery Process

```bash
# Stop services
docker-compose down

# Restore from backup
./scripts/deploy.sh --rollback

# Verify restoration
docker-compose logs n0name-bot
```

### Support and Maintenance

#### 1. Log Analysis

```bash
# View application logs
docker-compose logs -f n0name-bot

# Search for errors
docker-compose logs n0name-bot | grep ERROR

# Export logs
docker-compose logs n0name-bot > trading_bot.log
```

#### 2. Performance Monitoring

```bash
# System resources
docker stats

# Database performance
docker-compose exec postgres pg_stat_activity

# Redis metrics
docker-compose exec redis redis-cli info
```

#### 3. Updates and Maintenance

```bash
# Update to latest version
git pull origin main
./scripts/deploy.sh -e production -t latest

# Update dependencies
pip install -e .[dev,performance,monitoring] --upgrade

# Clean old data
docker system prune -a
```

For additional support, please refer to the project documentation or create an issue in the GitHub repository. 