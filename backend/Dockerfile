# Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src ./src
COPY data ./data

# Default port (Railway will override via PORT env var)
ENV PORT=8000

# Expose port
EXPOSE 8000

# Start command - use shell form for variable expansion
CMD uvicorn src.main:app --host 0.0.0.0 --port $PORT
