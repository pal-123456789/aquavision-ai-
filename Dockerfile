# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application's code into the container
COPY . .

# Expose the port Render provides
EXPOSE 10000

# THIS IS THE CORRECTED LINE: Use the "shell" form to run the server
CMD gunicorn --bind 0.0.0.0:${PORT} app:app