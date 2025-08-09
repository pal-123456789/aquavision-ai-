# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose the port Render will use
EXPOSE 10000

# CORRECTED: Use the "shell" form to run Gunicorn, allowing the ${PORT} variable to work
CMD gunicorn --bind 0.0.0.0:${PORT} app:app