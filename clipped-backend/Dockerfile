# Base image with Python
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install ffmpeg (required for processing media files)
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*
# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose port (default for FastAPI)
EXPOSE 8000

# Start FastAPI app using Uvicorn (app.py is at root)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
