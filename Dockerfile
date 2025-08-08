# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# --- THIS IS THE UPDATED LINE ---
# Install system-level dependencies for OpenCV and RasterIO, then install Python packages
RUN apt-get update && apt-get install -y libgl1-mesa-glx libgdal-dev && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Tell Render what command to run when the container starts
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]