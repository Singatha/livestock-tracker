# Base image
FROM python:3.8-slim-buster
#FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

ENV PYTHONPATH "${PYTHONPATH}:/app"

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy the FastAPI application code
COPY . .

# Expose the application port
EXPOSE 50051

# Run the FastAPI application
CMD ["python", "main.py"]
