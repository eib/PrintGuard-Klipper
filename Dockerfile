# PrintGuard API Dockerfile
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY src/printguard ./printguard

# Create directories for data and models
RUN mkdir -p /app/data /app/models

# Expose API port
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "printguard.main:app", "--host", "0.0.0.0", "--port", "8000"]
