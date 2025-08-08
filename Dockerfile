# 1. Use an official, lightweight Python runtime as the base image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file into the container
# This is done first to leverage Docker's build cache. The packages layer
# will only be rebuilt if you change the requirements.txt file.
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container
# This includes app.py, the /templates folder, the /static folder, etc.
COPY . .

# 6. Tell Docker the container listens on the port provided by Render
# The PORT environment variable is automatically set by Render.
EXPOSE ${PORT}

# 7. Define the command to run the application using Gunicorn
# This will start the web server, binding to all IPs on the port Render assigns.
CMD ["gunicorn", "--bind", "0.0.0.0:${PORT}", "app:app"]