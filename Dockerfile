FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV FLASK_APP=wsgi.py

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create necessary directories
RUN mkdir -p /app/instance/uploads && \
    mkdir -p /app/instance/analysis && \
    chmod -R a+rwx /app/instance

# Use $PORT environment variable for Render
CMD ["sh", "-c", "gunicorn --bind 0.0.0.0:${PORT} --pythonpath /app backend.wsgi:app"]