# Use an official, secure Python runtime
FROM python:3.9-slim-buster

# Add a label to force a layer rebuild
LABEL maintainer="pal-ghevariya"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port
EXPOSE 10000

# Start the application
CMD gunicorn --bind 0.0.0.0:${PORT} app:app