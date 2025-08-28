FROM python:3.10-slim

# System dependencies for Guardian
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi-dev \
    python3-cffi \
    python3-brotli \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

# Working directory
WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy requirements first for better caching
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app/backend

# Environment variables
ENV FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=5051

EXPOSE 5051

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5051/api/health || exit 1

# Use Gunicorn for production
CMD ["gunicorn", "--config", "backend/gunicorn.conf.py", "backend.wsgi:app"]