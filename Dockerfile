# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 10000  # Default port if not specified

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create static directory
RUN mkdir -p /app/static

# Expose the default port (Render will override $PORT)
EXPOSE 10000

# Use PORT from environment variable
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} app:app"]