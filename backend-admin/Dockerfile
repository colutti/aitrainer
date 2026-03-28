# Build stage - instala dependências com build tools
FROM docker.io/library/python:3.12-slim AS builder

WORKDIR /app

# Performance and stability environments
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies for building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (Docker layer caching)
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Verify stage - admin service needs pyright and libatomic at runtime
FROM builder AS verify-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pylint pyright

# Runtime stage - imagem mínima
FROM docker.io/library/python:3.12-slim

WORKDIR /app

# Runtime environments
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy source code
COPY src/ ./src/

# Create a non-privileged user and group
RUN groupadd -r app && useradd -r -g app -s /sbin/nologin app
RUN mkdir -p /home/app && chown app:app /home/app
RUN chown -R app:app /app

USER app

EXPOSE 8000

CMD ["sh", "-c", "gunicorn src.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]

# Verify runtime - includes static analysis tooling
FROM docker.io/library/python:3.12-slim AS verify

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

COPY --from=verify-builder /opt/venv /opt/venv

CMD ["sh", "-lc", "/opt/venv/bin/pylint src && /opt/venv/bin/pyright --pythonpath /opt/venv/bin/python src"]
