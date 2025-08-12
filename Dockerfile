# Use an official, secure Python runtime
FROM python:3.9-slim

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Expose the port Render will use
EXPOSE 10000

# CORRECTED: Use a more robust startup command for Gunicorn
CMD ["gunicorn", "--chdir", "/app", "--bind", "0.0.0.0:10000", "app:app"]