# Build stage
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Runtime stage
FROM python:3.9-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 10000
ENV FLASK_ENV=production

RUN mkdir -p /app/static/{analysis,uploads} \
    && mkdir -p /app/logs \
    && chmod -R a+rwx /app/logs \
    && chmod -R a+rwx /app/static

EXPOSE $PORT
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:$PORT/health || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "--workers", "4", "--threads", "2", "--timeout", "120", "app:app"]