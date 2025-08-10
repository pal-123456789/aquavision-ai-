FROM python:3.9-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Create directories (adjust paths to match your config)
RUN mkdir -p /app/src/static/uploads && \
    mkdir -p /app/src/static/analysis && \
    chmod -R a+rwx /app/src/static

EXPOSE 5000

# Updated Gunicorn command
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "wsgi:app"]