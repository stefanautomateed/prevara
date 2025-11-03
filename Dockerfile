# Dockerfile for Railway deployment
FROM python:3.11-slim

# Set environment variables for non-interactive apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    fonts-noto-color-emoji \
    fonts-noto-cjk \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    libu2f-udev \
    libvulkan1 \
    libxshmfence1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (skip system deps since we already installed them)
RUN playwright install chromium --with-deps || playwright install chromium

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose port (Railway will set PORT env var)
EXPOSE 5000

# Run the web application with gunicorn
# Using shell form to allow PORT env var expansion
CMD gunicorn --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 2 --timeout 300 app:app
