# 1. Use an official, lightweight Python runtime as the base image
FROM python:3.9-slim

# 2. Set the working directory inside the container
WORKDIR /app

# 3. Copy the requirements file into the container
COPY requirements.txt .

# 4. Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container
COPY . .

# 6. Tell Docker the container listens on the port provided by Render
# The PORT environment variable is automatically set by Render.
EXPOSE ${PORT}

# 7. Define the command to run the application using Gunicorn (SHELL FORM)
# This version allows the shell to substitute the ${PORT} variable correctly.
CMD gunicorn --bind 0.0.0.0:${PORT} app:app