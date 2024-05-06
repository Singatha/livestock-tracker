# Base image
FROM python:3.8-slim-buster

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

RUN pip3 install --no-cache-dir --upgrade -r requirements.txt

# Copy the FastAPI application code
COPY . .

# Expose the application port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
