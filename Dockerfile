FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
  && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml /app/

# Install Python dependencies — source of truth is pyproject.toml
RUN pip install --no-cache-dir -U pip \
 && python3 -c "\
import tomllib; \
deps = tomllib.load(open('/app/pyproject.toml', 'rb'))['project']['dependencies']; \
open('/tmp/reqs.txt', 'w').write('\n'.join(deps))" \
 && pip install --no-cache-dir -r /tmp/reqs.txt

# Copy application code
COPY app /app/app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check - увеличен start-period для безопасного старта
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers ${UVICORN_WORKERS:-4}"]
