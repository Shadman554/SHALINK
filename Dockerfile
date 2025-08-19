# Use Python 3.12 official image
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python packages
COPY requirements_railway_new.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements_railway_new.txt

# Copy application code
COPY . .

# Test deployment
RUN python deploy_railway_fix.py

# Expose port (Railway requirement)
EXPOSE 5000

# Start the bot
CMD ["python", "main.py"]