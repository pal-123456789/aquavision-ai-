# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed system-level packages and then the Python packages
# This helps with dependencies for libraries like opencv and rasterio
RUN apt-get update && apt-get install -y build-essential libgdal-dev && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Tell Render what command to run when the container starts
# Note: Gunicorn is run on port 10000, Render will handle the rest
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]