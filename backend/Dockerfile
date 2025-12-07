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
COPY start.sh .

# Make start script executable
RUN chmod +x start.sh

# Default port
ENV PORT=8000

# Expose port
EXPOSE 8000

# Use the start script
ENTRYPOINT ["./start.sh"]
