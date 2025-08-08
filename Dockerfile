# --- THIS IS THE ONLY LINE THAT CHANGES ---
# Use the full, official Python image, not the "slim" version
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Run installations. This command is kept for maximum reliability.
RUN apt-get update && apt-get install -y libgl1-mesa-glx libgdal-dev && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container
COPY . .

# Tell Render what command to run when the container starts
CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]