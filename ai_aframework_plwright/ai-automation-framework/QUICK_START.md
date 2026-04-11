# Quick Start Guide

## Installation

`ash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Or use invoke
python -m invoke setup
`

## Running Tests

### Using PyInvoke (Recommended)

`ash
# List all tasks
python -m invoke --list

# Run smoke tests
python -m invoke test-smoke --env=qa

# Run API tests
python -m invoke test-api

# Run UI tests
python -m invoke test-ui --env=staging --tags=@smoke

# Run demo test (profile page validation)
python -m invoke test-demo --env=demo

# Run all tests
python -m invoke test-all --env=staging
`

### Using Python Scripts Directly

`ash
# Run API tests
python -m pytest tests/api/ -v

# Run UI tests (--env is required)
python run_bdd_tests.py --env=qa

# Run UI tests with tag filter
python run_bdd_tests.py --env=staging --tags=@smoke

# Run all tests (API + UI)
python run_all_tests.py --env=staging

# Clean allure reports before running
python run_bdd_tests.py --env=qa --clean
`

## Allure Reports

`ash
# Generate and open report
python -m invoke allure-report

# Or step by step
python -m invoke allure-generate
python -m invoke allure-open

# Clear old reports
python -m invoke allure-clear

# Generate from CLI
allure generate reports/allure-results -o reports/allure-report --clean
allure open reports/allure-report
`

## Common Workflows

### Quick Test + Report
`ash
python -m invoke test-and-report --test-type=smoke
`

### Full CI Pipeline
`ash
python -m invoke ci
`

### Clean Project
`ash
python -m invoke clean
`

## Project Structure

`
ai-automation-framework/
+-- business/           # Business logic & page objects
|   +-- api/            # API endpoints
|   +-- ui/             # UI pages & flows
+-- tests/              # Test files
|   +-- api/            # API tests (pytest)
|   +-- ui/             # UI tests (behave)
+-- config/             # Configuration (environments.yaml, test_suites.yaml)
+-- core/               # Framework core (driver_factory, api_client, base_test)
+-- ai/                 # AI self-healing & failure analysis
+-- utilities/          # Helpers (logger, data_generator, file_handler, etc.)
+-- reports/            # Generated reports, logs, screenshots
+-- tasks.py            # Invoke task runner
`

## Configuration

Edit `config/environments.yaml` to configure:
- Base URLs and API URLs
- Credentials per role (standard, admin)
- Browser settings (headless, timeout, viewport)
- Feature flags (self_healing, ai_analysis, video_recording)

Set environment via `--env` flag or `TEST_ENV` env variable.
Valid environments: qa, staging, production, local, demo.

## Documentation

- [Architecture Diagram](ARCHITECTURE_DIAGRAM.md)
- [Installation Guide](INSTALLATION_GUIDE.md)
