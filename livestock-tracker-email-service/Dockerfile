# Dockerfile
FROM python:3.8-slim-buster

WORKDIR /app

# Copy and install dependencies
COPY requirements.txt .

#ENV PYTHONPATH "${PYTHONPATH}:/app"

RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the application code
COPY consumer.py .

CMD ["python", "./consumer.py"]
