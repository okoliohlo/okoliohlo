# Multi-stage Dockerfile for test execution

FROM mcr.microsoft.com/playwright/python:v1.40.0-focal AS base

# Set working directory
WORKDIR /automation

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install --with-deps

# Copy framework code
COPY . .

# Create directories
RUN mkdir -p reports/allure-results reports/screenshots reports/videos reports/logs

# Set environment variables
ENV PYTHONPATH=/automation
ENV TEST_ENV=qa
ENV SELF_HEALING=true
ENV AI_ANALYSIS=true

# Default command
CMD ["pytest", "tests/", "-n", "4", "-m", "smoke", "--alluredir=reports/allure-results", "-v"]