#!/bin/bash

# Cleanup script

echo "========================================="
echo "Cleaning up test artifacts"
echo "========================================="

# Remove reports
rm -rf reports/allure-results/*
rm -rf reports/allure-report/*
rm -rf reports/screenshots/*
rm -rf reports/videos/*
rm -rf reports/logs/*
rm -rf reports/*.html
rm -rf reports/*.json

# Remove cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

echo "✅ Cleanup complete!"