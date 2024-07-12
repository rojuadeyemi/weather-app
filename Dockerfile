# Use the official Python image from the Docker Hub
FROM python:3.9.7-buster

# Set the working directory
WORKDIR /app

# Copy the rest of the application code
COPY requirements.txt .

# Copy the requirements.txt file and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Copy the application module
COPY weather_app ./weather_app

# Expose the port the app runs on
EXPOSE 5000

# Run the Flask-SocketIO app using gunicorn with eventle
CMD ["gunicorn", "-k", "eventlet", "-w", "5", "weather_app:app"]