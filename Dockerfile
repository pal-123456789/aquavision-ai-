# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 10000
ENV FLASK_ENV=production

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create necessary directories
RUN mkdir -p /app/static/{analysis,uploads} \
    && mkdir -p /app/logs \
    && chmod -R a+rwx /app/logs \
    && chmod -R a+rwx /app/static

# Expose the port
EXPOSE $PORT

# Start the application
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]