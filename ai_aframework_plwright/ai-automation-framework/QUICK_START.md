# 🚀 Quick Start Guide

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Or use invoke
python -m invoke setup
```

## Running Tests

### Using PyInvoke (Recommended)

```bash
# List all tasks
python -m invoke --list

# Run smoke tests
python -m invoke test-smoke

# Run API tests
python -m invoke test-api

# Run UI tests
python -m invoke test-ui

# Run all tests
python -m invoke test-all
```

### Using Python Scripts

```bash
# Run API tests
python -m pytest tests/api/ -v

# Run UI tests
python run_bdd_tests.py

# Run specific UI test
python run_bdd_tests.py --tags=@smoke
```

## Allure Reports

```bash
# Generate and open report
python -m invoke allure-report

# Or step by step
python -m invoke allure-generate
python -m invoke allure-open

# Clear old reports
python -m invoke allure-clear
```

## Common Workflows

### Quick Test + Report
```bash
python -m invoke test-and-report --test-type=smoke
```

### Full CI Pipeline
```bash
python -m invoke ci
```

### Patient Login Test with New Account
```bash
python -m invoke test-patient-login --create-account
```

## Project Structure

```
ai-automation-framework/
├── business/           # Business logic & page objects
│   ├── api/           # API endpoints
│   └── ui/            # UI page objects
├── tests/             # Test files
│   ├── api/          # API tests (pytest)
│   └── ui/           # UI tests (behave)
├── config/            # Configuration files
├── utilities/         # Helper utilities
├── reports/           # Test reports
└── tasks.py          # Invoke tasks
```

## Configuration

Edit `config/environments.yaml` to configure:
- Base URLs
- Credentials
- Browser settings
- Viewport size
- Timeouts

## Documentation

- [Invoke Tasks Guide](INVOKE_TASKS.md) - Complete task reference
- [API Helpers Guide](API_HELPERS_USAGE_GUIDE.md) - API usage
- [Patient API Guide](business/api/README_PATIENT_API.md) - Patient API details
- [Framework Structure](FRAMEWORK_STRUCTURE.md) - Architecture overview

## Need Help?

```bash
# Show project info
python -m invoke info

# Get help for specific task
python -m invoke --help test-api
```
