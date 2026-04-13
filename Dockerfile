# Use the official Python image from the Docker Hub
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the rest of the application code
COPY requirements.txt .

# Copy the requirements.txt file and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application module
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the Flask-SocketIO app using gunicorn with eventlet
CMD ["gunicorn", "-k", "geventwebsocket.gunicorn.workers.GeventWebSocketWorker", "-w", "1", "--bind", "0.0.0.0:5000", "app:app"]