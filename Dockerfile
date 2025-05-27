# Multi-stage Dockerfile for n0name Trading Bot
# Stage 1: Build stage
FROM python:3.11-slim as builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-performance.txt ./
COPY pyproject.toml setup.py ./

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt && \
    pip install -r requirements-performance.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/
COPY n0name.py ./

# Install the package
RUN pip install -e .

# Stage 2: Production stage
FROM python:3.11-slim as production

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.local/bin:$PATH" \
    ENVIRONMENT=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd -r n0name && useradd -r -g n0name -d /app -s /bin/bash n0name

# Create necessary directories
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R n0name:n0name /app

# Set working directory
WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application files
COPY --from=builder --chown=n0name:n0name /app/src ./src
COPY --from=builder --chown=n0name:n0name /app/config ./config
COPY --from=builder --chown=n0name:n0name /app/n0name.py ./

# Copy additional configuration files
COPY --chown=n0name:n0name env.example .env.example
COPY --chown=n0name:n0name sample_config.yml ./config/

# Switch to non-root user
USER n0name

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health', timeout=5)" || exit 1

# Expose ports
EXPOSE 8080 3000

# Default command
CMD ["python", "n0name.py"]

# Stage 3: Development stage
FROM production as development

# Switch back to root for development tools installation
USER root

# Install development dependencies
RUN apt-get update && apt-get install -y \
    vim \
    git \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy development requirements
COPY requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

# Install additional development tools
RUN pip install jupyter ipython

# Switch back to n0name user
USER n0name

# Override command for development
CMD ["python", "-m", "uvicorn", "src.n0name.api:app", "--host", "0.0.0.0", "--port", "8080", "--reload"] 