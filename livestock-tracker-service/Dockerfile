# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Copy and install dependencies
COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy the FastAPI application code
COPY . .

# Expose the application port
EXPOSE 50051

# Run the FastAPI application
CMD ["python", "main.py"]
