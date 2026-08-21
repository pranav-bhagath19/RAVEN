# RAVEN Production-Ready Lightweight Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project requirement files if present or install dependencies
COPY . /app/

RUN pip install --no-cache-dir fastapi uvicorn pydantic pydantic-settings httpx pytest ruff mypy

# Expose API Gateway port
EXPOSE 8000

# Health check endpoint probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

# Run Uvicorn production server
CMD ["uvicorn", "apps.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
