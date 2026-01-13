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

# Install Python dependencies
# Извлекаем зависимости из pyproject.toml и устанавливаем напрямую
RUN pip install --no-cache-dir -U pip \
 && pip install --no-cache-dir \
    'fastapi>=0.110' \
    'uvicorn[standard]>=0.27' \
    'httpx>=0.26' \
    'pydantic>=2.6' \
    'pydantic-settings>=2.2' \
    'python-multipart>=0.0.9' \
    'pypdf>=4.0.0' \
    'google-genai'

# Copy application code
COPY app /app/app

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check - увеличен start-period для безопасного старта
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8000/health/live || exit 1

# Use single worker - безопасно для async приложений с shared state
# Для масштабирования используй несколько контейнеров за load balancer
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
