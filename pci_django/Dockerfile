# Stage 1: Dependencies buildin
FROM python:3.12-slim AS builder

# Prevent .pyc files and enableunbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level, build tools needed by psycopg2 combination
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/* 

# Copy only requirements first - re-run when requirements.txt changes
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir --prefix=/install -r requirements.txt

# stage 2: Runtime image
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DJANGO_SETTINGS_MODULE=config.settings

# Runtime only OS packages
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 && rm -rf /var/lib/apt/lists/*

# Create a non-root user - container must not run as a root user
RUN useradd --create-home --shell /bin/bash appuser

WORKDIR /app

# Copy install package from builder stage
COPY --from=builder /install /usr/local

# Copy application source
COPY . .

#  Create log directories and fix ownership
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Entrypoint
# 1. Wait for postgress
# 2. Run migrations of db
# 3. Start gunicorn with 4 workers
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 --workers 4 --preload --access-logfile - --error-logfile - --log-level info"]