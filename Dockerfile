# Use an official, secure Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for production efficiency
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# Copy and install dependencies first to leverage Docker's cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code
COPY . .

# Expose the port that Render will use to run the service
EXPOSE 10000

# The command to run the application using Gunicorn for production
# This format allows the ${PORT} environment variable to be correctly used by Render
CMD gunicorn --bind 0.0.0.0:${PORT} app:app