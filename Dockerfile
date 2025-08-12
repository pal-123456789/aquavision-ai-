# Use an official, secure Python runtime as a parent image
FROM python:3.9-slim

# Set environment variables for production efficiency
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory inside the container
WORKDIR /app

# MODIFICATION: Install system dependencies required for geospatial libraries
# The 'rasterio' and 'geopandas' packages need the GDAL library to be installed.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgdal-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies first to leverage Docker's cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code, including the machine learning model
COPY . .

# Expose the port that Render will use to run the service
EXPOSE 10000

# The command to run the application using Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "app:app"]