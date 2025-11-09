# Multi-stage Dockerfile for Sugartalking AVR Control
# Supports both AMD64 and ARM64 architectures

# Stage 1: Build stage
FROM python:3.11-slim AS builder

# Set working directory
WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt


# Stage 2: Runtime stage
FROM python:3.11-slim

LABEL maintainer="Sugartalking Project"
LABEL description="Universal AVR control web interface with multi-receiver support"
LABEL version="2.0.0"

# Create non-root user for security
RUN useradd -m -u 1000 sugartalking && \
    mkdir -p /data /data/logs && \
    chown -R sugartalking:sugartalking /data

# Set working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libavahi-compat-libdnssd1 \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/sugartalking/.local

# Copy application code
COPY --chown=sugartalking:sugartalking app/ /app/app/
COPY --chown=sugartalking:sugartalking static/ /app/static/
COPY --chown=sugartalking:sugartalking scripts/ /app/scripts/
COPY --chown=sugartalking:sugartalking wsgi.py /app/
COPY --chown=sugartalking:sugartalking requirements.txt /app/

# Set environment variables
ENV PATH=/home/sugartalking/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data \
    LOG_DIR=/data/logs \
    LOG_LEVEL=INFO \
    PORT=5000

# Switch to non-root user
USER sugartalking

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health', timeout=5)"

# Run with Gunicorn
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--threads", "4", \
     "--worker-class", "gthread", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "wsgi:app"]
