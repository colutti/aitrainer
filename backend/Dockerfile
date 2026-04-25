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

# Build a wheelhouse once and reuse it for deterministic + faster installs.
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --wheel-dir /tmp/wheels -r requirements.txt

# Create virtual environment and install dependencies from local wheelhouse
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-index --find-links=/tmp/wheels -r requirements.txt

# Verify stage - includes dev tooling for lint/typecheck/tests
FROM builder AS verify-builder

COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt

# Verify runtime - reuses the builder venv with dev tooling installed
FROM docker.io/library/python:3.12-slim AS verify

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

COPY --from=verify-builder /opt/venv /opt/venv

CMD ["sh", "-lc", "/opt/venv/bin/ruff check src tests && /opt/venv/bin/pylint src && /opt/venv/bin/pytest tests/unit tests/api tests/services tests/test_services"]

# Runtime stage - imagem mínima
FROM docker.io/library/python:3.12-slim AS production

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
COPY scripts/ ./scripts/

# Create a non-privileged user and group
RUN groupadd -r app && useradd -r -g app -s /sbin/nologin app

# Create a home directory for the user and set permissions
RUN mkdir -p /home/app && chown app:app /home/app

# Change ownership of the app directory
RUN chown -R app:app /app

# Use the non-privileged user
USER app

EXPOSE 8000

CMD ["sh", "-c", "gunicorn src.api.main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT:-8000}"]
