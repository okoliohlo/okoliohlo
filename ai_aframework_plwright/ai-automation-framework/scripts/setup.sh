#!/bin/bash

# Setup script for the automation framework

echo "========================================="
echo "Setting up Automation Framework"
echo "========================================="

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install
playwright install-deps

# Create directories
#echo "Creating directories..."
#mkdir -p reports/allure-results
#mkdir -p reports/allure-report
#mkdir -p reports/screenshots
#mkdir -p reports/videos
#mkdir -p reports/logs
#mkdir -p test_data

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Verify installation
echo "Verifying installation..."
python3 -c "import playwright; print('Playwright version:', playwright.__version__)"
pytest --version

echo "========================================="
echo "✅ Setup complete!"
echo "========================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run tests: ./scripts/run_tests.sh"
echo ""